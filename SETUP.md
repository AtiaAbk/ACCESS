# ACCESS Setup Guide

This guide installs and runs ACCESS on Windows, macOS, and Linux. Commands are
shown from the project root—the directory containing this file and
`requirements.txt`.

## 1. Requirements

- Python 3.10 or newer
- `pip`
- Tkinter, which provides the native graphical interface
- An active desktop session for screenshots and application launching
- Git only if you are cloning the repository

Check Python before continuing:

```bash
python --version
```

On systems where the command is named `python3`:

```bash
python3 --version
```

## 2. Get the project

Clone the repository using its Git URL, or download and extract the source
archive. Then open a terminal in the extracted project root.

```bash
git clone <repository-url>
cd ACCESS
```

Replace `<repository-url>` with the HTTPS or SSH URL shown by the repository
host. If you downloaded a ZIP archive, extract it and open that folder instead.

The correct directory contains:

```text
README.md
SETUP.md
requirements.txt
ACCESS/
```

## 3. Install on Windows

Python from [python.org](https://www.python.org/downloads/) normally includes
Tkinter. During installation, enable **Add Python to PATH**.

Open PowerShell in the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python ACCESS\main.py
```

If PowerShell blocks virtual-environment activation, either run ACCESS without
activation:

```powershell
.\.venv\Scripts\python.exe ACCESS\main.py
```

or allow locally created scripts for the current user:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Windows screenshot capture uses built-in PowerShell and .NET components, so no
additional screenshot utility is required.

## 4. Install on macOS

Install a current Python release from [python.org](https://www.python.org/downloads/)
or Homebrew. Ensure the selected Python build includes Tkinter.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python ACCESS/main.py
```

If a Homebrew Python installation cannot import Tkinter, install the matching
Tk package offered by Homebrew, or use the python.org installer.

The first screenshot attempt may trigger a macOS permission prompt. If capture
fails, open:

**System Settings → Privacy & Security → Screen & System Audio Recording**

Allow the terminal or Python application running ACCESS, then restart ACCESS.
Screenshots use the built-in `screencapture` command. Opening and revealing files
uses the built-in `open` command.

## 5. Install on Linux

Package names differ by distribution. Install Python, virtual-environment
support, Tkinter, and at least one screenshot utility.

### Ubuntu, Debian, and Linux Mint

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip python3-tk gnome-screenshot
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python ACCESS/main.py
```

For a Wayland compositor, `grim` may be a better screenshot backend when it is
available in your distribution.

### Fedora

```bash
sudo dnf install python3 python3-pip python3-tkinter gnome-screenshot
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python ACCESS/main.py
```

### Arch Linux and Manjaro

```bash
sudo pacman -S python python-pip tk grim
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python ACCESS/main.py
```

ACCESS tries these Linux screenshot backends in order when available:

1. `gnome-screenshot`
2. `grim`, especially for Wayland compositors
3. ImageMagick `import`
4. `scrot`
5. PyAutoGUI fallback

Opening screenshot attachments uses `xdg-open`. Install `xdg-utils` if your
distribution does not provide it by default. Application Quick Actions resolve
common GNOME, KDE Plasma, Xfce, MATE, and other desktop executables when present.

## 6. First launch

Start the GUI from the project root:

```bash
python ACCESS/main.py
```

Use `python3` instead when required by your system. A successful launch shows:

- the ACCESS sidebar;
- engine, mode, and platform status cards;
- the conversation area;
- configurable Quick Actions; and
- the command composer.

Try these safe checks:

```text
status
open calculator
take a screenshot
help
```

After a screenshot, ACCESS should display a thumbnail attachment with **Open
image**, **Show in folder**, and **Copy path** actions.

## 7. Configure Quick Actions

Select **SETUP ›** next to **Quick Actions**.

- Select an existing action and use **Move up** or **Move down**.
- Select **Remove** to hide it.
- Choose an unused built-in action and select **Add selected**.
- Select **Add custom…** to provide a button label and an ACCESS command.
- Select **Reset defaults** to restore the original launcher.
- Select **Save layout** to apply and persist the configuration.

Custom actions must contain commands ACCESS already understands, such as
`open chrome`, `take a screenshot`, or `status`. Up to 24 actions can be saved.

## 8. Optional Ollama setup

Ollama is not required for desktop commands. To enable local conversational
fallback, install Ollama separately and run:

```bash
ollama pull qwen3:1.7b
ollama serve
```

ACCESS looks for Ollama at `http://127.0.0.1:11434`. If it is offline, ACCESS
continues using deterministic command routing.

## 9. Terminal-only mode

If the graphical desktop is unavailable, use:

```bash
python ACCESS/main.py --cli
```

Terminal mode requires the `rich` dependency installed by `requirements.txt`.

## 10. Troubleshooting

### `No module named ...`

Activate the virtual environment and reinstall dependencies:

```bash
python -m pip install -r requirements.txt
```

Confirm that `python` and `pip` refer to the same environment:

```bash
python -c "import sys; print(sys.executable)"
python -m pip --version
```

### `No module named tkinter`

- Windows/macOS: use a Python build that includes Tcl/Tk.
- Ubuntu/Debian: `sudo apt install python3-tk`
- Fedora: `sudo dnf install python3-tkinter`
- Arch: `sudo pacman -S tk`

Test Tkinter:

```bash
python -m tkinter
```

### The GUI cannot open in Linux

ACCESS needs an active graphical session. Check that `DISPLAY` is present for
X11 or `WAYLAND_DISPLAY` is present for Wayland. A remote/headless shell should
use `--cli` unless GUI forwarding is configured.

### Screenshot capture fails on Linux

Install a backend appropriate for the desktop session. For example:

```bash
sudo apt install gnome-screenshot
```

Wayland users can install `grim` where supported. Some compositors enforce their
own screenshot permissions or portals.

### Screenshot capture fails on macOS

Grant Screen & System Audio Recording permission to the terminal or Python app
running ACCESS, close ACCESS completely, and launch it again.

### An application Quick Action reports “not found”

The application must be installed. Linux application names vary between desktop
environments; enter `open EXECUTABLE_NAME` or create a custom Quick Action using
the executable available on that computer.

### Screenshot previews do not appear

Reinstall Pillow and restart ACCESS:

```bash
python -m pip install --upgrade Pillow
```

The screenshot path remains available even if thumbnail decoding fails.

### Syntax highlighting is basic or unavailable

Install or update Pygments:

```bash
python -m pip install --upgrade Pygments
```

ACCESS includes a smaller built-in highlighting fallback.

### Reset Quick Actions manually

Close ACCESS and remove the settings file for the current platform:

| Platform | File |
| --- | --- |
| Windows | `%APPDATA%\ACCESS\settings.json` |
| macOS | `~/Library/Application Support/ACCESS/settings.json` |
| Linux | `$XDG_CONFIG_HOME/ACCESS/settings.json` or `~/.config/ACCESS/settings.json` |

ACCESS recreates the default action layout on the next launch. Removing this file
does not remove conversation history.

### Reset conversation history

Conversation history is stored at `ACCESS/memory/access_memory.db`. Back up the
file before removing it. ACCESS creates a fresh database when it next starts.

## 11. Updating ACCESS

After replacing or pulling newer source files, activate the environment and
refresh dependencies:

```bash
python -m pip install --upgrade -r requirements.txt
python ACCESS/main.py
```

User Quick Actions remain in the operating-system settings directory. Existing
conversation history remains in the project database unless it is removed.
