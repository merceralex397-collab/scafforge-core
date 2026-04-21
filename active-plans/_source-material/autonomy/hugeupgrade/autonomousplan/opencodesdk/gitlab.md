---
source_url: https://opencode.ai/docs/gitlab
fetched_with: http
---

# GitLab

Use OpenCode in GitLab issues and merge requests.

OpenCode integrates with your GitLab workflow through your GitLab CI/CD pipeline or with GitLab Duo.

In both cases, OpenCode will run on your GitLab runners.

OpenCode works in a regular GitLab pipeline. You can build it into a pipeline as a CI component

Here we are using a community-created CI/CD component for OpenCode — nagyv/gitlab-opencode.

**Use custom configuration per job**: Configure OpenCode with a custom configuration directory, for example`./config/#custom-directory`

to enable or disable functionality per OpenCode invocation.**Minimal setup**: The CI component sets up OpenCode in the background, you only need to create the OpenCode configuration and the initial prompt.**Flexible**: The CI component supports several inputs for customizing its behavior

-
Store your OpenCode authentication JSON as a File type CI environment variables under

**Settings**>**CI/CD**>**Variables**. Make sure to mark them as “Masked and hidden”. -
Add the following to your

`.gitlab-ci.yml`

file.

For more inputs and use cases check out the docs for this component.

OpenCode integrates with your GitLab workflow. Mention `@opencode`

in a comment, and OpenCode will execute tasks within your GitLab CI pipeline.

**Triage issues**: Ask OpenCode to look into an issue and explain it to you.**Fix and implement**: Ask OpenCode to fix an issue or implement a feature. It will create a new branch and raise a merge request with the changes.**Secure**: OpenCode runs on your GitLab runners.

OpenCode runs in your GitLab CI/CD pipeline, here’s what you’ll need to set it up:

-
Configure your GitLab environment

-
Set up CI/CD

-
Get an AI model provider API key

-
Create a service account

-
Configure CI/CD variables

-
Create a flow config file, here’s an example:

## Flow configuration

You can refer to the GitLab CLI agents docs for detailed instructions.

Here are some examples of how you can use OpenCode in GitLab.

-
**Explain an issue**Add this comment in a GitLab issue.

OpenCode will read the issue and reply with a clear explanation.

-
**Fix an issue**In a GitLab issue, say:

OpenCode will create a new branch, implement the changes, and open a merge request with the changes.

-
**Review merge requests**Leave the following comment on a GitLab merge request.

OpenCode will review the merge request and provide feedback.
