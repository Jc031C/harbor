from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def load_config(project_root: Path) -> dict:
    config_path = project_root / "scripts" / "update_tool" / "update_config.json"
    if not config_path.exists():
        return {"required_dirs": [], "verify_commands": ["python -m unittest discover -s tests"]}
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check_json(path: Path) -> bool:
    if not path.exists():
        print(f"SKIP JSON：{path} 不存在")
        return True
    try:
        json.loads(path.read_text(encoding="utf-8"))
        print(f"OK JSON：{path}")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL JSON：{path}，原因：{exc}")
        return False


def ensure_dirs(project_root: Path, required_dirs: list[str]) -> None:
    for rel in required_dirs:
        path = project_root / rel
        path.mkdir(parents=True, exist_ok=True)
        gitkeep = path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("", encoding="utf-8")
        print(f"OK DIR：{rel}")


def run_command(command: str, project_root: Path) -> bool:
    print(f"\nRUN：{command}")
    normalized = command.replace("python ", f'"{sys.executable}" ', 1) if command.startswith("python ") else command
    result = subprocess.run(normalized, cwd=str(project_root), shell=True)
    if result.returncode == 0:
        print(f"OK CMD：{command}")
        return True
    print(f"FAIL CMD：{command}")
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="项目基础检验：目录、配置 JSON、测试命令。")
    parser.add_argument("--project-root", default=".", help="项目根目录，默认当前目录")
    parser.add_argument("--skip-tests", action="store_true", help="跳过测试命令")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    config = load_config(project_root)

    print(f"项目目录：{project_root}")
    if not project_root.exists():
        print("FAIL：项目目录不存在")
        return 2

    ensure_dirs(project_root, config.get("required_dirs", []))

    ok = True
    ok = check_json(project_root / "config" / "settings.json") and ok

    expected_paths = ["README.md", "src", "tests"]
    for rel in expected_paths:
        path = project_root / rel
        if path.exists():
            print(f"OK PATH：{rel}")
        else:
            print(f"WARN PATH：{rel} 不存在，可能不是 Harbor 标准仓库")

    if args.skip_tests:
        print("\n已跳过测试命令。")
        return 0 if ok else 1

    tests_dir = project_root / "tests"
    if not tests_dir.exists():
        print("\n未找到 tests 目录，跳过测试。")
        return 0 if ok else 1

    for command in config.get("verify_commands", ["python -m unittest discover -s tests"]):
        ok = run_command(command, project_root) and ok

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
