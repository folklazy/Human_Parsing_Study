"""Create private local credentials once; reuse the existing PostgreSQL image."""

from pathlib import Path
import secrets, subprocess, os

p = Path(__file__).resolve().parents[1]
env = p / ".runtime/app.env"
env.parent.mkdir(exist_ok=True)
if not env.exists():
    pg = secrets.token_hex(24)
    text = f"DATABASE_URL=postgresql://body_app:{pg}@127.0.0.1:55438/body_extraction\nBODY_PG_PASSWORD={pg}\nBODY_USERNAME=admin\nBODY_PASSWORD={secrets.token_urlsafe(24)}\nBODY_SECRET={secrets.token_hex(32)}\n"
    with os.fdopen(os.open(env, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as f:
        f.write(text)
subprocess.run(
    [
        "docker",
        "compose",
        "--env-file",
        str(env),
        "-p",
        "body-extraction-human",
        "-f",
        str(p / "compose.yaml"),
        "up",
        "-d",
        "postgres",
    ],
    check=True,
)
print("Database started. Private credentials: .runtime/app.env (not printed).")
