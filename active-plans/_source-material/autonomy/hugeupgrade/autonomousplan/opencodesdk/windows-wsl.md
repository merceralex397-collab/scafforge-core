---
source_url: https://opencode.ai/docs/windows-wsl
fetched_with: http
---

# Windows (WSL)

Run OpenCode on Windows using WSL for the best experience.

While OpenCode can run directly on Windows, we recommend using Windows Subsystem for Linux (WSL) for the best experience. WSL provides a Linux environment that works seamlessly with OpenCode’s features.

-
**Install WSL**If you haven’t already, install WSL using the official Microsoft guide.

-
**Install OpenCode in WSL**Once WSL is set up, open your WSL terminal and install OpenCode using one of the installation methods.

-
**Use OpenCode from WSL**Navigate to your project directory (access Windows files via

`/mnt/c/`

,`/mnt/d/`

, etc.) and run OpenCode.

If you prefer using the OpenCode Desktop app but want to run the server in WSL:

-
**Start the server in WSL**with`--hostname 0.0.0.0`

to allow external connections: -
**Connect the Desktop app**to`http://localhost:4096`

For the best web experience on Windows:

-
**Run**rather than PowerShell:`opencode web`

in the WSL terminal -
**Access from your Windows browser**at`http://localhost:<port>`

(OpenCode prints the URL)

Running `opencode web`

from WSL ensures proper file system access and terminal integration while still being accessible from your Windows browser.

WSL can access all your Windows files through the `/mnt/`

directory:

`C:`

drive →`/mnt/c/`

`D:`

drive →`/mnt/d/`

- And so on…

Example:

- Keep OpenCode running in WSL for projects stored on Windows drives - file access is seamless
- Use VS Code’s WSL extension alongside OpenCode for an integrated development workflow
- Your OpenCode config and sessions are stored within the WSL environment at
`~/.local/share/opencode/`
