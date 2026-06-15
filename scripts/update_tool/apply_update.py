from __future__ import annotations

import argparse
import fnmatch
import json
import os
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Iterable


DEFAULT_CONFIG = {
    "project_name": "Project",
    "preserve_runtime_data": True,
    "preserve_gitkeep_in_data": True,
    "exclude_globs": [
        ".git/**",
        ".git",
        ".venv/**",
        "venv/**",
        "env/**",
        "__pycache__/**",
        "**/__pycache__/**",
        ".pytest_cache/**",
        ".mypy_cache/**",
        ".ruff_cache/**",
        ".DS_Store",
        "**/.DS_Store",
        ".update_backups/**",
    ],
    "required_dirs": [],
    "verify_commands": ["python -m unittest discover -s tests"],
}


@dataclass(frozen=True)
class ZipItem:
    source_name: str
    rel_path: PurePosixPath
    is_dir: bool


def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        return DEFAULT_CONFIG.copy()
    with config_path.open("r", encoding="utf-8") as f:
        loaded = json.load(f)
    config = DEFAULT_CONFIG.copy()
    config.update(loaded)
    return config


def normalize_zip_name(name: str) -> PurePosixPath | None:
    name = name.replace("\\", "/").strip("/")
    if not name:
        return None
    path = PurePosixPath(name)
    if any(part in ("", ".", "..") for part in path.parts):
        raise ValueError(f"不安全的 zip 路径：{name}")
    return path


def detect_single_root(paths: Iterable[PurePosixPath]) -> str | None:
    paths = list(paths)
    if not paths:
        return None
    first_parts = {path.parts[0] for path in paths if path.parts}
    if len(first_parts) != 1:
        return None
    root = next(iter(first_parts))
    # 如果 zip 里所有内容都在同一个顶层目录下，就自动去掉这个目录。
    if all(len(path.parts) >= 2 for path in paths):
        return root
    return None


def read_zip_items(zip_path: Path) -> list[ZipItem]:
    with zipfile.ZipFile(zip_path, "r") as zf:
        raw_paths: list[PurePosixPath] = []
        for info in zf.infolist():
            path = normalize_zip_name(info.filename)
            if path is not None:
                raw_paths.append(path)

        root = detect_single_root(raw_paths)
        items: list[ZipItem] = []
        for info in zf.infolist():
            path = normalize_zip_name(info.filename)
            if path is None:
                continue
            if root and path.parts and path.parts[0] == root:
                stripped_parts = path.parts[1:]
                if not stripped_parts:
                    continue
                rel_path = PurePosixPath(*stripped_parts)
            else:
                rel_path = path
            items.append(ZipItem(info.filename, rel_path, info.is_dir()))
        return items


def posix(path: PurePosixPath | Path | str) -> str:
    return str(path).replace("\\", "/").strip("/")


def is_excluded(rel_path: PurePosixPath, is_dir: bool, config: dict) -> bool:
    rel = posix(rel_path)
    if not rel:
        return True

    # 默认保护运行期数据：data 下除了 .gitkeep 以外的文件都不覆盖。
    if config.get("preserve_runtime_data", True) and rel.startswith("data/"):
        if config.get("preserve_gitkeep_in_data", True) and rel.endswith("/.gitkeep"):
            return False
        return True

    candidates = [rel]
    if is_dir:
        candidates.append(rel + "/")

    for pattern in config.get("exclude_globs", []):
        pattern = pattern.replace("\\", "/")
        for candidate in candidates:
            if fnmatch.fnmatch(candidate, pattern):
                return True
            if pattern.endswith("/**") and candidate.startswith(pattern[:-3] + "/"):
                return True
    return False


def backup_existing(target: Path, project_root: Path, backup_root: Path, backed_up: set[str]) -> None:
    if not target.exists():
        return
    rel = target.relative_to(project_root)
    key = posix(rel)
    if key in backed_up:
        return
    backup_target = backup_root / rel
    backup_target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_dir():
        if backup_target.exists():
            shutil.rmtree(backup_target)
        shutil.copytree(target, backup_target)
    else:
        shutil.copy2(target, backup_target)
    backed_up.add(key)


