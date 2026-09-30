import os
import sys
import time
import schedule
import psutil

def process_scan():
    """Scans all running processes and retrieves key execution metrics."""
    process_list = []

    for proc in psutil.process_iter():
        try:
            info = proc.as_dict(attrs=["pid", "name", "username", "status"])
            info["cpu_percent"] = proc.cpu_percent(None)
            info["memory_percent"] = proc.memory_percent()
            process_list.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    return process_list


def platform_surveillance(folder_name):
    """Gathers system metrics and active process logs, saving them to a timestamped file."""
    border = "-" * 50

    if not os.path.exists(folder_name):
        try:
            os.mkdir(folder_name)
            print(f"[INFO] Created log directory: {folder_name}")
        except Exception as e:
            print(f"[ERROR] Unable to create directory {folder_name}: {e}")
            return
    elif not os.path.isdir(folder_name):
        print(f"[ERROR] Target path '{folder_name}' exists but is not a directory.")
        return

    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    file_path = os.path.join(folder_name, f"SystemReport_{timestamp}.log")

    try:
        with open(file_path, "w", encoding="utf-8") as fobj:
            fobj.write(f"{border}\n")
            fobj.write("Platform Surveillance System - Diagnostics Log\n")
            fobj.write(f"Generated At: {timestamp}\n")
            fobj.write(f"{border}\n\n")

            fobj.write("---------------- System Summary ----------------\n")
            fobj.write(f"Active CPU Cores : {psutil.cpu_count()}\n")
            fobj.write(f"CPU Utilization  : {psutil.cpu_percent()}%\n")
            fobj.write(f"{border}\n")

            memory = psutil.virtual_memory()
            fobj.write(f"RAM Utilization  : {memory.percent}%\n")
            fobj.write(f"Total Available  : {memory.total / (1024 ** 3):.2f} GB\n")
            fobj.write(f"{border}\n")

            net_io = psutil.net_io_counters()
            fobj.write("Network Activity\n")
            fobj.write(f"Sent     : {net_io.bytes_sent / (1024 * 1024):.2f} MB\n")
            fobj.write(f"Received : {net_io.bytes_recv / (1024 * 1024):.2f} MB\n")
            fobj.write(f"{border}\n\n")

            fobj.write("---------------- Active Processes ---------------\n")
            processes = process_scan()
            for proc in processes:
                fobj.write(f"PID        : {proc.get('pid')}\n")
                fobj.write(f"Name       : {proc.get('name')}\n")
                fobj.write(f"User       : {proc.get('username')}\n")
                fobj.write(f"Status     : {proc.get('status')}\n")
                fobj.write(f"CPU Usage  : {proc.get('cpu_percent'):.2f}%\n")
                fobj.write(f"RAM Usage  : {proc.get('memory_percent'):.2f}%\n")
                fobj.write(f"{border}\n")

            fobj.write("--------------- End of Log File ----------------\n")
            fobj.write(f"{border}\n")

        print(f"[SUCCESS] System report saved to: {file_path}")

    except Exception as e:
        print(f"[ERROR] Failed to write log file: {e}")


def main():
    border = "-" * 50
    print(border)
    print("Platform Surveillance System")
    print(border)

    if len(sys.argv) == 2:
        flag = sys.argv[1].lower()
        if flag == "--h":
            print("Utility Capabilities:")
            print("1. Scans active system processes and execution metrics.")
            print("2. Captures RAM utilization and memory capacity.")
            print("3. Tracks network bytes sent and received.")
            print("4. Evaluates total processor usage across CPU cores.")
            print("5. Executes periodic automated monitoring background loops.")
            print("6. Outputs formatted, timestamped log reports.")
        elif flag == "--u":
            print("Usage Options:")
            print(f"python {sys.argv[0]} <Interval_In_Minutes> <Log_Folder_Name>")
            print("Example: python PlatformSurveillance.py 5 SystemLogs")
        else:
            print("[ERROR] Unrecognized flag. Use --h for help or --u for usage instructions.")

    elif len(sys.argv) == 3:
        try:
            interval = int(sys.argv[1])
            folder_name = sys.argv[2]

            print(f"[INFO] Monitoring loop initialized. Running every {interval} minute(s)...")
            print("[INFO] Press Ctrl + C to stop execution.")

            schedule.every(interval).minutes.do(platform_surveillance, folder_name)

            while True:
                schedule.run_pending()
                time.sleep(1)

        except ValueError:
            print("[ERROR] Time interval must be a valid integer number of minutes.")
        except KeyboardInterrupt:
            print("\n[INFO] Monitoring process terminated by user.")

    else:
        print("[ERROR] Invalid argument count. Use --h for help or --u for usage options.")

    print(border)


if __name__ == "__main__":
    main()