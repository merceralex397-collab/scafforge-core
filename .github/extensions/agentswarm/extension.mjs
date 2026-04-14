import { access } from "node:fs/promises";
import path from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

import { joinSession } from "@github/copilot-sdk/extension";

const execFileAsync = promisify(execFile);

const MODEL_ID = "fireworks-ai/accounts/fireworks/routers/kimi-k2p5-turbo";
const DEFAULT_SWARM_SIZE = 4;
const MAX_SWARM_SIZE = 20;
const DEFAULT_TIMEOUT_SECONDS = 300;
const MAX_TIMEOUT_SECONDS = 900;
const DEFAULT_MAX_BUFFER = 2 * 1024 * 1024;
const MAX_RESULT_CHARS = 6000;

let lastKnownCwd = process.cwd();

function stripAnsi(text) {
    return String(text || "").replace(/\u001B\[[0-9;]*[A-Za-z]/g, "");
}

function clampInteger(value, fallback, minimum, maximum) {
    const numeric = Number.parseInt(String(value ?? ""), 10);
    if (!Number.isFinite(numeric)) return fallback;
    return Math.min(maximum, Math.max(minimum, numeric));
}

function truncate(text, limit = MAX_RESULT_CHARS) {
    const normalized = stripAnsi(text).trim();
    if (normalized.length <= limit) return normalized;
    return `${normalized.slice(0, limit)}\n...[truncated ${normalized.length - limit} chars]`;
}

function extractOpencodeText(stdout) {
    const raw = String(stdout || "").trim();
    if (!raw) return "";

    const parts = [];
    for (const line of raw.split(/\r?\n/)) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        try {
            const event = JSON.parse(trimmed);
            if (event?.type === "text" && typeof event?.part?.text === "string") {
                parts.push(event.part.text);
            }
        } catch {
            return truncate(raw);
        }
    }

    return truncate(parts.join("\n").trim() || raw);
}

function formatPromptPreview(text, limit = 300) {
    const normalized = String(text || "").replace(/\s+/g, " ").trim();
    if (normalized.length <= limit) return normalized;
    return `${normalized.slice(0, limit)}...`;
}

async function normalizeFiles(cwd, files) {
    const normalized = [];
    for (const entry of Array.isArray(files) ? files : []) {
        const raw = String(entry || "").trim();
        if (!raw) continue;
        const resolved = path.isAbsolute(raw) ? raw : path.resolve(cwd, raw);
        await access(resolved);
        normalized.push(resolved);
    }
    return normalized;
}

function buildPromptList(args) {
    const explicitPrompts = Array.isArray(args.prompts)
        ? args.prompts.map((value) => String(value || "").trim()).filter(Boolean)
        : [];
    const basePrompt = String(args.prompt || "").trim();

    if (explicitPrompts.length > 0) {
        if (explicitPrompts.length > MAX_SWARM_SIZE) {
            throw new Error(`agentswarm supports at most ${MAX_SWARM_SIZE} prompts per run.`);
        }
        return explicitPrompts;
    }

    if (!basePrompt) {
        throw new Error("Provide either prompt or prompts.");
    }

    const swarmSize = clampInteger(args.swarmSize, DEFAULT_SWARM_SIZE, 1, MAX_SWARM_SIZE);
    return Array.from({ length: swarmSize }, () => basePrompt);
}

function buildWorkerPrompt({ prompt, sharedContext, index, total }) {
    const blocks = [
        `You are worker ${index} of ${total} in an exploration swarm.`,
        "Model quality is intentionally fast and weaker than the supervising agent.",
        "Do not guess. If you are unsure, say UNKNOWN.",
        "Use this only for evidence gathering, not final judgment.",
        "Prefer concrete evidence: file paths, symbols, commands, URLs, and short quoted snippets.",
        "Do not propose code edits unless the task explicitly requests them.",
        "Keep the response compact.",
        "Output exactly these sections:",
        "FINDINGS:\n- ...",
        "EVIDENCE:\n- ...",
        "UNKNOWNS:\n- ...",
        "CONFIDENCE: low|medium|high",
    ];

    if (String(sharedContext || "").trim()) {
        blocks.push(`SHARED CONTEXT:\n${String(sharedContext).trim()}`);
    }

    blocks.push(`TASK:\n${String(prompt).trim()}`);
    return blocks.join("\n\n");
}

