# PlatformSurveillance - Automated System & Process Monitoring Utility

**PlatformSurveillance** is a Python-based system automation tool built to monitor process execution metrics, CPU and memory usage, and network activity with precise timestamps and structured logging.

---

## Motivation & Thought Process

In modern system administration, server management, and automated dev environments, background applications and long-running services can experience memory leaks, abnormal CPU spikes, or network bottlenecks. Manually inspecting process lists and resource usage in real time is inefficient and prone to missed anomalies.

`PlatformSurveillance` was created as an automated background utility to solve system diagnostic tracking. The goal was to build a script that:
- Periodically records total system health and individual process behaviors on a customizable schedule.
- Captures system metrics including core usage, physical memory allocation, network throughput, and per-process memory/CPU utilization.
- Writes continuous, structured, timestamped audit reports to an isolated logging folder.
- Operates quietly across OS environments while gracefully managing access restrictions and missing processes.

---

## Architecture & System Flow

```
+------------------+     +------------------------+     +--------------------------+
|  User Command /  | --> | Argument & Interval    | --> | Target Log Directory     |
|  Scheduled Loop  |     | Flag Parsing           |     | Validation & Creation    |
+------------------+     +------------------------+     +--------------------------+
                                                                     |
                                                                     v
+------------------+     +------------------------+     +--------------------------+
| Continuous       | <-- | Scan Active Processes  | <-- | Capture CPU, RAM, &      |
| `schedule` Loop  |     | & Log Execution Stats  |     | Network System Metrics   |
+------------------+     +------------------------+     +--------------------------+
```

1. **CLI Argument Parsing:** Evaluates user inputs for documentation flags (`--h`, `--u`) or monitoring loop parameters (`<Interval_In_Minutes>` and `<Log_Folder_Name>`).
2. **Directory Guarding:** Verifies the existence of the specified log directory (`os.path.exists`) and creates it if it does not exist.
3. **Hardware & Resource Profiling:** Captures CPU core counts, overall CPU utilization percentage, RAM consumption, and network bytes transferred via `psutil`.
4. **Process Inspection:** Iterates through all running processes using `psutil.process_iter()`, safely fetching execution details (PID, Name, Username, Status, CPU %, and RAM %).
5. **Timestamped Audit Logging:** Compiles system health data and process snapshots into custom-named log files (`SystemReport_<timestamp>.log`).

---

## Technical Challenges & Solutions

### 1. Ephemeral Process Handling & Exceptions
- **Challenge:** Processes frequently spawn and terminate during system scans. Accessing process metrics on terminated or elevated system processes caused unhandled `psutil.NoSuchProcess`, `psutil.AccessDenied`, or `psutil.ZombieProcess` exceptions.
- **Solution:** Encapsulated individual process iteration inside `try-except` blocks to silently bypass dead or restricted processes without halting the overall diagnostic routine.

### 2. Multi-Platform Timestamp Naming
- **Challenge:** Generating log filenames with standard timestamp formatting can include spaces or illegal characters (such as colons `:` on Windows systems).
- **Solution:** Formatted output file names using strict, OS-safe date string formatting (`%Y-%m-%d_%H-%M-%S`), ensuring cross-platform file system compatibility across Windows, Linux, and macOS.

### 3. Loop Interruption & Clean Exit
- **Challenge:** Terminating continuous background tasks using `Ctrl + C` often prints multi-line stack trace errors in terminal outputs.
- **Solution:** Intercepted execution loops with a `KeyboardInterrupt` exception block to catch termination signals cleanly and notify the user upon exit.

---

## Features

- **Active Process Scanning:** Fetches runtime stats for all active processes, including PID, ownership, CPU %, and RAM %.
- **System Metrics Capture:** Records total CPU utilization, available CPU cores, RAM allocation, and network traffic metrics.
- **Timestamped Audit Logging:** Generates isolated, timestamped diagnostic logs (`SystemReport_YYYY-MM-DD_HH-MM-SS.log`).
- **Automated Loop Execution:** Built-in cron-style background scheduling managed via Python's `schedule` library.
- **Interactive CLI Flags:** Features dedicated help (`--h`) and usage (`--u`) options.

---

## Directory Structure

```
PlatformSurveillance/
├── PlatformSurveillance.py   # Main automation script
├── requirements.txt          # Project dependencies
├── README.md                 # Documentation
└── .gitignore                # Git ignore configuration
```

---

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Prathmesh-Girme/PlatformSurveillance.git
   cd PlatformSurveillance
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage Examples

### 1. View Help Flags

```bash
python PlatformSurveillance.py --h
```

**Output:**
```text
--------------------------------------------------
Platform Surveillance System
--------------------------------------------------
Utility Capabilities:
1. Scans active system processes and execution metrics.
2. Captures RAM utilization and memory capacity.
3. Tracks network bytes sent and received.
4. Evaluates total processor usage across CPU cores.
5. Executes periodic automated monitoring background loops.
6. Outputs formatted, timestamped log reports.
--------------------------------------------------
```

### 2. View Usage Guide

```bash
python PlatformSurveillance.py --u
```

**Output:**
```text
--------------------------------------------------
Platform Surveillance System
--------------------------------------------------
Usage Options:
python PlatformSurveillance.py <Interval_In_Minutes> <Log_Folder_Name>
Example: python PlatformSurveillance.py 5 SystemLogs
--------------------------------------------------
```

### 3. Real-World Execution Walkthrough

#### **Run Command:**
```bash
python PlatformSurveillance.py 5 SystemLogs
```

#### **Terminal Output:**
```text
--------------------------------------------------
Platform Surveillance System
--------------------------------------------------
[INFO] Created log directory: SystemLogs
[INFO] Monitoring loop initialized. Running every 5 minute(s)...
[INFO] Press Ctrl + C to stop execution.
[SUCCESS] System report saved to: SystemLogs/SystemReport_2026-09-30_11-20-00.log
```

#### **Generated Audit Log Content (`SystemLogs/SystemReport_2026-09-30_11-20-00.log`):**
```text
--------------------------------------------------
Platform Surveillance System - Diagnostics Log
Generated At: 2026-09-30_11-20-00
--------------------------------------------------

---------------- System Summary ----------------
Active CPU Cores : 8
CPU Utilization  : 12.4%
--------------------------------------------------
RAM Utilization  : 45.20%
Total Available  : 15.82 GB
--------------------------------------------------
Network Activity
Sent     : 142.50 MB
Received : 890.12 MB
--------------------------------------------------

---------------- Active Processes ---------------
PID        : 1234
Name       : python.exe
User       : Prathmesh
Status     : running
CPU Usage  : 2.10%
RAM Usage  : 0.85%
--------------------------------------------------
PID        : 5678
Name       : chrome.exe
User       : Prathmesh
Status     : sleeping
CPU Usage  : 0.50%
RAM Usage  : 3.12%
--------------------------------------------------
--------------- End of Log File ----------------
--------------------------------------------------
```

---

## Author

**Prathmesh Girme**
- GitHub: [@Prathmesh-Girme](https://github.com/Prathmesh-Girme)
