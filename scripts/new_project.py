"""用 template/ 建立一個新的 EUC 專案。

    python scripts/new_project.py <目標資料夾> --name "報表整理工具" --slug report-tool \
        --package reporttool --owner "王小明"

會做的事：
1. 複製 template/，把 __APP_NAME__、__APP_SLUG__、__PACKAGE__、__OWNER__、__TODAY__ 換成實際值。
2. 有安裝 uv 時：產生 app/uv.lock、示意圖與使用手冊 HTML，讓專案一建好就能跑測試與打包。
3. 加上 --git 時，初始化 Git 並做第一個 commit。
"""
from __future__ import annotations

import argparse
import datetime
import re
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL / "template"
TEXT_SUFFIXES = {".py", ".md", ".ps1", ".sh", ".bat", ".toml", ".yml", ".yaml", ".html", ".js", ".css", ".txt"}
TEXT_NAMES = {".gitignore", ".gitattributes", ".python-version"}
BOM = b"\xef\xbb\xbf"


def replace_tokens(path: Path, tokens: dict[str, str]) -> None:
    raw = path.read_bytes()
    has_bom = raw.startswith(BOM)
    text = raw[len(BOM):].decode("utf-8") if has_bom else raw.decode("utf-8")
    for key, value in tokens.items():
        text = text.replace(key, value)
    data = text.encode("utf-8")
    path.write_bytes(BOM + data if has_bom else data)  # Windows PowerShell 5.1 要有 BOM 才讀得懂中文


def run(command: list[str], cwd: Path) -> bool:
    print("  $", " ".join(command), flush=True)
    return subprocess.run(command, cwd=cwd).returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", help="新專案的資料夾（不存在或是空的）")
    parser.add_argument("--name", required=True, help="顯示名稱，例如：報表整理工具")
    parser.add_argument("--slug", required=True, help="資料夾與發布檔名，小寫英數與連字號，例如：report-tool")
    parser.add_argument("--package", help="Python 套件名稱，小寫英數與底線，預設由 slug 去掉連字號")
    parser.add_argument("--owner", default="待填", help="負責人")
    parser.add_argument("--git", action="store_true", help="初始化 Git 並做第一個 commit")
    args = parser.parse_args()

    package = args.package or args.slug.replace("-", "")
    if not re.fullmatch(r"[a-z][a-z0-9-]{1,40}", args.slug):
        sys.exit("--slug 只能用小寫英文、數字與連字號，英文開頭")
    if not re.fullmatch(r"[a-z][a-z0-9_]{1,40}", package):
        sys.exit("--package 只能用小寫英文、數字與底線，英文開頭")
    target = Path(args.target).resolve()
    if target.exists() and any(target.iterdir()):
        sys.exit(f"{target} 已經有檔案，請指定新的資料夾")

    def ignore(folder: str, names: list[str]) -> set[str]:
        skipped = {name for name in names if name in {"__pycache__", ".venv"} or name.endswith(".pyc")}
        if Path(folder) == TEMPLATE:  # 只略過最外層的執行產物，app/examples/workspace 要保留
            skipped |= {name for name in names if name in {"runtime", "workspace", "dist"}}
        return skipped

    shutil.copytree(TEMPLATE, target, dirs_exist_ok=True, ignore=ignore)
    (target / "app" / "__PACKAGE__").rename(target / "app" / package)
    tokens = {
        "__APP_NAME__": args.name,
        "__APP_SLUG__": args.slug,
        "__PACKAGE__": package,
        "__OWNER__": args.owner,
        "__TODAY__": datetime.date.today().isoformat(),
    }
    for path in target.rglob("*"):
        if path.is_file() and (path.suffix in TEXT_SUFFIXES or path.name in TEXT_NAMES):
            replace_tokens(path, tokens)
    for script in ("run.sh", "app/launcher.sh"):
        (target / script).chmod(0o755)
    print(f"已建立 {target}")

    if shutil.which("uv"):
        ok = (run(["uv", "lock", "--project", "app"], target)
              and run(["uv", "run", "--project", "app", "python", "scripts/make_manual_figures.py"], target)
              and run(["uv", "run", "--project", "app", "python", "scripts/build_manual.py"], target))
        if not ok:
            print("uv 步驟沒有完成，之後可以照 docs/maintain.md 手動執行。")
    else:
        print("沒有找到 uv：之後請執行 uv lock --project app，再重建示意圖與使用手冊。")

    if args.git and shutil.which("git"):
        run(["git", "init", "-q"], target)
        run(["git", "add", "-A"], target)
        run(["git", "commit", "-q", "-m", f"建立 {args.name} 專案骨架"], target)

    print(f"""
下一步：
  cd {target}
  uv run --project app pytest tests      # 確認骨架正常
  bash run.sh                            # 或 Windows 雙擊 run.bat
然後填寫 OWNER.md、README.md、docs/design.md 與 docs/user-guide.md 裡標「待填」的地方。""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
