> ## Documentation Index

> Fetch the complete documentation index at: https://platform.minimax.io/docs/llms.txt

> Use this file to discover all available pages before exploring further.



\# Token Plan MCP Guide



> Token Plan MCP provides two exclusive tools: \*\*web\_search\*\* and \*\*understand\_image\*\*, helping developers quickly access information and understand image content during coding.



\## Tool Description



<AccordionGroup>

&#x20; <Accordion title="web\_search" icon="search">

&#x20;   Performs web searches based on search queries, returning search results and related suggestions.



&#x20;   | Parameter | Type   | Required | Description  |

&#x20;   | :-------- | :----- | :------: | :----------- |

&#x20;   | query     | string |     ✓    | Search query |

&#x20; </Accordion>



&#x20; <Accordion title="understand\_image" icon="eye">

&#x20;   Performs image understanding and analysis, supporting multiple image input methods.



&#x20;   | Parameter  | Type   | Required | Description                                              |

&#x20;   | :--------- | :----- | :------: | :------------------------------------------------------- |

&#x20;   | prompt     | string |     ✓    | Question or analysis request for the image               |

&#x20;   | image\\\_url | string |     ✓    | Image source, supports HTTP/HTTPS URL or local file path |



&#x20;   \*\*Supported formats\*\*: JPEG, PNG, GIF, WebP (max 20MB)

&#x20; </Accordion>

</AccordionGroup>



\## Prerequisites



<Steps>

&#x20; <Step title="Get API Key">

&#x20;   Visit \[Token Plan subscription page](https://platform.minimax.io/subscribe/token-plan), subscribe to a plan and get your exclusive API Key.

&#x20; </Step>



&#x20; <Step title="Install uvx">

&#x20;   <Tabs>

&#x20;     <Tab title="macOS / Linux">

&#x20;       ```bash theme={null}

&#x20;       curl -LsSf https://astral.sh/uv/install.sh | sh

&#x20;       ```

&#x20;     </Tab>



&#x20;     <Tab title="Windows">

&#x20;       ```powershell theme={null}

&#x20;       powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

&#x20;       ```

&#x20;     </Tab>

&#x20;   </Tabs>



&#x20;   <Note>

&#x20;     For other installation methods, refer to the \[uv repository](https://github.com/astral-sh/uv).

&#x20;   </Note>

&#x20; </Step>



&#x20; <Step title="Verify Installation">

&#x20;   <Tabs>

&#x20;     <Tab title="macOS / Linux">

&#x20;       ```bash theme={null}

&#x20;       which uvx

&#x20;       ```

&#x20;     </Tab>



&#x20;     <Tab title="Windows">

&#x20;       ```powershell theme={null}

&#x20;       (Get-Command uvx).source

&#x20;       ```

&#x20;     </Tab>

&#x20;   </Tabs>



&#x20;   <Note>

&#x20;     If installed correctly, a path will be shown (e.g., `/usr/local/bin/uvx`). If you get `spawn uvx ENOENT` error, you need to configure the absolute path.

&#x20;   </Note>

&#x20; </Step>

</Steps>



\## Use in Claude Code



<Steps>

&#x20; <Step title="Download Claude Code">

&#x20;   Download and install Claude Code from \[Claude Code official website](https://www.claude.com/product/claude-code)

&#x20; </Step>



&#x20; <Step title="Configure MCP">

&#x20;   <Tabs>

&#x20;     <Tab title="Quick Install">

&#x20;       Run the following command in terminal, replace `api\_key` with your API Key:



&#x20;       ```bash theme={null}

&#x20;       claude mcp add -s user MiniMax --env MINIMAX\_API\_KEY=api\_key --env MINIMAX\_API\_HOST=https://api.minimax.io -- uvx minimax-coding-plan-mcp -y

&#x20;       ```

&#x20;     </Tab>



&#x20;     <Tab title="Manual Configuration">

&#x20;       Edit the config file `\~/.claude.json`, add the following MCP configuration:



&#x20;       ```json theme={null}

&#x20;       {

