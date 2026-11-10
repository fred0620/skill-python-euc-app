# 資安基線

範本的 `server.py` 已經包含前四項。後面幾項依工具的功能加上。

## 1. 只在本機

- `app.run(host="127.0.0.1")`，不要綁 `0.0.0.0`。
- 擋 **DNS rebinding**：外部網域可以解析成 127.0.0.1，讓瀏覽器以為是同一個網站。所以只接受 `Host` 是 `127.0.0.1`、`localhost`、`[::1]` 的請求。
- 擋 **CSRF**：使用者瀏覽其他網站時，那個網站可以對本機服務發請求。`/api/` 拒絕 `Sec-Fetch-Site` 不是 `same-origin`／`none` 的請求，以及 `Origin` 和 `Host` 不一致的寫入請求。

## 2. 安全標頭

- `Content-Security-Policy`：`default-src 'self'`，不載入外部腳本。
- `X-Frame-Options: DENY`、`X-Content-Type-Options: nosniff`、`Referrer-Policy: no-referrer`、`Cross-Origin-Opener-Policy` 與 `Cross-Origin-Resource-Policy: same-origin`。
- API 回應 `Cache-Control: no-store`，資料不留在瀏覽器快取。

## 3. 錯誤不外洩

- 未預期的例外只回「處理時發生錯誤，詳細內容已記錄在 workspace/logs」，traceback 只寫進本機日誌。
- `/api/ping` 回傳資料夾路徑的雜湊，不回完整路徑（路徑常含使用者名稱）。

## 4. 日誌

- 只記代號（doc_id、run_id）、數量、版本；不記檔名、使用者資料、人工修正的內容。
- 需要記檔名時記雜湊。
- 外部字串寫進日誌前去掉換行與控制字元，避免偽造日誌行。
- 輪替 1 MB × 5 份，超過 30 天刪除。

## 5. 上傳檔案

```python
UNSAFE_NAME = re.compile(r'[\x00-\x1f\x7f<>:"/\\|?*]')

def safe_name(raw: str | None, limit: int = 120) -> str:
    """只保留檔名本身，去掉路徑、控制字元與 Windows 不允許的字元。"""
    name = Path((raw or "").replace("\\", "/")).name
    name = UNSAFE_NAME.sub("_", name).strip(" .")
    return name[:limit] or "file"

def looks_like_pdf(stream) -> bool:
    head = stream.read(1024)
    stream.seek(0)
    return b"%PDF-" in head          # 依檔案類型換成對應的檔頭檢查
```

- 存到 `paths.UPLOADS`，檔名前面加隨機代號，避免同名覆蓋與路徑猜測。
- 設定 `MAX_CONTENT_LENGTH`。
- 工具結束時刪除，異常結束則下次啟動時刪除。

## 6. 輸出 Excel

以 `=`、`+`、`-`、`@` 開頭的文字會被 Excel 當成公式（CSV／公式注入）。所有文字儲存格：

```python
CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

def write_text(cell, value: str) -> None:
    cell.value = CONTROL.sub("", str(value))
    cell.data_type = "s"           # openpyxl：強制當文字，不會被當成公式
    cell.number_format = "@"
```

包含檔名、錯誤訊息這些「看起來不像資料」的欄位。

## 7. 使用者輸入當作代號或檔名

```python
WINDOWS_RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}

def check_id(value: str) -> str:
    if not re.fullmatch(r"[\w\-]{1,64}", value or ""):
        raise ValueError("只能用文字、數字、底線與連字號，最多 64 個字")
    if value.lower() in WINDOWS_RESERVED:
        raise ValueError("這是 Windows 保留名稱，請換一個")
    return value
```

## 8. 套件與發布

- `uv.lock` 鎖版本；CI 跑 `uv lock --check` 與 `pip-audit`，打標籤時弱點檢查不過就不能發布。
- 讀取外部檔案（PDF、Excel、圖片）的套件最需要跟上更新。
- 選套件時看授權，避開 AGPL 這類會影響公司使用的授權。
- 下載 uv 時比對官方 SHA256；發布包用白名單打包。

## 9. 客製腳本

讓使用者執行自己的 Python 腳本（例如第三層客製處理）等於讓他執行任意程式。只從使用者自己的 `workspace` 讀取，發布包不附任何會被自動執行的腳本，文件寫清楚這件事。
