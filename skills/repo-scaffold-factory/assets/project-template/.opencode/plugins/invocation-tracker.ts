import { type Plugin } from "@opencode-ai/plugin"
import { appendJsonl, invocationLogPath } from "../lib/workflow"

export const InvocationTracker: Plugin = async (pluginInput) => {
  const path = invocationLogPath(pluginInput.directory)
  const timestamp = () => new Date().toISOString()
  const recordEvent = async (payload: Record<string, unknown>) => {
    try {
      await appendJsonl(path, payload)
    } catch (error) {
      console.warn(`InvocationTracker disabled for this event: ${String(error)}`)
    }
  }

  return {
    "chat.message": async (input, output) => {
      await recordEvent({
        event: "chat.message",
        timestamp: timestamp(),
        session_id: input.sessionID,
        agent: input.agent ?? null,
        message_id: input.messageID ?? null,
        model: input.model ?? null,
        variant: input.variant ?? null,
        part_count: output.parts.length,
      })
    },
    "command.execute.before": async (input) => {
      await recordEvent({
        event: "command.execute.before",
        timestamp: timestamp(),
        session_id: input.sessionID,
        agent: input.agent ?? null,
        command: input.command,
        arguments: input.arguments,
      })
    },
    "tool.execute.before": async (input, output) => {
      await recordEvent({
        event: "tool.execute.before",
        timestamp: timestamp(),
        session_id: input.sessionID,
        agent: input.agent ?? null,
        tool: input.tool,
        call_id: input.callID,
        args: output.args,
      })
    },
    "tool.execute.after": async (input, output) => {
      await recordEvent({
        event: "tool.execute.after",
        timestamp: timestamp(),
        session_id: input.sessionID,
        agent: input.agent ?? null,
        tool: input.tool,
        call_id: input.callID,
        args: input.args,
        title: output.title,
        metadata: output.metadata ?? null,
      })
    },
  }
}
