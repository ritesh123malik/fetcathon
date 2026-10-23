"""Small process supervisor for one-instance deployments with shared SQLite storage."""

import os
import signal
import subprocess
import sys
import time

from backend.config import settings
from backend.db import Database


def main():
    Database(settings.database_path).initialize(seed=settings.demo_mode)
    commands = [
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.api:app",
            "--host",
            "0.0.0.0",
            "--port",
            os.getenv("PORT", "8000"),
        ]
    ]
    if os.getenv("RUN_AGENTS", "false").lower() == "true":
        if not settings.agent_seed:
            raise SystemExit("RUN_AGENTS=true requires AGENT_SEED.")
        commands.append([sys.executable, "-m", "agents.runtime"])
    children = [subprocess.Popen(command) for command in commands]

    def stop(*_):
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                child.kill()

    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))
    try:
        while True:
            for child in children:
                if child.poll() is not None:
                    raise SystemExit(child.returncode or 1)
            time.sleep(1)
    finally:
        stop()


if __name__ == "__main__":
    main()
