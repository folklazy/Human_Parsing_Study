"""Start/inspect/stop only this app's owned local services; never other jobs."""

from pathlib import Path
import argparse, json, os, signal, subprocess, time, sys,fcntl

P = Path(__file__).resolve().parents[1]
local_env = {}
for path in [P / ".runtime/app.env", P / ".env"]:
    if path.exists():
        for line in path.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                local_env[key.strip()] = value.strip().strip('"').strip("'")
local_env.update(os.environ)
W = Path(local_env.get("BODY_WORKSPACE", P.parent)).resolve()
R = P / ".runtime"
R.mkdir(exist_ok=True)
manifest = R / "services.json"


def alive(row):
    try:
        cmd = Path("/proc") / str(row["pid"]) / "cmdline"
        return row["marker"] in cmd.read_bytes().decode().replace("\x00", " ")
    except (FileNotFoundError, ProcessLookupError):
        return False


def start():
    rows = json.loads(manifest.read_text()) if manifest.exists() else {}
    env = local_env.copy()
    env["PYTHONPATH"] = str(P / "backend")
    python = W / ".venvs/body-extraction-api/bin/python"
    commands = {
        "api": [
            str(python),
            "-m",
            "uvicorn",
            "app.api:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8038",
            "--no-access-log",
        ],
        "worker": [str(python), "-m", "app.worker"],
    }
    for role, cmd in commands.items():
        if role in rows and alive(rows[role]):
            continue
        with (R / (role + ".log")).open("ab", buffering=0) as log:
            process = subprocess.Popen(
                cmd,
                cwd=P,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        rows[role] = dict(
            pid=process.pid,
            marker="app.api:app" if role == "api" else "app.worker",
            command=cmd,
        )
        manifest.write_text(json.dumps(rows, indent=2))
        time.sleep(0.5)
    return rows


if __name__ == "__main__":
    service_lock=(R/'services.lock').open('a')
    fcntl.flock(service_lock,fcntl.LOCK_EX)
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["start", "status", "stop", "restart-api"])
    a = parser.parse_args()
    rows = (
        start()
        if a.action == "start"
        else json.loads(manifest.read_text())
        if manifest.exists()
        else {}
    )
    if a.action == "restart-api":
        if rows.get("api") and alive(rows["api"]):
            os.kill(rows["api"]["pid"], signal.SIGTERM)
        time.sleep(1)
        rows = start()
    if a.action == "stop":
        for role, row in rows.items():
            if alive(row):
                os.kill(row["pid"], signal.SIGTERM)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and any(alive(row) for row in rows.values()):
            time.sleep(0.2)
    for role, row in rows.items():
        print(role, row["pid"], "RUNNING" if alive(row) else "STOPPED")
