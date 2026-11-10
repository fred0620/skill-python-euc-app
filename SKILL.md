---
name: python-euc-app
description: 為業務端個人開發、給同事在自己電腦上用的 Python 小工具（End-User Computing）建立或改造專案架構：app / workspace / runtime 分離、run.bat 啟動與換版回滾、GitLab CI 發布、輕量治理文件。使用者要做新的業務 app、或要讓既有的 Python 腳本能安全分享與更新給同事時使用。
---

# Python EUC App 架構

給「不是 IT 部門、個人開發、不會部署到 production」的業務工具用的專案架構。目標是三件事：

1. **可攜**：同事不用裝 Python，解壓後雙擊 `run.bat` 就能用，全部在一個資料夾內。
2. **安全**：只在本機執行，資料不離開電腦；發布包可驗證、不含資料；換版失敗能退回。
3. **好接手**：別人照文件就能維護與發版，不依賴原作者。

這套架構來自實際專案（PDF 解析器）的整理，`references/` 記錄每個決定的原因與踩過的坑。

## 什麼時候用

- 使用者要做一個新的業務工具，要分享給同事在 Windows 電腦上使用。
- 使用者有一支 Python 腳本或小程式，想讓同事也能用，並且之後能更新。
- 使用者問「這種工具要怎麼發布、更新、維護」。

不適合：要部署到伺服器、多人同時連線、需要寫入公司核心系統的應用。這些應該走 IT 的正式開發流程，直接告訴使用者。

## 流程

### A. 建立新專案

1. 問清楚四件事（缺的才問）：顯示名稱、英文 slug（小寫與連字號）、負責人、這個工具處理什麼資料。
2. 執行建立腳本：

   ```bash
   python <skill 路徑>/scripts/new_project.py <目標資料夾> --name "顯示名稱" --slug my-tool --owner "負責人" --git
   ```

   會複製 `template/`、替換名稱、產生 `uv.lock`、示意圖與使用手冊 HTML。
3. 跑 `uv run --project app pytest tests`，確認骨架正常。
4. 在 `app/<package>/server.py` 的「功能」區塊加上這個工具的 API，前端改 `app/<package>/web/`。需要的套件用 `uv add --project app 套件` 加入，並加進 `__main__.py` 的 doctor 檢查。
5. 填寫標「待填」的地方：`OWNER.md`、`README.md`、`docs/design.md` 前半、`docs/user-guide.md` 第 2 節。

### B. 改造既有專案

先讀 `references/architecture.md`，再照下面順序搬，每一步都跑測試：

1. 程式移到 `app/`，`pyproject.toml`、`uv.lock`、`.python-version` 也移進去。
2. 新增 `paths.py`，把所有讀寫位置集中，使用者資料改寫到 `workspace/`。啟動程式用 `APP_HOME` 指定最外層。
3. 從 `template/` 複製 `run.bat`、`run.sh`、`app/launcher.ps1`、`app/launcher.sh`、`scripts/`、`.gitattributes`、`.gitlab-ci.yml`，替換名稱。
4. 版本號只留在 `app/pyproject.toml`，`__init__.py` 從那裡讀。
5. 舊版的使用者資料（例如放在最外層的範本）在第一次啟動時**複製**到 `workspace`，不要刪除，由使用者確認後自己刪。
6. 補上治理文件（`OWNER.md`、`CHANGELOG.md`、`docs/` 四份）。

## 一定要守的規則

- **程式和資料分開**：`app/` 每次換版整包換掉；使用者資料只能寫到 `workspace/`；`runtime/` 隨時可刪掉重建。所有路徑只在 `paths.py` 定義。
- **`run.bat` 只有一行**，以 `exit /b` 結尾。換版時會覆蓋它，多行的批次檔會讀到一半的新內容。
- **`.ps1` 存成 UTF-8 with BOM**，`.bat`、`.ps1` 用 CRLF（`.gitattributes` 已設定）。Windows PowerShell 5.1 沒有 BOM 就讀不懂中文。
- **不包成 exe**：防毒常誤判，也不能只換一部分。
- **不連網檢查更新**：同事從 GitLab Release 下載 ZIP，放進工具資料夾，雙擊 `run.bat` 安裝。換版說明附圖解，並保留手動更新與 `rollback`。
- **本機服務只綁 127.0.0.1**，保留 `server.py` 裡的 Host／Origin 檢查、安全標頭與一般化的錯誤訊息。新增 API 不要繞過它們。
- **日誌不記資料內容與檔名**，只記代號與數量。
- **發布包用白名單**：`scripts/build_release.py` 只打包列出的檔案。新增要發布的資料夾時加進清單。
- **CHANGELOG 沒寫不能發布**，打標籤時 CI 會檢查標籤和版本一致。
- **治理只留大架構**：工具卡、發版檢查清單、維護手冊。不要替使用者寫各公司不同的政策、登記流程或風險分級；寫「公司另有規定時以公司為準」。

## 文件與檔案對照

| 要做的事 | 看哪裡 |
|---|---|
| 了解每個設計決定的原因 | `references/architecture.md` |
| Windows 上會遇到的坑（封鎖、編碼、換行、Proxy） | `references/windows-pitfalls.md` |
| 本機服務、上傳、Excel 輸出的資安做法與程式片段 | `references/security.md` |
| 工具卡、檢查清單、版本號、CI 與發版節奏 | `references/governance.md` |
| 專案骨架本身 | `template/` |

## 交付前檢查

- [ ] `uv run --project app pytest tests` 全部通過
- [ ] `uv run --project app python scripts/build_release.py` 能打包，ZIP 裡只有 `run.bat`、`run.sh` 和 `app/`
- [ ] 解壓發布包後 `bash run.sh doctor` 正常（Windows 上用 `run.bat doctor`）
- [ ] 把新版 ZIP 放進解壓後的資料夾，`run.bat update` 能換版、`run.bat rollback` 能退回
- [ ] 文件裡沒有殘留的「待填」，或已告訴使用者哪些要他自己填
- [ ] 改了示意圖文字或步驟時，重跑 `scripts/make_manual_figures.py` 與 `scripts/build_manual.py`