function getOpencodeInvocation(args) {
    if (process.platform === "win32") {
        return {
            command: "cmd.exe",
            args: ["/d", "/s", "/c", "opencode", ...args],
        };
    }

    return {
        command: "opencode",
        args,
    };
}

async function runWorker({
    cwd,
    files,
    prompt,
    sharedContext,
    index,
    total,
    timeoutSeconds,
}) {
    const workerPrompt = buildWorkerPrompt({
        prompt,
        sharedContext,
        index: index + 1,
        total,
    });

    const opencodeArgs = [
        "run",
        "--pure",
        "--model",
        MODEL_ID,
        "--format",
        "json",
        "--dir",
        cwd,
        "--title",
        `agentswarm-${index + 1}`,
    ];

    for (const filePath of files) {
        opencodeArgs.push("--file", filePath);
    }

    opencodeArgs.push(workerPrompt);

    const { command, args } = getOpencodeInvocation(opencodeArgs);
    const startedAt = Date.now();

    try {
        const { stdout, stderr } = await execFileAsync(command, args, {
            cwd,
            timeout: timeoutSeconds * 1000,
            maxBuffer: DEFAULT_MAX_BUFFER,
            env: {
                ...process.env,
                NO_COLOR: "1",
                TERM: "dumb",
                CI: "1",
            },
        });

        return {
            index,
            ok: true,
            promptPreview: formatPromptPreview(prompt),
            stdout: extractOpencodeText(stdout),
            stderr: truncate(stderr),
            durationSeconds: ((Date.now() - startedAt) / 1000).toFixed(1),
        };
    } catch (error) {
        return {
            index,
            ok: false,
            promptPreview: formatPromptPreview(prompt),
            stdout: extractOpencodeText(error?.stdout),
            stderr: truncate(error?.stderr || error?.message || "Unknown error"),
            durationSeconds: ((Date.now() - startedAt) / 1000).toFixed(1),
            exitCode: error?.code ?? "unknown",
            signal: error?.signal ?? null,
        };
    }
}

async function mapLimit(items, limit, iteratee) {
    const results = new Array(items.length);
    let cursor = 0;

    async function workerLoop() {
        while (true) {
            const current = cursor;
            cursor += 1;
            if (current >= items.length) return;
            results[current] = await iteratee(items[current], current);
        }
    }

    const workerCount = Math.min(limit, items.length);
    await Promise.all(Array.from({ length: workerCount }, () => workerLoop()));
    return results;
}

function formatSwarmResult({
    results,
    cwd,
    files,
    totalPrompts,
    maxParallel,
    timeoutSeconds,
}) {
    const successCount = results.filter((result) => result.ok).length;
    const failureCount = results.length - successCount;
    const lines = [
        `agentswarm completed ${results.length} worker(s) with model ${MODEL_ID}.`,
        `Succeeded: ${successCount}; failed: ${failureCount}; cwd: ${cwd}; maxParallel: ${maxParallel}; timeoutSeconds: ${timeoutSeconds}.`,
    ];

    if (files.length > 0) {
        lines.push(`Attached files (${files.length}): ${files.join(", ")}`);
    }

    if (totalPrompts !== results.length) {
        lines.push(`Requested prompts: ${totalPrompts}; executed workers: ${results.length}.`);
    }

    for (const result of results) {
        lines.push("");
        lines.push(`### worker-${result.index + 1} | ${result.ok ? "success" : "failure"} | ${result.durationSeconds}s`);
        lines.push(`Prompt: ${result.promptPreview || "(empty)"}`);
        if (result.stdout) {
            lines.push("Output:");
            lines.push(result.stdout);
        }
        if (result.stderr) {
            lines.push("Stderr:");
            lines.push(result.stderr);
        }
        if (!result.ok) {
            lines.push(`Exit: ${result.exitCode}${result.signal ? `; signal: ${result.signal}` : ""}`);
        }
    }

    lines.push("");
    lines.push("Treat these results as weak-model exploration output. Verify anything important before acting on it.");
    return lines.join("\n");
}

