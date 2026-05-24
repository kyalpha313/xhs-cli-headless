#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_COMMANDS = [
    {"name": "status", "args": ["status"], "expected": [0, 1]},
    {"name": "whoami", "args": ["whoami"], "expected": [0, 1]},
    {"name": "auth_doctor", "args": ["auth", "doctor"], "expected": [0, 1]},
]

DISCOVERY_COMMANDS = [
    {"name": "hot", "args": ["hot"], "expected": [0, 1]},
    {"name": "feed", "args": ["feed"], "expected": [0, 1]},
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run agent-oriented xhs smoke checks.")
    parser.add_argument("--xhs-binary", default="xhs", help="Path or executable name for xhs.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    parser.add_argument("--include-discovery", action="store_true", help="Also run hot/feed/search checks.")
    parser.add_argument("--search-query", default="AI agent", help="Search query for discovery checks.")
    return parser.parse_args()


def run_wrapper(root: Path, xhs_binary: str, spec: dict[str, Any]) -> dict[str, Any]:
    proc = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "run_xhs.py"),
            "--xhs-binary",
            xhs_binary,
            "--append-json-flag",
            *spec["args"],
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        payload = {"ok": False, "exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
    return {
        "name": spec["name"],
        "ok": payload.get("exit_code") in spec["expected"],
        "expected_exit_codes": spec["expected"],
        "result": payload,
    }


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parent.parent
    resolved = shutil.which(args.xhs_binary)
    env_ok = resolved is not None or args.xhs_binary != "xhs"

    command_specs = list(DEFAULT_COMMANDS)
    if args.include_discovery:
        command_specs.extend(DISCOVERY_COMMANDS)
        command_specs.append({"name": "search", "args": ["search", args.search_query], "expected": [0, 1]})

    commands = [run_wrapper(root, args.xhs_binary, spec) for spec in command_specs] if env_ok else []
    report = {
        "ok": env_ok and all(item["ok"] for item in commands),
        "root_dir": str(root),
        "xhs_binary": resolved or args.xhs_binary,
        "env_check": {
            "ok": env_ok,
            "error": "" if env_ok else "未找到 `xhs` 可执行文件，请先安装 xhs-cli-headless。",
        },
        "commands": commands,
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"xhs smoke check: {'ok' if report['ok'] else 'failed'}")
        if report["env_check"]["error"]:
            print(report["env_check"]["error"])
        for item in commands:
            print(f"- {item['name']}: {'ok' if item['ok'] else 'failed'}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
