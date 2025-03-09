# espTranslator

Skyrim mod `.esp` 文件翻譯工具

這是一款基於 Python 的工具，可用於提取、翻譯並重新組裝 Skyrim Mod 文件（例如 `.esp`）中的文本字串。本工具透過 **Aho–Corasick 自動機** 進行詞彙替換，並利用 **OpenAI ChatCompletion API** 來非同步翻譯文本至 **繁體中文**，同時估算 API 令牌（token）使用量與成本，並提供最少且分組的日誌輸出。

---

## ✨ 功能

### 🔍 **插件解析**
- 解析 `.esp` 文件，提取文本字串。
- 使用插件接口進行字串提取。
- 保留原始文件夾結構並輸出。

### 📝 **詞彙替換**
- 使用 **Aho–Corasick 自動機** 高效替換指定的英文術語為對應的中文翻譯。
- **詞彙對應表存放於 `dict.txt`，應放置在 Mod 根目錄。**

### ⚡ **非同步翻譯**
- 透過 **非同步 API** 向 OpenAI 送出翻譯請求。
- 可自訂 **批次大小** 和 **併發請求數**。
- **自動重試** 失敗的請求，並使用 **指數回退機制（Exponential Backoff）**。

### 🔢 **Token 計算 & 成本估算**
- 可透過 `tiktoken`（若安裝）準確計算 Token 數量。
- 預測每次 API 呼叫的 **輸入 / 輸出 token** 並估算翻譯成本。
- **計價方式：**
  - **輸入 Token：** 每 100 萬個 Token **$0.15 美元**
  - **輸出 Token：** 每 100 萬個 Token **$0.6 美元**

### 📜 **最少 & 分組日誌**
- **減少不必要的輸出**，避免 OpenAI 客戶端的詳細日誌。
- **將多個日誌條目合併成單一訊息**，保持輸出簡潔。

---

## 🔧 安裝

### 📌 **環境需求**
- **Python 3.9+**
- **OpenAI API 金鑰**（[申請連結](https://platform.openai.com/account/api-keys)）
- **必要 Python 套件：**
  - `openai`
  - `pyahocorasick`
  - `tiktoken`（**可選，用於精確 Token 計算**）
  - 其他標準函式庫（`asyncio`、`logging` 等）

### 🚀 **安裝步驟**

1. **複製倉庫（或直接下載代碼）：**

   ```bash
   git clone https://github.com/yourusername/skyrim-mod-translator.git
   cd skyrim-mod-translator
   ```

2. **安裝依賴項：**

   ```bash
   pip install openai pyahocorasick
   ```

3. **如需精確 Token 計算，請額外安裝 `tiktoken`：**

   ```bash
   pip install tiktoken
   ```

4. **設定環境變數（API 金鑰）：**

   ```bash
   export OPENAI_API_KEY="your_openai_api_key"
   ```

---

## 📂 目錄結構

```
skyrim-mod-translator/
├── espTranslator.py       # 主要的非同步轉換腳本
├── plugin_interface/      # 包含插件解析模組（plugin.py, plugin_string.py 等）
├── dict.txt               # 詞彙對應表（格式："英文詞彙 中文翻譯"）
└── README.md
```

**Mod 目錄結構：**

```
mods/
├── Subfolder1/
│   └── modName.esp
├── Subfolder2/
│   └── anotherMod.esp
└── dict.txt
```

---

## 📌 使用方式

執行腳本並指定 Mod 目錄路徑：

```bash
python espTranslator.py <path_to_mods_directory>
```

示例：

```bash
python espTranslator.py ./mods
```

執行後，腳本將：
- 解析 `mods/` 目錄內的 `.esp` 文件。
- 根據 `dict.txt` 進行詞彙替換。
- 以 **批次方式** 送出 OpenAI 翻譯請求。
- **保留原始目錄結構**，將翻譯結果儲存為 JSON 檔案。

---

## 📊 記錄與成本估算

### 📝 **分組日誌**
- **每 5 個批次合併一次日誌輸出**，內容包括：
  - 批次 ID
  - API 請求時間
  - Token 使用量（輸入 / 輸出）
  - 預估成本

### 💰 **成本計算**
- **輸入 Token：** 每 100 萬個 Token **$0.15 美元**
- **輸出 Token：** 每 100 萬個 Token **$0.6 美元**

### 🔇 **日誌過濾**
- **自動抑制 OpenAI 客戶端及 `urllib3` 詳細日誌**，保持輸出清晰。

---

## 🔮 未來改進

- **📌 快取翻譯結果：**
  - 避免重複字串的 API 呼叫，減少開銷。

- **🚀 單次解析：**
  - 優化插件解析流程，合併字串提取步驟，提高效能。

- **⚡ 多進程處理：**
  - 引入 **多進程** 加速解析大量 Mod 文件。

- **🔍 更強大的錯誤處理：**
  - 強化 API 超時與速率限制的應對策略。

---

## 📜 授權協議

本工具包含 **Cutleast** 開發的 `SSE Auto Translator` 代碼，請參閱其原始授權條款（[Attribution-NonCommercial-NoDerivatives 4.0 International](https://creativecommons.org/licenses/by-nc-nd/4.0/)）以確保合法使用與再發佈。

---

## 🤝 貢獻方式

歡迎提交 **問題回報** 或 **Pull Requests** 來改進此工具！
請注意，由於部分代碼受原始授權條款限制，請確保您的貢獻符合該授權要求。
