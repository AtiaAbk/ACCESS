# ACCESS

**Adaptive Cognitive Companion for Efficient System Services**

ACCESS is a cross-platform, offline-first desktop assistant for Windows, macOS,
and Linux. It combines a native graphical interface with local command routing,
desktop automation, file tools, screenshot previews, configurable quick actions,
syntax-highlighted code responses, and locally stored conversation history.

> Version 1.0 · Python · Offline-first · Privacy-focused

## What ACCESS can do

- Open and close supported desktop applications.
- Capture screenshots and show clickable previews in the conversation.
- Open screenshots, reveal them in the file manager, or copy their paths.
- Create, read, find, copy, move, rename, and delete files.
- Lock, sleep, restart, or shut down the computer with confirmation safeguards.
- Display source files with syntax highlighting.
- Store and search recent conversations locally using SQLite.
- Provide configurable Quick Actions with built-in and custom commands.
- Switch between light and dark themes.
- Run as a desktop GUI or classic terminal interface.
- Optionally use a local Ollama model for conversational fallback.
- Speak commands through the microphone using offline recognition.
- Read assistant responses aloud with the operating system's speech engine.
- Schedule persistent reminders with desktop notifications.
- Stay available in the system tray with a global voice shortcut.
- Monitor live CPU, memory, storage, battery, and network activity.

Some system controls depend on the operating system, desktop environment, and
installed utilities. ACCESS reports when an operation is unavailable.

## Quick start

You need Python 3.10 or newer. From the project root:

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python ACCESS\main.py
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python ACCESS/main.py
```

For platform packages, permissions, Linux screenshot utilities, and detailed
troubleshooting, follow [SETUP.md](SETUP.md).

## Using the application

Enter a command in the composer and press **Enter** or select **Send**. Examples:

```text
open chrome
open calculator
take a screenshot
read file ./example.py
search file report
volume up
lock screen
```

Sensitive power actions such as shutdown, restart, and sleep require explicit
confirmation before ACCESS performs them.

### Configuring Quick Actions

Select **SETUP ›** beside **Quick Actions** in the sidebar. The editor lets you:

- add or remove built-in actions;
- move actions up or down;
- create a custom tile that runs any command ACCESS understands;
- restore the default layout; and
- save the layout for future sessions.

Quick Action settings are stored per operating-system user:

| Platform | Settings file |
| --- | --- |
| Windows | `%APPDATA%\ACCESS\settings.json` |
| macOS | `~/Library/Application Support/ACCESS/settings.json` |
| Linux | `$XDG_CONFIG_HOME/ACCESS/settings.json` or `~/.config/ACCESS/settings.json` |

Conversation history is stored locally in
`ACCESS/memory/access_memory.db`.

### Keyboard shortcuts

| Shortcut | Action |
| --- | --- |
| `Enter` | Send the current command |
| `Ctrl+K` or `Ctrl+L` | Focus the command input |
| `Ctrl+N` | Start a new visible conversation |
| `F1` | Show available commands |
| `Ctrl+Shift+V` | Listen for a spoken command |
| `Esc` | Return focus to the command input |

Select the microphone button beside **Send** to speak one command. The speaker
button toggles spoken assistant responses. Voice recognition and speech output
run locally; microphone availability and language support depend on the host
operating system and installed audio devices.

Open **Settings** from the sidebar to choose the microphone, system voice,
speaking rate, volume, theme, reminder notifications, tray behavior, and global
shortcut. When enabled, `Ctrl+Alt+Space` brings ACCESS forward and starts voice
input even while another application is active.

### Reminders

ACCESS stores pending reminders locally and delivers them in the conversation
and through a desktop notification. Examples:

```text
remind me in 10 minutes to check the oven
remind me tomorrow at 9:30 AM to send the report
show reminders
cancel reminder a1b2c3d4
```

Use the identifier shown by `show reminders` when cancelling one.

### System dashboard

Open **Dashboard** from the sidebar or enter `system dashboard`. It refreshes in
the background every two seconds and displays:

- CPU and physical-memory utilization;
- system-drive usage;
- battery charge, power state, and estimated time remaining;
- current network download/upload rates and cumulative totals;
- device name, operating system, uptime, and local IP address; and
- warnings for high CPU, memory, or storage use and low unplugged battery.

Dashboard monitoring is read-only and remains responsive while metrics are
sampled on a worker thread.

The commands `/help`, `?`, `/history`, and `/clear` are also supported.

## Terminal mode

The original terminal interface remains available:

```bash
python ACCESS/main.py --cli
```

## Optional local AI with Ollama

ACCESS works without a language model for its deterministic commands. When
Ollama is running locally, ACCESS can use the configured `qwen3:1.7b` model as a
conversation and intent fallback.

```bash
ollama pull qwen3:1.7b
ollama serve
```

Ollama is optional; if it is unavailable, the rest of ACCESS continues working.

## Project layout

```text
ACCESS/
├── ACCESS/
│   ├── ai/             # intent, planning, and local-model integration
│   ├── core/           # command router and execution engine
│   ├── memory/         # local SQLite conversation memory
│   ├── tools/          # system, file, and screenshot operations
│   ├── ui/             # native GUI and syntax highlighting
│   └── main.py         # application entry point
├── requirements.txt
├── SETUP.md
└── README.md
```

## Safety and privacy

- Conversation memory stays in the local SQLite database.
- Quick Action settings remain in the current user's configuration directory.
- Shutdown, restart, and sleep require confirmation.
- ACCESS does not need an online account for local operations.
- File and system commands operate with the permissions of the current user.

## More help

See [SETUP.md](SETUP.md) for installation and troubleshooting. Inside the GUI,
select **Commands** or enter `/help` to see command examples.
