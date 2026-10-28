#!/usr/bin/env python3
"""Platform Surveillance System.

A command-line utility that periodically records system health (CPU, RAM,
network) and per-process metrics into timestamped diagnostic log files.

Usage:
    python PlatformSurveillance.py <interval_in_minutes> <log_folder>

Example:
    python PlatformSurveillance.py 5 SystemLogs
"""

from __future__ import annotations

import argparse
import logging
import os
import signal
import sys
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import psutil
import schedule

__version__ = "1.0.0"

LOGGER = logging.getLogger("platform_surveillance")

BORDER = "-" * 50
BYTES_PER_MB = 1024 ** 2
BYTES_PER_GB = 1024 ** 3
CPU_SAMPLE_SECONDS = 1.0
REPORT_PREFIX = "SystemReport"
FILE_TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"  # Safe on Windows, Linux and macOS
NOT_AVAILABLE = "N/A"

# Raised by psutil when a process exits mid-scan or cannot be inspected.
SKIPPABLE_PROCESS_ERRORS = (
    psutil.NoSuchProcess,
    psutil.AccessDenied,
    psutil.ZombieProcess,
)


# --------------------------------------------------------------------------- #
# Data models
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class SystemMetrics:
    """Snapshot of machine-wide resource usage."""

    cpu_cores: Optional[int]
    cpu_percent: float
    ram_percent: float
    ram_total_gb: float
    ram_available_gb: float
    net_sent_mb: Optional[float]
    net_received_mb: Optional[float]


@dataclass(frozen=True)
class ProcessMetrics:
    """Snapshot of a single running process."""

    pid: int
    name: str
    username: str
    status: str
    cpu_percent: float
    memory_percent: float


# --------------------------------------------------------------------------- #
# Data collection
# --------------------------------------------------------------------------- #
def prime_process_cpu_counters() -> None:
    """Start the CPU measurement window for every process.

    psutil reports process CPU usage relative to the previous call, so the
    first call always returns 0.0. Calling it once here, then reading again
    after the sampling interval, gives meaningful values in every report.
    """
    for proc in psutil.process_iter():
        try:
            proc.cpu_percent(None)
        except SKIPPABLE_PROCESS_ERRORS:
            continue


def collect_system_metrics() -> SystemMetrics:
    """Collect machine-wide CPU, memory and network metrics."""
    memory = psutil.virtual_memory()
    network = psutil.net_io_counters()  # May be None if no interface exists

    return SystemMetrics(
        cpu_cores=psutil.cpu_count(),
        cpu_percent=psutil.cpu_percent(interval=CPU_SAMPLE_SECONDS),
        ram_percent=memory.percent,
        ram_total_gb=memory.total / BYTES_PER_GB,
        ram_available_gb=memory.available / BYTES_PER_GB,
        net_sent_mb=network.bytes_sent / BYTES_PER_MB if network else None,
        net_received_mb=network.bytes_recv / BYTES_PER_MB if network else None,
    )


def collect_process_metrics() -> Tuple[List[ProcessMetrics], int]:
    """Collect metrics for all running processes.

    Returns:
        A tuple of (process metrics, number of processes skipped because they
        exited during the scan or could not be accessed).
    """
    processes: List[ProcessMetrics] = []
    skipped = 0

    for proc in psutil.process_iter():
        try:
            with proc.oneshot():
                info = proc.as_dict(attrs=["pid", "name", "username", "status"])
                cpu_percent = proc.cpu_percent(None)
                memory_percent = proc.memory_percent()
        except SKIPPABLE_PROCESS_ERRORS:
            skipped += 1
            LOGGER.debug("Skipped process %s (exited or access denied)", proc.pid)
            continue

        processes.append(
            ProcessMetrics(
                pid=info["pid"],
                name=info["name"] or NOT_AVAILABLE,
                username=info["username"] or NOT_AVAILABLE,
                status=info["status"] or NOT_AVAILABLE,
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
            )
        )

    return processes, skipped


# --------------------------------------------------------------------------- #
# Report generation
# --------------------------------------------------------------------------- #
def _format_mb(value: Optional[float]) -> str:
    return f"{value:.2f} MB" if value is not None else NOT_AVAILABLE


