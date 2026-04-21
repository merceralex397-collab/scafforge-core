---
source_url: https://opencode.ai/docs/themes
fetched_with: http
---

# Themes

Select a built-in theme or define your own.

With OpenCode you can select from one of several built-in themes, use a theme that adapts to your terminal theme, or define your own custom theme.

By default, OpenCode uses our own `opencode`

theme.

For themes to display correctly with their full color palette, your terminal must support **truecolor** (24-bit color). Most modern terminals support this by default, but you may need to enable it:

**Check support**: Run`echo $COLORTERM`

- it should output`truecolor`

or`24bit`

**Enable truecolor**: Set the environment variable`COLORTERM=truecolor`

in your shell profile**Terminal compatibility**: Ensure your terminal emulator supports 24-bit color (most modern terminals like iTerm2, Alacritty, Kitty, Windows Terminal, and recent versions of GNOME Terminal do)

Without truecolor support, themes may appear with reduced color accuracy or fall back to the nearest 256-color approximation.

OpenCode comes with several built-in themes.

| Name | Description |
|---|---|
`system` | Adapts to your terminal’s background color | `tokyonight` | Based on the Tokyonight theme | `everforest` | Based on the Everforest theme | `ayu` | Based on the Ayu dark theme | `catppuccin` | Based on the Catppuccin theme | `catppuccin-macchiato` | Based on the Catppuccin theme | `gruvbox` | Based on the Gruvbox theme | `kanagawa` | Based on the Kanagawa theme | `nord` | Based on the Nord theme | `matrix` | Hacker-style green on black theme | `one-dark` | Based on the Atom One Dark theme |

And more, we are constantly adding new themes.

The `system`

theme is designed to automatically adapt to your terminal’s color scheme. Unlike traditional themes that use fixed colors, the *system* theme:

**Generates gray scale**: Creates a custom gray scale based on your terminal’s background color, ensuring optimal contrast.**Uses ANSI colors**: Leverages standard ANSI colors (0-15) for syntax highlighting and UI elements, which respect your terminal’s color palette.**Preserves terminal defaults**: Uses`none`

for text and background colors to maintain your terminal’s native appearance.

The system theme is for users who:

- Want OpenCode to match their terminal’s appearance
- Use custom terminal color schemes
- Prefer a consistent look across all terminal applications

You can select a theme by bringing up the theme select with the `/theme`

command. Or you can specify it in your config.

OpenCode supports a flexible JSON-based theme system that allows users to create and customize themes easily.

Themes are loaded from multiple directories in the following order where later directories override earlier ones:

**Built-in themes**- These are embedded in the binary**User config directory**- Defined in`~/.config/opencode/themes/*.json`

or`$XDG_CONFIG_HOME/opencode/themes/*.json`

**Project root directory**- Defined in the`<project-root>/.opencode/themes/*.json`

**Current working directory**- Defined in`./.opencode/themes/*.json`

If multiple directories contain a theme with the same name, the theme from the directory with higher priority will be used.

To create a custom theme, create a JSON file in one of the theme directories.

For user-wide themes:

And for project-specific themes.

Themes use a flexible JSON format with support for:

**Hex colors**:`"#ffffff"`

**ANSI colors**:`3`

(0-255)**Color references**:`"primary"`

or custom definitions**Dark/light variants**:`{"dark": "#000", "light": "#fff"}`

**No color**:`"none"`

- Uses the terminal’s default color or transparent

The `defs`

section is optional and it allows you to define reusable colors that can be referenced in the theme.

The special value `"none"`

can be used for any color to inherit the terminal’s default color. This is particularly useful for creating themes that blend seamlessly with your terminal’s color scheme:

`"text": "none"`

- Uses terminal’s default foreground color`"background": "none"`

- Uses terminal’s default background color

Here’s an example of a custom theme:
