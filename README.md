# python-euc-app

一個 Claude skill：給業務端個人開發的 Python 小工具（End-User Computing）用的專案架構。工具要給同事在自己的 Windows 電腦上使用，不進 production。

- **可攜**：同事不用裝 Python，解壓後雙擊 `run.bat`。uv、Python、套件都放在工具資料夾內。
- **安全**：只在本機執行；本機服務擋 DNS rebinding 與跨站請求；日誌不記資料；發布包用白名單、不含資料。
- **好換版**：新版 ZIP 放進資料夾、雙擊 `run.bat` 就換好，舊版保留可 `rollback`；使用者資料在 `workspace`，換版不會動到。
- **好接手**：固定的工具卡、維護手冊、發版檢查清單，GitLab CI 自動測試、弱點檢查、打包與 Release。

整理自實際專案的做法與踩過的坑，每個決定的原因寫在 `references/`。

## 內容

```text
SKILL.md                    給 Claude 的流程與規則
references/
  architecture.md           資料夾分工、啟動、換版、不包 exe 的原因
  windows-pitfalls.md       封鎖、換行、編碼、批次檔、Proxy 等實際踩過的坑
  security.md               本機服務、上傳、Excel 輸出的資安做法與程式片段
  governance.md             只留大架構的治理：文件、版本號、CI、例行節奏
scripts/
  new_project.py            用 template/ 建立新專案
template/                   專案骨架（Flask 本機網頁工具，含測試、CI、文件與示意圖）
```

## 安裝

- **Claude Code**：把整個資料夾放到 `~/.claude/skills/python-euc-app/`（個人）或專案的 `.claude/skills/python-euc-app/`。
- **Claude 網頁版或 App**：把資料夾壓成 ZIP，在設定的 Skills 頁面上傳。

之後跟 Claude 說「用 python-euc-app 幫我建立一個新工具」或「把這個腳本改成可以分享給同事的工具」即可。

## 不用 Claude 也能直接用

需要 Python 3.10 以上與 [uv](https://docs.astral.sh/uv/)。

```bash
python scripts/new_project.py ../report-tool --name "報表整理工具" --slug report-tool --owner "你的名字" --git
cd ../report-tool
uv run --project app pytest tests
bash run.sh            # Windows：雙擊 run.bat
```

建好的專案裡，`docs/maintain.md` 有完整的開發與發版步驟。

## 範本內建什麼

| 項目 | 位置 |
|---|---|
| 單行 `run.bat`，換版時可安全覆蓋 | `run.bat` |
| 環境建立、離線套件、換版、回滾 | `app/launcher.ps1` |
| 路徑集中管理，起始資料只放一次 | `app/<package>/paths.py` |
| 本機網頁後端：Host／Origin 檢查、安全標頭、頁面關閉後自動結束、只開一份 | `app/<package>/server.py` |
| 不記資料內容的日誌 | `app/<package>/logs.py` |
| 白名單打包、附 Windows 離線套件、CHANGELOG 檢查 | `scripts/build_release.py` |
| 換版說明的示意圖（黑白灰 SVG） | `scripts/make_manual_figures.py` |
| 測試、`uv lock --check`、`pip-audit`、Release | `.gitlab-ci.yml` |
| 工具卡、維護手冊、發版檢查清單、使用手冊、換版說明 | `OWNER.md`、`docs/` |

## 限制

- 啟動與換版流程以 Windows PowerShell 5.1 為主要目標，已在 Linux 版 PowerShell 7 測試；第一次用在新公司環境時，請在實際的 Windows 電腦上跑一次。
- 換版說明的「解除封鎖」畫面是示意圖，實際文字依 Windows 版本略有不同。
- CI 是 GitLab 格式。用 GitHub 時，把 `.gitlab-ci.yml` 的步驟改寫成 GitHub Actions 即可，打包腳本不用改。
