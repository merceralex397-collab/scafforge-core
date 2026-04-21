---
source_url: https://opencode.ai/docs/github
fetched_with: http
---

# GitHub

Use OpenCode in GitHub issues and pull-requests.

OpenCode integrates with your GitHub workflow. Mention `/opencode`

or `/oc`

in your comment, and OpenCode will execute tasks within your GitHub Actions runner.

**Triage issues**: Ask OpenCode to look into an issue and explain it to you.**Fix and implement**: Ask OpenCode to fix an issue or implement a feature. And it will work in a new branch and submits a PR with all the changes.**Secure**: OpenCode runs inside your GitHub’s runners.

Run the following command in a project that is in a GitHub repo:

This will walk you through installing the GitHub app, creating the workflow, and setting up secrets.

Or you can set it up manually.

-
**Install the GitHub app**Head over to

**github.com/apps/opencode-agent**. Make sure it’s installed on the target repository. -
**Add the workflow**Add the following workflow file to

`.github/workflows/opencode.yml`

in your repo. Make sure to set the appropriate`model`

and required API keys in`env`

. -
**Store the API keys in secrets**In your organization or project

**settings**, expand**Secrets and variables**on the left and select**Actions**. And add the required API keys.

-
`model`

: The model to use with OpenCode. Takes the format of`provider/model`

. This is**required**. - `agent`

: The agent to use. Must be a primary agent. Falls back to`default_agent`

from config or`"build"`

if not found. - `share`

: Whether to share the OpenCode session. Defaults to**true**for public repositories. - `prompt`

: Optional custom prompt to override the default behavior. Use this to customize how OpenCode processes requests. - `token`

: Optional GitHub access token for performing operations such as creating comments, committing changes, and opening pull requests. By default, OpenCode uses the installation access token from the OpenCode GitHub App, so commits, comments, and pull requests appear as coming from the app.Alternatively, you can use the GitHub Action runner’s built-in

`GITHUB_TOKEN`

without installing the OpenCode GitHub App. Just make sure to grant the required permissions in your workflow:You can also use a personal access tokens(PAT) if preferred.

OpenCode can be triggered by the following GitHub events:

| Event Type | Triggered By | Details |
|---|---|---|
`issue_comment` | Comment on an issue or PR | Mention `/opencode` or `/oc` in your comment. OpenCode reads context and can create branches, open PRs, or reply. | `pull_request_review_comment` | Comment on specific code lines in a PR | Mention `/opencode` or `/oc` while reviewing code. OpenCode receives file path, line numbers, and diff context. | `issues` | Issue opened or edited | Automatically trigger OpenCode when issues are created or modified. Requires `prompt` input. | `pull_request` | PR opened or updated | Automatically trigger OpenCode when PRs are opened, synchronized, or reopened. Useful for automated reviews. | `schedule` | Cron-based schedule | Run OpenCode on a schedule. Requires `prompt` input. Output goes to logs and PRs (no issue to comment on). | `workflow_dispatch` | Manual trigger from GitHub UI | Trigger OpenCode on demand via Actions tab. Requires `prompt` input. Output goes to logs and PRs. |

Run OpenCode on a schedule to perform automated tasks:

For scheduled events, the `prompt`

input is **required** since there’s no comment to extract instructions from. Scheduled workflows run without a user context to permission-check, so the workflow must grant `contents: write`

and `pull-requests: write`

if you expect OpenCode to create branches or PRs.

Automatically review PRs when they are opened or updated:

For `pull_request`

events, if no `prompt`

is provided, OpenCode defaults to reviewing the pull request.

Automatically triage new issues. This example filters to accounts older than 30 days to reduce spam:

For `issues`

events, the `prompt`

input is **required** since there’s no comment to extract instructions from.

Override the default prompt to customize OpenCode’s behavior for your workflow.

This is useful for enforcing specific review criteria, coding standards, or focus areas relevant to your project.

Here are some examples of how you can use OpenCode in GitHub.

-
**Explain an issue**Add this comment in a GitHub issue.

OpenCode will read the entire thread, including all comments, and reply with a clear explanation.

-
**Fix an issue**In a GitHub issue, say:

And OpenCode will create a new branch, implement the changes, and open a PR with the changes.

-
**Review PRs and make changes**Leave the following comment on a GitHub PR.

OpenCode will implement the requested change and commit it to the same PR.

-
**Review specific code lines**Leave a comment directly on code lines in the PR’s “Files” tab. OpenCode automatically detects the file, line numbers, and diff context to provide precise responses.

When commenting on specific lines, OpenCode receives:

- The exact file being reviewed
- The specific lines of code
- The surrounding diff context
- Line number information

This allows for more targeted requests without needing to specify file paths or line numbers manually.
