<div align="center">

# ACCESS

**Adaptive Cognitive Companion for Efficient System Services**

*Intelligent Desktop Assistant & IoT Smart Home/Security Hub*

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows-000000?logo=apple&logoColor=white)
![Version](https://img.shields.io/badge/Version-2.0%20(Tech%20Fair%20Release)-blue)
![Status](https://img.shields.io/badge/Status-Complete%20%26%20Ready-brightgreen)
![Privacy](https://img.shields.io/badge/Privacy-100%25%20Local--First-success)
![License](https://img.shields.io/badge/License-MIT-green)

<img src="banner.png" alt="ACCESS Banner" width="700"/>

</div>

---

ACCESS is an intelligent, offline-first cognitive desktop assistant and smart home hub. Engineered for complete local privacy and responsiveness, ACCESS bridges natural language interaction with direct operating system control and simulated/physical IoT automation. 

Equipped with a modern High-DPI Desktop GUI and a high-performance terminal CLI, ACCESS operates seamlessly without requiring external cloud connectivity or mandatory LLM dependencies.

> 🏆 **Tech Fair Evaluators & Judges**: Check out the comprehensive [TECHFAIR_GUIDE.md](TECHFAIR_GUIDE.md) for 30-second elevator pitches, live demonstration scripts, architecture deep-dives, and technical Q&A sheets.

---

## ✨ Core Features & Capabilities

| Feature Pillar | Description | Status |
| :--- | :--- | :---: |
| ⚡ **Deterministic & Hybrid AI Engine** | Fast regex-based deterministic router for zero-latency execution combined with an AI Goal Detector, compound task planner, and multi-tier conversational fallbacks. | ✅ Working |
| 🏠 **Smart Home & Security Hub** | Room-level IoT device control (lighting, AC/thermostat, curtains, water pump), CCTV camera monitoring, smoke/motion sensor telemetry, and 4-mode security alarm state machine. | ✅ Working |
| 🖥️ **Desktop & OS Automation** | Native control of system volume, display brightness, dark/light theme switching, application lifecycle (launch/terminate), and real-time hardware health metrics. | ✅ Working |
| 🗂️ **File Operations & Screenshots** | Safe file creation, reading, and deletion (with confirmation guardrails and recycle bin safety), file search, and instant screen capture with thumbnail preview. | ✅ Working |
| ⏰ **Background Reminders & Alerts** | Persistent background task scheduler with platform-native notifications (macOS AppleScript, Windows toast, plyer). | ✅ Working |
| 🎙️ **Voice I/O & Accessibility** | Dual-mode speech recognition (PocketSphinx offline + Google online) and native zero-dependency speech synthesis (macOS `say`, Windows SAPI, Linux `espeak`, `pyttsx3`). | ✅ Working |
| 🧾 **Persistent Memory System** | SQLite-backed interaction memory (`access_memory.db`) with fuzzy search and contextual execution (e.g., *"do that again"*). | ✅ Working |
| 🎨 **Dual User Interfaces** | Sleek Dark-Mode Desktop GUI (CustomTkinter/Tkinter) with quick-action shortcuts alongside an interactive, styled Rich Terminal CLI. | ✅ Working |

---

## 🧠 System Architecture

```
                                  USER INPUT
                 ┌────────────────────┴────────────────────┐
                 ▼                                         ▼
     🖥️ Modern Desktop GUI (v2.0)               ⌨️ Rich Terminal CLI
                 └────────────────────┬────────────────────┘
                                      ▼
                        ╔═══════════════════════════╗
                        ║     core.engine.Engine    ║
                        ║     (AccessEngine Core)   ║
                        ╚═══════════════════════════╝
                                      │
              ┌───────────────────────┼───────────────────────┐
              ▼                       ▼                       ▼
    Deterministic Router       AI Decision Layer      Multi-Tiered Fallback
     (Regex Pattern Match)     (Goal & Plan Engine)   (Ollama / Gemini / Heuristics)
              │                       │                       │
              └───────────────────────┼───────────────────────┘
                                      ▼
                      DEVICE & SYSTEM EXECUTION LAYER
       ┌──────────────────────────────┼──────────────────────────────┐
       ▼                              ▼                              ▼
 🖥️ Desktop & OS Tools       🏠 Smart Home Hub (IoT)       ⏰ Services & Memory
 • SystemControl (Apps/Vol)   • Virtual Device Registry     • ReminderService (Daemon)
 • FileTools (Safe I/O)       • Security State Machine      • AccessMemory (SQLite)
 • ScreenshotTool (Grab)      • Sensor / Alarm Dispatch     • VoiceService (Native Audio)
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- macOS or Windows

### Installation
```bash
# 1. Clone repository
git clone https://github.com/AtiaAbk/ACCESS.git
cd ACCESS

# 2. Set up virtual environment
python3 -m venv ACCESS/.venv
source ACCESS/.venv/bin/activate  # On Windows: ACCESS\.venv\Scripts\activate

# 3. Install dependencies
pip install -r ACCESS/requirements.txt
```

### Launching ACCESS

#### 🎨 Desktop GUI Mode (Recommended for Demos)
```bash
python ACCESS/main.py
```
*Launches the responsive desktop interface featuring real-time chat, Quick Action preset buttons (`Live Demo`, `Smart Home`, `System Health`, `Dev Setup`), voice toggle, and system tray integration.*

#### ⌨️ Terminal CLI Mode
```bash
python ACCESS/main.py --cli
```
*Launches the high-performance Rich terminal interface with formatted Markdown tables and colored execution logs.*

---

## 🧪 Running Automated Tests

ACCESS includes a comprehensive 31-test suite covering smart home state management, safety guardrails, engine routing, AST math execution, and planner workflows:

```bash
cd ACCESS
../ACCESS/.venv/bin/python -m unittest discover tests
../ACCESS/.venv/bin/python test_phase5.py
```

---

## 💻 Example Commands to Try

| Category | Voice or Text Command | Expected Action |
| :--- | :--- | :--- |
| **Tech Fair Demo** | `demo` or `showcase` | Displays comprehensive capabilities overview and interactive guide |
| **System Diagnostics** | `system health` or `battery` | Reports real-time CPU %, RAM usage, battery level, and disk stats |
| **Workspace Automation** | `prepare my development workspace` | Automatically opens IDE, terminal, browser, and project folders |
| **Smart Home IoT** | `turn on living room light` | Toggles smart light relay with state persistence |
| **Smart Thermostat** | `set thermostat to 22` | Adjusts climate control target temperature |
| **Security Hub** | `security status` / `arm security away` | Inspects or arms perimeter sensors, door locks, and CCTV feeds |
| **Emergency** | `trigger panic alarm` / `silence alarm` | Activates high-priority emergency sirens and dispatch protocols |
| **System Settings** | `turn on dark mode` / `mute volume` | Modifies native macOS/Windows desktop settings |
| **Safe File Actions** | `find project notes.txt` | Discovers files matching keywords in local directories |
| **Persistent Reminder** | `remind me in 10 minutes to submit report` | Schedules background desktop alert with native notification |
| **Safe Calculation** | `calculate (1500 * 1.15) / 12` | Safe AST-based mathematical evaluation |

---

## 🗺️ Completed Roadmap

- [x] High-performance deterministic rule-based router
- [x] AI decision layer & multi-step compound task planner (Phase 5)
- [x] Safe file operations with confirmation prompts & trash protection
- [x] Instant screenshot capture tool with automatic file storage
- [x] Persistent SQLite interaction memory with fuzzy recall
- [x] Multi-step workspace orchestration (`Dev`, `Presentation`, `Research`)
- [x] Voice input & output with zero-dependency native OS fallbacks
- [x] Comprehensive IoT Smart Home & Security subsystem
- [x] High-DPI Desktop GUI with quick action shortcuts & tray support
- [x] Multi-tiered offline fallback (graceful degradation without internet)

---

## 👥 Authors & Acknowledgments

- **Atia Oishi** ([@AtiaAbk](https://github.com/AtiaAbk)) — *Lead Developer & Architect*

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
