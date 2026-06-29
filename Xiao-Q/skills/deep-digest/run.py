import subprocess
import json

def run(input_path, mode="insight", length="medium"):
    cmd = [
        "summarize",
        input_path,
        "--length", length
    ]

    # YouTube 特殊处理
    if "youtube.com" in input_path or "youtu.be" in input_path:
        cmd.extend(["--youtube", "auto"])

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return {"error": result.stderr}

    return {
        "raw": result.stdout,
        "mode": mode
    }