#!/usr/bin/env python3
"""
Autonomous DevOps & CI/CD Telemetry Platform - Concurrent Dev Server
---------------------------------------------------------------------
Launches both the FastAPI backend (port 8000) and Vite React frontend (port 5173)
concurrently with synchronized logging and clean shutdown on Ctrl+C.
"""

import os
import sys
import subprocess
import signal
import time

CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
RESET = "\033[0m"
BOLD = "\033[1m"


def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(root_dir, "frontend")

    print(f"\n{BOLD}{CYAN}================================================================={RESET}")
    print(f"{BOLD}{CYAN}   AUTONOMOUS DEVOPS PLATFORM - CONCURRENT DEV LAUNCHER          {RESET}")
    print(f"{BOLD}{CYAN}================================================================={RESET}")
    print(f"Backend API  : {BOLD}http://127.0.0.1:8000{RESET} (Docs: http://127.0.0.1:8000/docs)")
    print(f"Frontend UI  : {BOLD}http://127.0.0.1:5173{RESET} (Vite with HMR & WebSocket proxy)")
    print(f"Built UI     : {BOLD}http://127.0.0.1:8000/dashboard{RESET}")
    print(f"Press {YELLOW}Ctrl+C{RESET} to stop all services simultaneously.\n")

    # Locate Python in .venv if available
    venv_python = os.path.join(root_dir, ".venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        venv_python = os.path.join(root_dir, ".venv", "bin", "python")
    if not os.path.exists(venv_python):
        venv_python = sys.executable

    # Check for npm / node
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"

    processes = []
    try:
        # 1. Start FastAPI backend
        print(f"{GREEN}[LAUNCHING]{RESET} FastAPI backend server...")
        backend_proc = subprocess.Popen(
            [venv_python, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
            cwd=root_dir,
        )
        processes.append(("Backend", backend_proc))

        # Give backend a moment to bind port
        time.sleep(1.5)

        # 2. Start Vite frontend
        print(f"{MAGENTA}[LAUNCHING]{RESET} Vite React frontend...")
        frontend_proc = subprocess.Popen(
            [npm_cmd, "run", "dev"],
            cwd=frontend_dir,
            shell=(sys.platform == "win32"),
        )
        processes.append(("Frontend", frontend_proc))

        print(f"\n{GREEN}[READY]{RESET} Both services are running concurrently!\n")

        # Wait for either process to terminate
        while True:
            for name, proc in processes:
                ret = proc.poll()
                if ret is not None:
                    print(f"\n{YELLOW}[NOTICE]{RESET} {name} process exited with code {ret}")
                    return
            time.sleep(0.5)

    except KeyboardInterrupt:
        print(f"\n{YELLOW}Shutting down dev servers gracefully...{RESET}")
    finally:
        for name, proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        print(f"{GREEN}[DONE]{RESET} All services stopped cleanly.")


if __name__ == "__main__":
    main()