&#x20;         "mcpServers": {

&#x20;           "MiniMax": {

&#x20;             "command": "uvx",

&#x20;             "args": \["minimax-coding-plan-mcp", "-y"],

&#x20;             "env": {

&#x20;               "MINIMAX\_API\_KEY": "MINIMAX\_API\_KEY",

&#x20;               "MINIMAX\_API\_HOST": "https://api.minimax.io"

&#x20;             }

&#x20;           }

&#x20;         }

&#x20;       }

&#x20;       ```

&#x20;     </Tab>

&#x20;   </Tabs>

&#x20; </Step>



&#x20; <Step title="Verify Configuration">

&#x20;   After entering Claude Code, type `/mcp`. If you can see `web\_search` and `understand\_image`, the configuration is successful.



&#x20;   <img src="https://filecdn.minimax.chat/public/59a2ac4d-fe8a-42d9-8898-e81aea641622.png" width="80%" />

&#x20; </Step>

</Steps>



<Note>

&#x20; If you use MCP in an IDE (like TRAE), you also need to configure MCP in the corresponding IDE settings

</Note>



\## Use in Cursor



<Steps>

&#x20; <Step title="Download Cursor">

&#x20;   Download and install Cursor from \[Cursor official website](https://cursor.com/)

&#x20; </Step>



&#x20; <Step title="Open MCP Configuration">

&#x20;   Go to `Cursor -> Preferences -> Cursor Settings -> Tools \& Integrations -> MCP -> Add Custom MCP`



&#x20;   !\[Cursor MCP Configuration](https://filecdn.minimax.chat/public/61982fde-6575-4230-94eb-798f35a60450.png)

&#x20; </Step>



&#x20; <Step title="Add Configuration">

&#x20;   Add the following configuration to `mcp.json` file:



&#x20;   ```json theme={null}

&#x20;   {

&#x20;     "mcpServers": {

&#x20;       "MiniMax": {

&#x20;         "command": "uvx",

&#x20;         "args": \["minimax-coding-plan-mcp"],

&#x20;         "env": {

&#x20;           "MINIMAX\_API\_KEY": "Enter your API key",

&#x20;           "MINIMAX\_MCP\_BASE\_PATH": "Local output directory path, ensure the path exists and is writable",

&#x20;           "MINIMAX\_API\_HOST": "https://api.minimax.io",

&#x20;           "MINIMAX\_API\_RESOURCE\_MODE": "Optional. Resource delivery method: url or local, default url"

&#x20;         }

&#x20;       }

&#x20;     }

&#x20;   }

&#x20;   ```

&#x20; </Step>

</Steps>



\## Use in OpenCode



<Steps>

&#x20; <Step title="Download OpenCode">

&#x20;   Download and install OpenCode from \[OpenCode official website](https://opencode.ai/)

&#x20; </Step>



&#x20; <Step title="Configure MCP">

&#x20;   Edit the config file `\~/.config/opencode/opencode.json`, add the following MCP configuration:



&#x20;   ```json theme={null}

&#x20;   {

&#x20;     "$schema": "https://opencode.ai/config.json",

&#x20;     "mcp": {

&#x20;       "MiniMax": {

&#x20;         "type": "local",

&#x20;         "command": \["uvx", "minimax-coding-plan-mcp", "-y"],

&#x20;         "environment": {

&#x20;           "MINIMAX\_API\_KEY": "MINIMAX\_API\_KEY",

&#x20;           "MINIMAX\_API\_HOST": "https://api.minimax.io"

&#x20;         },

&#x20;         "enabled": true

&#x20;       }

&#x20;     }

&#x20;   }

&#x20;   ```

&#x20; </Step>



&#x20; <Step title="Verify Configuration">

&#x20;   After entering OpenCode, type `/mcp`. If you can see `MiniMax connected`, the configuration is successful.



&#x20;   <img src="https://filecdn.minimax.chat/public/1a24c300-4cff-40ee-a428-869467074c1d.png" width="80%" />

&#x20; </Step>

</Steps>



