# espTranslator

Skyrim mod `.esp` file translator

A Python-based tool for extracting, translating, and reassembling plugin strings from Skyrim mod files (e.g., `.esp` files). This tool applies term translations via an **Aho–Corasick automaton** and leverages the **OpenAI ChatCompletion API** to translate text asynchronously into **Traditional Chinese**. It also estimates API token usage and cost while logging minimal and grouped status messages.

---

## ✨ Features

### 🔍 **Plugin Parsing**
- Parses `.esp` files to extract text strings.
- Uses a plugin interface for structured string extraction.
- Preserves the original folder structure for output.

### 📝 **Term Replacement**
- Utilizes an **Aho–Corasick automaton** for efficient English-to-Chinese term replacement.
- **Define mappings in `dict.txt` placed in the mods root directory.**

### ⚡ **Asynchronous Translation**
- Sends translation requests in batches via **asynchronous API calls** to OpenAI.
- Configurable **batch size** and **concurrency settings**.
- **Retries failed requests** using an **exponential backoff mechanism**.

### 🔢 **Token Counting & Cost Estimation**
- Uses `tiktoken` (if installed) for accurate token counting.
- Estimates **input/output token usage** and **cost per API call**.
- **Pricing:**
  - **Input tokens:** $0.15 per 1M tokens
  - **Output tokens:** $0.6 per 1M tokens

### 📜 **Minimal & Grouped Logging**
- **Suppresses unnecessary logs** to avoid clutter.
- **Combines multiple log entries** into a single output for readability.

---

## 🔧 Installation

### 📌 **Requirements**
- **Python 3.9+**
- **OpenAI API Key** ([Get yours here](https://platform.openai.com/account/api-keys))
- **Required Python Packages:**
  - `openai`
  - `pyahocorasick`
  - `tiktoken` (**optional, for precise token counting**)
  - Other standard libraries (`asyncio`, `logging`, etc.)

### 🚀 **Setup Steps**

1. **Clone the repository (or download the files):**

   ```bash
   git clone https://github.com/yourusername/skyrim-mod-translator.git
   cd skyrim-mod-translator
   ```

2. **Install dependencies:**

   ```bash
   pip install openai pyahocorasick
   ```

3. **For accurate token counting, install `tiktoken`:**

   ```bash
   pip install tiktoken
   ```

4. **Set environment variables (API key):**

   ```bash
   export OPENAI_API_KEY="your_openai_api_key"
   ```

---

## 📂 Directory Structure

```
skyrim-mod-translator/
├── espTranslator.py       # Main asynchronous converter script
├── plugin_interface/      # Plugin parsing modules (plugin.py, plugin_string.py, etc.)
├── dict.txt               # Term mapping file (format: "EnglishPhrase ChineseTranslation")
└── README.md
```

**Mods Directory Structure:**

```
mods/
├── Subfolder1/
│   └── modName.esp
├── Subfolder2/
│   └── anotherMod.esp
└── dict.txt
```

---

## 📌 Usage

Run the script and specify the mods directory path:

```bash
python espTranslator.py <path_to_mods_directory>
```

Example:

```bash
python espTranslator.py ./mods
```

Once executed, the script will:
- Parse `.esp` files located in `mods/` subdirectories.
- Replace terms based on `dict.txt`.
- Send translation requests to OpenAI in **batches**.
- **Preserve original folder structure** while saving translated results as JSON files.

---

## 📊 Logging & Cost Estimation

### 📝 **Grouped Logs**
- **Combines log entries every 5 batches**, displaying:
  - Batch IDs
  - API call duration
  - Input/output token counts
  - Estimated cost

### 💰 **Cost Calculation**
- **Input Tokens:** $0.15 per 1M tokens
- **Output Tokens:** $0.6 per 1M tokens

### 🔇 **Log Suppression**
- **Suppresses detailed logs from OpenAI client and `urllib3`** to keep output clean.

---

## 🔮 Future Improvements

- **📌 Caching Translations:**
  - Avoid redundant API calls for repeated strings.

- **🚀 Single-Pass Extraction:**
  - Optimize plugin parsing to extract strings in a single step.

- **⚡ Parallel Processing:**
  - Utilize **multi-processing** for faster parsing of large mod files.

- **🔍 Enhanced Error Handling:**
  - Improve handling of API timeouts and rate limits.

---

## 📜 License

This tool includes code from the **SSE Auto Translator** project by Cutleast. Please review the corresponding license terms ([Attribution-NonCommercial-NoDerivatives 4.0 International](https://creativecommons.org/licenses/by-nc-nd/4.0/)) for usage and redistribution guidelines.

---

## 🤝 Contributing

Contributions and improvements are welcome! Feel free to open issues or submit pull requests with clear explanations of enhancements.
(Note: Due to licensing restrictions on parts of the code, contributions should respect the original license.)
