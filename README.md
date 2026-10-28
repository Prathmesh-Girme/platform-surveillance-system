# Platform Surveillance System using Python & psutil

This project demonstrates an **end-to-end system monitoring utility** that tracks **process execution, CPU utilization, memory allocation, and network activity** and saves the results as timestamped diagnostic log files.

It follows **industrial best practices** by:

- Automating periodic scans with the **schedule** library
- Collecting system and process metrics using **psutil**
- Separating collection, report rendering, and file writing into small **typed functions and dataclasses**
- Handling terminated or privileged processes using **exception handling**
- Writing reports **atomically** (temp file, then rename) so a log is never half-written
- Using Python's **logging** module instead of `print` statements
- Providing a standard **argparse CLI** with input validation and proper exit codes
- Shutting down cleanly on **Ctrl + C** and **SIGTERM**

---

## Dependencies

Requires **Python 3.8+**. Install the required Python packages before running the project:

```bash
pip install -r requirements.txt
```

or directly:

```bash
pip install psutil schedule
```

`os`, `sys`, `logging`, `argparse`, `signal`, `threading`, `pathlib`, `datetime` and `dataclasses` are part of the Python standard library and need no installation.

---

## System Information

**Source:** `psutil` (cross-platform library for system and process monitoring)

**System Metrics (7):**

1. Active CPU Cores
2. CPU Utilization (%)
3. RAM Utilization (%)
4. Total RAM (GB)
5. Available RAM (GB)
6. Network Data Sent (MB)
7. Network Data Received (MB)

**Process Attributes (6):**

1. PID
2. Name
3. User
4. Status
5. CPU Usage (%)
6. RAM Usage (%)

**Output:**

- One log file per scan: `SystemReport_YYYY-MM-DD_HH-MM-SS.log`

---

## Workflow

### Argument Parsing

- Parse arguments with `argparse`
- `interval`: minutes between scans (integer, 1 or more)
- `log_folder`: folder where reports are saved
- Optional: `-h / --help`, `-v / --verbose`, `--version`
- Invalid input prints a clear error and exits with code 2

### Directory Validation

- Validate the log folder **at startup** so errors appear immediately
- Create the folder (including parent folders) if it does not exist
- Exit with code 1 if the path exists but is not a directory

### Metrics Collection

- **Step 1:** Start the CPU measurement window for every process
- **Step 2:** Read `psutil.cpu_percent()`, `virtual_memory()` and `net_io_counters()` (this also acts as a 1 second sampling window)
- **Step 3:** Read each process's PID, name, user, status, CPU % and RAM %

### Process Scanning

- Iterate over all running processes using `psutil.process_iter()`
- Skip processes that end during the scan or deny access (`NoSuchProcess`, `AccessDenied`, `ZombieProcess`)
- Count skipped processes and show the count in the report

### Log Writing

- Build the file name from the current timestamp (`%Y-%m-%d_%H-%M-%S`), which is safe on Windows, Linux and macOS
- Write to a temporary file, then rename it to the final name
- A failed scan is logged with its traceback and does **not** stop the monitoring loop

### Scheduling

- Run **one scan immediately**, then repeat using `schedule.every(interval).minutes`
- Check for pending jobs every second until the stop signal arrives
- Press **Ctrl + C** (or send SIGTERM) to stop cleanly, with no stack trace

---

## Running the Project

### Show Help

```bash
python PlatformSurveillance.py --help
```

```text
usage: PlatformSurveillance.py [-h] [-v] [--version] interval log_folder

positional arguments:
  interval       time between scans, in minutes (integer >= 1)
  log_folder     folder where report files are saved (created if missing)

options:
  -h, --help     show this help message and exit
  -v, --verbose  show debug messages
  --version      show program's version number and exit
```

### Start Monitoring

```bash
python PlatformSurveillance.py 5 SystemLogs
```

Expected output:

```text
2026-10-28 11:20:00 [INFO] Monitoring started. Interval: 5 minute(s).
2026-10-28 11:20:00 [INFO] Log directory: /home/user/SystemLogs
2026-10-28 11:20:00 [INFO] Press Ctrl + C to stop.
2026-10-28 11:20:02 [INFO] System report saved to: SystemLogs/SystemReport_2026-10-28_11-20-02.log
2026-10-28 11:25:02 [INFO] System report saved to: SystemLogs/SystemReport_2026-10-28_11-25-02.log
```

### Stop Monitoring

Press **Ctrl + C**:

```text
2026-10-28 11:27:41 [INFO] Received SIGINT. Shutting down...
2026-10-28 11:27:41 [INFO] Monitoring stopped.
```

### Error Handling Examples

```text
$ python PlatformSurveillance.py 0 SystemLogs
PlatformSurveillance.py: error: argument interval: interval must be at least 1 minute

$ python PlatformSurveillance.py 5 existing_file.txt
2026-10-28 11:20:00 [ERROR] Cannot use log directory: 'existing_file.txt' exists but is not a directory
```

---

## Visualizations

- Not applicable. The output is a structured text report that can be read directly or parsed by other tools.

---

## Log Storage

- Reports are saved inside the folder given on the command line (for example `SystemLogs/`)
- Each scan creates a new file, so earlier reports are never overwritten
- File name format: `SystemReport_YYYY-MM-DD_HH-MM-SS.log`

```text
SystemLogs/
├── SystemReport_2026-10-28_11-20-02.log
├── SystemReport_2026-10-28_11-25-02.log
└── SystemReport_2026-10-28_11-30-02.log
```

---

## Sample Log

```text
--------------------------------------------------
Platform Surveillance System - Diagnostics Log
Generated At: 2026-10-28 11:20:02
--------------------------------------------------

---------------- System Summary ----------------
Active CPU Cores : 8
CPU Utilization  : 12.4%
--------------------------------------------------
RAM Utilization  : 45.2%
Total RAM        : 15.82 GB
Available RAM    : 8.67 GB
--------------------------------------------------
Network Activity (since system boot)
Sent     : 142.50 MB
Received : 890.12 MB
--------------------------------------------------

---------------- Active Processes (214) ---------------
PID        : 1234
Name       : python.exe
User       : Prathmesh
Status     : running
CPU Usage  : 2.10%
RAM Usage  : 0.85%
--------------------------------------------------
...
Skipped Processes : 3
--------------- End of Log File ----------------
--------------------------------------------------
```

> **Note:** Network counters are totals since system boot, not per-interval values. Per-process CPU can exceed 100% on multi-core machines because it is measured against a single core. Processes owned by other users may be skipped unless the script runs with elevated privileges.

---

## Author

**Prathmesh Girme**
GitHub: [@Prathmesh-Girme](https://github.com/Prathmesh-Girme)
**Date:** 28/10/2026
