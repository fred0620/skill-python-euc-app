# Windows 上會遇到的坑

都是實際踩過的。改啟動程式或打包流程前先看一遍。

## 從瀏覽器下載的檔案被封鎖（Mark of the Web）

- 瀏覽器和 email 下載的檔案會帶「來自網路」的標記；用檔案總管解壓時，裡面每個檔案都會繼承。
- 結果：雙擊 `run.bat` 跳安全性警告或沒有反應；PowerShell 在 `RemoteSigned` 原則下拒絕執行沒簽章的腳本。
- `git clone` 不會加標記，所以常出現「clone 可以跑，下載 ZIP 不行」。
- 做法：
  - 第一次安裝：換版說明教使用者解壓前「右鍵 > 內容 > 勾選解除封鎖」，附圖解，並寫明只對公司 GitLab 的檔案這樣做。
  - 之後的換版：由 `launcher.ps1` 用 `Expand-Archive` 解壓，不會產生這個問題。
  - 公司要求簽章時，請 IT 簽，不要教使用者改執行原則。

## 換行字元

- 用 LF 換行的 `.bat` 會出現 `goto`、標籤錯亂之類的怪錯誤。
- `.gitattributes` 固定 `*.bat`、`*.ps1` 用 CRLF，`*.sh` 用 LF；`* text=auto` 要放在最前面，後面的規則才會覆蓋它。
- 打包腳本也會再轉一次，不依賴打包那台電腦的 Git 設定。

## 編碼

- Windows PowerShell 5.1 讀沒有 BOM 的 UTF-8 腳本會把中文變亂碼，甚至語法錯誤。`.ps1` 一律存成 **UTF-8 with BOM**。
- 用程式改 `.ps1` 時，讀取用 `utf-8-sig`，寫回時把 BOM 加回去。
- `run.bat` 只放 ASCII，cmd 的編碼依系統語系而定。
- 啟動程式設定 `[Console]::OutputEncoding = UTF8`、`PYTHONUTF8=1`、`PYTHONIOENCODING=utf-8`。

## 批次檔被覆蓋時

- cmd 執行批次檔是一行一行從檔案讀，執行完一行才讀下一行。執行中途檔案被換掉，會從原本的位置讀新檔案的內容。
- 所以 `run.bat` 只有一行，以 `& exit /b` 結尾：整行在執行前已經讀完，結束後直接離開，不會再讀檔。
- `exit /b` 不帶數字，保留 PowerShell 的結束代碼，指令列模式才能被排程判斷成功或失敗。

## PowerShell 函式的回傳值

- PowerShell 函式會把「所有沒被接住的輸出」一起回傳。`Expand-Archive` 等指令有時會輸出物件（例如載入的 assembly），讓 `return $false` 變成陣列，`if` 判斷就變成真。
- 做法：可能有輸出的指令接 `| Out-Null`；判斷時寫 `(Update-App) -eq $true`。

## 改名資料夾失敗

- 防毒軟體或檔案總管會短暫鎖住剛解壓的資料夾，`Rename-Item` 偶爾失敗。
- 做法：重試幾次，每次等一秒；最後還是失敗就換回原狀並告訴使用者。
- 換版前先 `Set-Location` 到最外層，不要停在 `app/` 裡面，否則無法改名。

## 公司網路

- HTTPS 被公司攔截檢查：uv 設 `UV_SYSTEM_CERTS=1` 用 Windows 憑證。
- 擋 GitHub 或 PyPI：套件隨發布包附上；uv 和 Python 用「在能連網的電腦先跑一次，再複製資料夾」的離線安裝。
- 有 `HTTP_PROXY` 時，Python 連 127.0.0.1 也會走 Proxy 而失敗，本機檢查要明確關掉 Proxy。

## venv 不能搬家

- venv 記錄了絕對路徑，整個工具資料夾搬到別處後就壞了。
- 啟動程式先跑一次 `python -c pass`，失敗就刪掉 `runtime/venv` 重建。

## Windows 保留名稱

- `CON`、`PRN`、`AUX`、`NUL`、`COM1`–`COM9`、`LPT1`–`LPT9` 不能當檔名（不分大小寫、加副檔名也不行）。
- 使用者輸入會變成檔名時（範本代號、匯出檔名），要排除這些名稱和 `<>:"/\|?*`、控制字元。