def render_report(
    system: SystemMetrics,
    processes: Sequence[ProcessMetrics],
    skipped: int,
    generated_at: datetime,
) -> str:
    """Build the full text of a diagnostics report."""
    lines: List[str] = [
        BORDER,
        "Platform Surveillance System - Diagnostics Log",
        f"Generated At: {generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
        BORDER,
        "",
        "---------------- System Summary ----------------",
        f"Active CPU Cores : {system.cpu_cores if system.cpu_cores else NOT_AVAILABLE}",
        f"CPU Utilization  : {system.cpu_percent:.1f}%",
        BORDER,
        f"RAM Utilization  : {system.ram_percent:.1f}%",
        f"Total RAM        : {system.ram_total_gb:.2f} GB",
        f"Available RAM    : {system.ram_available_gb:.2f} GB",
        BORDER,
        "Network Activity (since system boot)",
        f"Sent     : {_format_mb(system.net_sent_mb)}",
        f"Received : {_format_mb(system.net_received_mb)}",
        BORDER,
        "",
        f"---------------- Active Processes ({len(processes)}) ---------------",
    ]

    for proc in processes:
        lines.extend(
            [
                f"PID        : {proc.pid}",
                f"Name       : {proc.name}",
                f"User       : {proc.username}",
                f"Status     : {proc.status}",
                f"CPU Usage  : {proc.cpu_percent:.2f}%",
                f"RAM Usage  : {proc.memory_percent:.2f}%",
                BORDER,
            ]
        )

    lines.extend(
        [
            f"Skipped Processes : {skipped}",
            "--------------- End of Log File ----------------",
            BORDER,
            "",
        ]
    )
    return "\n".join(lines)


def ensure_log_directory(folder: Path) -> None:
    """Create the log directory if needed.

    Raises:
        NotADirectoryError: If the path exists but is not a directory.
        OSError: If the directory cannot be created.
    """
    if folder.exists() and not folder.is_dir():
        raise NotADirectoryError(f"'{folder}' exists but is not a directory")
    folder.mkdir(parents=True, exist_ok=True)


def write_report(folder: Path, content: str, generated_at: datetime) -> Path:
    """Write a report atomically so readers never see a half-written file."""
    file_name = f"{REPORT_PREFIX}_{generated_at.strftime(FILE_TIMESTAMP_FORMAT)}.log"
    target = folder / file_name
    temporary = target.with_suffix(".log.tmp")

    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, target)
    return target


# --------------------------------------------------------------------------- #
# Scan job and scheduler
# --------------------------------------------------------------------------- #
def run_scan(folder: Path) -> Optional[Path]:
    """Run one full scan and save the report.

    Any failure is logged and swallowed so a single bad scan never stops
    the scheduler.
    """
    try:
        prime_process_cpu_counters()
        system = collect_system_metrics()  # Blocks for CPU_SAMPLE_SECONDS
        processes, skipped = collect_process_metrics()

        generated_at = datetime.now()
        report = render_report(system, processes, skipped, generated_at)
        report_path = write_report(folder, report, generated_at)
    except Exception:  # noqa: BLE001 - keep the monitoring loop alive
        LOGGER.exception("Scan failed")
        return None

    LOGGER.info("System report saved to: %s", report_path)
    return report_path


def install_signal_handlers(stop_event: threading.Event) -> None:
    """Stop the monitoring loop cleanly on Ctrl+C or SIGTERM."""

    def _handle(signum: int, _frame: object) -> None:
        LOGGER.info("Received %s. Shutting down...", signal.Signals(signum).name)
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, _handle)


def monitor(interval_minutes: int, folder: Path) -> None:
    """Run a scan immediately, then repeat every `interval_minutes`."""
    stop_event = threading.Event()
    install_signal_handlers(stop_event)

    scheduler = schedule.Scheduler()
    scheduler.every(interval_minutes).minutes.do(run_scan, folder)

    LOGGER.info("Monitoring started. Interval: %d minute(s).", interval_minutes)
    LOGGER.info("Log directory: %s", folder.resolve())
    LOGGER.info("Press Ctrl + C to stop.")

    run_scan(folder)  # First report right away, not after one full interval
    while not stop_event.is_set():
        scheduler.run_pending()
        stop_event.wait(1)

    LOGGER.info("Monitoring stopped.")


# --------------------------------------------------------------------------- #
# Command-line interface
# --------------------------------------------------------------------------- #
def positive_int(value: str) -> int:
    """argparse type: an integer greater than zero."""
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}' is not a valid integer") from None
    if number < 1:
        raise argparse.ArgumentTypeError("interval must be at least 1 minute")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="PlatformSurveillance.py",
        description=(
            "Periodically records CPU, RAM, network and per-process metrics "
            "into timestamped log files."
        ),
        epilog="Example: python PlatformSurveillance.py 5 SystemLogs",
    )
    parser.add_argument(
        "interval",
        type=positive_int,
        help="time between scans, in minutes (integer >= 1)",
    )
    parser.add_argument(
        "log_folder",
        type=Path,
        help="folder where report files are saved (created if missing)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="show debug messages"
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    return parser


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Program entry point. Returns a process exit code."""
    args = build_parser().parse_args(argv)
    configure_logging(args.verbose)

    try:
        ensure_log_directory(args.log_folder)
    except OSError as error:
        LOGGER.error("Cannot use log directory: %s", error)
        return 1

    monitor(args.interval, args.log_folder)
    return 0


if __name__ == "__main__":
    sys.exit(main())