const session = await joinSession({
    hooks: {
        onSessionStart: async (input) => {
            lastKnownCwd = input.cwd || lastKnownCwd;
            return {
                additionalContext: `Project extension available: agentswarm_run. It launches up to ${MAX_SWARM_SIZE} headless opencode workers on ${MODEL_ID} for cheap exploration and data gathering. Treat every result as weak-model evidence: split work into narrow prompts, ask for file paths/URLs/quoted evidence, require UNKNOWN when unsure, and never delegate final judgment or code mutation to the swarm.`,
            };
        },
        onUserPromptSubmitted: async (input) => {
            lastKnownCwd = input.cwd || lastKnownCwd;
        },
        onPreToolUse: async (input) => {
            lastKnownCwd = input.cwd || lastKnownCwd;
        },
    },
    tools: [
        {
            name: "agentswarm_run",
            description: "Run a fast headless opencode swarm on Fireworks Kimi K2.5 Turbo for narrow exploration and data gathering. Use for weak-model evidence gathering only; verify findings before relying on them.",
            parameters: {
                type: "object",
                properties: {
                    prompt: {
                        type: "string",
                        description: "Single prompt to fan out across the swarm. Best for repeated independent passes on the same narrow task.",
                    },
                    prompts: {
                        type: "array",
                        description: "One narrow prompt per worker. Preferred when splitting a task into focused sub-questions.",
                        items: {
                            type: "string",
                        },
                        minItems: 1,
                        maxItems: MAX_SWARM_SIZE,
                    },
                    sharedContext: {
                        type: "string",
                        description: "Optional context prepended to every worker prompt, such as repo constraints, directories, or output requirements.",
                    },
                    swarmSize: {
                        type: "integer",
                        description: `Worker count when using prompt. Defaults to ${DEFAULT_SWARM_SIZE}, max ${MAX_SWARM_SIZE}.`,
                        minimum: 1,
                        maximum: MAX_SWARM_SIZE,
                    },
                    maxParallel: {
                        type: "integer",
                        description: `Maximum workers to run at once. Defaults to the number of workers, capped at ${MAX_SWARM_SIZE}.`,
                        minimum: 1,
                        maximum: MAX_SWARM_SIZE,
                    },
                    timeoutSeconds: {
                        type: "integer",
                        description: `Per-worker timeout in seconds. Defaults to ${DEFAULT_TIMEOUT_SECONDS}.`,
                        minimum: 30,
                        maximum: MAX_TIMEOUT_SECONDS,
                    },
                    cwd: {
                        type: "string",
                        description: "Working directory for the swarm. Defaults to the current session cwd.",
                    },
                    files: {
                        type: "array",
                        description: "Optional files to attach to every opencode run.",
                        items: {
                            type: "string",
                        },
                    },
                },
            },
            handler: async (args) => {
                try {
                    const prompts = buildPromptList(args);
                    const cwd = path.resolve(String(args.cwd || lastKnownCwd || process.cwd()));
                    const files = await normalizeFiles(cwd, args.files);
                    const timeoutSeconds = clampInteger(
                        args.timeoutSeconds,
                        DEFAULT_TIMEOUT_SECONDS,
                        30,
                        MAX_TIMEOUT_SECONDS,
                    );
                    const maxParallel = clampInteger(
                        args.maxParallel,
                        prompts.length,
                        1,
                        MAX_SWARM_SIZE,
                    );

                    await session.log(
                        `agentswarm: launching ${prompts.length} worker(s) in ${cwd}`,
                        { ephemeral: true },
                    );

                    const results = await mapLimit(prompts, maxParallel, (prompt, index) =>
                        runWorker({
                            cwd,
                            files,
                            prompt,
                            sharedContext: args.sharedContext,
                            index,
                            total: prompts.length,
                            timeoutSeconds,
                        }),
                    );

                    const textResultForLlm = formatSwarmResult({
                        results,
                        cwd,
                        files,
                        totalPrompts: prompts.length,
                        maxParallel,
                        timeoutSeconds,
                    });
                    const allFailed = results.every((result) => !result.ok);

                    return {
                        textResultForLlm,
                        resultType: allFailed ? "failure" : "success",
                    };
                } catch (error) {
                    return {
                        textResultForLlm: `agentswarm rejected the request: ${error?.message || String(error)}`,
                        resultType: "rejected",
                    };
                }
            },
        },
    ],
});
