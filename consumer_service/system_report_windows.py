import platform
import subprocess
import shutil
import os
import socket
import psutil
import sys

def run_command(cmd):
    try:
        result = subprocess.check_output(cmd, shell=True, text=True)
        return result.strip()
    except Exception:
        return "N/A"

def get_cpu_info():
    try:
        cpu = run_command("wmic cpu get name,NumberOfCores,NumberOfLogicalProcessors /format:list")
        return cpu.strip()
    except Exception:
        return "N/A"

def get_memory_info():
    mem = psutil.virtual_memory()
    return {
        "Total": f"{round(mem.total / (1024 ** 3), 2)} GB",
        "Available": f"{round(mem.available / (1024 ** 3), 2)} GB",
        "Used": f"{round(mem.used / (1024 ** 3), 2)} GB",
        "Percent Used": f"{mem.percent}%"
    }

def get_disk_info():
    usage = shutil.disk_usage("/")
    return {
        "Total": f"{round(usage.total / (1024 ** 3), 2)} GB",
        "Used": f"{round(usage.used / (1024 ** 3), 2)} GB",
        "Free": f"{round(usage.free / (1024 ** 3), 2)} GB"
    }

def get_python_info():
    return {
        "Version": sys.version.split()[0],
        "Executable": sys.executable
    }

def get_java_info():
    return run_command("java -version")

def get_docker_info():
    return run_command("docker info")

def get_spark_version():
    return run_command("spark-submit --version")

def print_report():
    print("=== SYSTEM REPORT FOR OPTIMIZED CODE DESIGN ===\n")

    print("[OS Information]")
    print(f"OS: {platform.system()} {platform.release()} ({platform.version()})")
    print(f"Machine: {platform.machine()} | Processor: {platform.processor()}")
    print(f"Hostname: {socket.gethostname()}\n")

    print("[CPU Information]")
    print(get_cpu_info(), "\n")

    print("[Memory Information]")
    for k, v in get_memory_info().items():
        print(f"{k}: {v}")
    print()

    print("[Disk Information]")
    for k, v in get_disk_info().items():
        print(f"{k}: {v}")
    print()

    print("[Python Environment]")
    for k, v in get_python_info().items():
        print(f"{k}: {v}")
    print()

    print("[Java Version]")
    print(get_java_info(), "\n")

    print("[Docker Info (if installed)]")
    print(get_docker_info(), "\n")

    print("[Apache Spark Version (if installed)]")
    print(get_spark_version(), "\n")

if __name__ == "__main__":
    print_report()
