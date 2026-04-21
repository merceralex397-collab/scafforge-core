---
source_url: https://opencode.ai/docs/network
fetched_with: http
---

# Network

Configure proxies and custom certificates.

OpenCode supports standard proxy environment variables and custom certificates for enterprise network environments.

OpenCode respects standard proxy environment variables.

You can configure the server’s port and hostname using CLI flags.

If your proxy requires basic authentication, include credentials in the URL.

For proxies requiring advanced authentication like NTLM or Kerberos, consider using an LLM Gateway that supports your authentication method.

If your enterprise uses custom CAs for HTTPS connections, configure OpenCode to trust them.

This works for both proxy connections and direct API access.