def ensure_required_dirs(project_root: Path, config: dict, dry_run: bool) -> list[str]:
    created: list[str] = []
    for rel_dir in config.get("required_dirs", []):
        path = project_root / rel_dir
        gitkeep = path / ".gitkeep"
        if dry_run:
            if not path.exists():
                created.append(f"将创建目录：{rel_dir}")
            continue
        path.mkdir(parents=True, exist_ok=True)
        if not gitkeep.exists():
            gitkeep.write_text("", encoding="utf-8")
        created.append(rel_dir)
    return created


def run_verify(project_root: Path, skip_tests: bool) -> int:
    verify_script = project_root / "scripts" / "update_tool" / "verify_basic.py"
    if not verify_script.exists():
        print("未找到 scripts/update_tool/verify_basic.py，跳过基础检验。")
        return 0
    cmd = [sys.executable, str(verify_script), "--project-root", str(project_root)]
    if skip_tests:
        cmd.append("--skip-tests")
    print("\n开始基础检验...")
    result = subprocess.run(cmd, cwd=str(project_root))
    return result.returncode


def apply_update(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    zip_path = Path(args.zip_file).resolve()
    config_path = project_root / "scripts" / "update_tool" / "update_config.json"
    config = load_config(config_path)

    if not project_root.exists():
        print(f"项目目录不存在：{project_root}")
        return 2
    if not zip_path.exists():
        print(f"更新包不存在：{zip_path}")
        return 2
    if not zipfile.is_zipfile(zip_path):
        print(f"这不是有效 zip 文件：{zip_path}")
        return 2

    items = read_zip_items(zip_path)
    files = [item for item in items if not item.is_dir and not is_excluded(item.rel_path, False, config)]
    skipped = [item for item in items if is_excluded(item.rel_path, item.is_dir, config)]

    print(f"项目：{config.get('project_name', 'Project')}")
    print(f"项目目录：{project_root}")
    print(f"更新包：{zip_path}")
    print(f"将合并文件数：{len(files)}")
    print(f"将跳过项目数：{len(skipped)}")

    if args.dry_run:
        print("\n当前是 dry-run 预览模式，不会修改任何文件。")
        for item in files[:80]:
            print(f"  UPDATE {item.rel_path}")
        if len(files) > 80:
            print(f"  ... 还有 {len(files) - 80} 个文件")
        ensure_required_dirs(project_root, config, dry_run=True)
        return 0

    if not args.yes:
        answer = input("\n确认开始覆盖 / 合并？输入 YES 继续：").strip()
        if answer != "YES":
            print("已取消。")
            return 1

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = project_root / ".update_backups" / timestamp
    backup_root.mkdir(parents=True, exist_ok=True)
    backed_up: set[str] = set()
    written: list[str] = []

    with zipfile.ZipFile(zip_path, "r") as zf:
        for item in files:
            target = project_root / Path(*item.rel_path.parts)
            backup_existing(target, project_root, backup_root, backed_up)
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(item.source_name) as source, target.open("wb") as dest:
                shutil.copyfileobj(source, dest)
            written.append(posix(item.rel_path))

    ensure_required_dirs(project_root, config, dry_run=False)

    print("\n合并完成。")
    print(f"备份目录：{backup_root}")
    print(f"写入文件数：{len(written)}")
    if written:
        for rel in written[:80]:
            print(f"  OK {rel}")
        if len(written) > 80:
            print(f"  ... 还有 {len(written) - 80} 个文件")

    if not args.skip_verify:
        return run_verify(project_root, skip_tests=args.skip_tests)
    print("已按参数跳过基础检验。")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="通用 zip 解压合并工具：备份、覆盖、保留运行数据、基础检验。")
    parser.add_argument("zip_file", help="要合并到项目里的 zip 更新包路径")
    parser.add_argument("--project-root", default=".", help="项目根目录，默认当前目录")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不修改文件")
    parser.add_argument("--yes", action="store_true", help="跳过 YES 确认，适合脚本调用")
    parser.add_argument("--skip-tests", action="store_true", help="基础检验时跳过测试命令")
    parser.add_argument("--skip-verify", action="store_true", help="合并后不运行基础检验")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return apply_update(args)
    except Exception as exc:  # noqa: BLE001 - 这里需要把错误清楚打印给非程序员用户。
        print(f"\n更新失败：{exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
