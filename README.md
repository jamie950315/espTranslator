# espTranslator
Skyrim mod .esp file translator
A Python-based tool for extracting, translating, and reassembling plugin strings from Skyrim mod files (e.g. `.esp` files). This tool applies term translations via an Aho–Corasick automaton and leverages the OpenAI ChatCompletion API to translate text asynchronously into Traditional Chinese. It also estimates API token usage and cost while logging minimal and grouped status messages.

---

## Features

- **Plugin Parsing**:  
  Parses `.esp` files from the provided mods directory, extracts text strings using a plugin interface, and preserves folder structure for output.

- **Term Replacement**:  
  Uses an Aho–Corasick automaton to efficiently replace specified English terms with their corresponding Chinese translations.  
  *(Define mappings in `dict.txt` located in your mods root.)*

- **Asynchronous Translation**:  
  Sends translation requests in batches via asynchronous API calls to OpenAI.  
  - Configurable batch size and concurrency settings.
  - Retries failed requests with exponential backoff.

- **Token Counting & Cost Estimation**:  
  Incorporates token counting (via `tiktoken` if available) to estimate the number of input and output tokens and calculate the approximate cost of each API call.
  - Uses cost rates of USD 0.15 per 1M input tokens and USD 0.6 per 1M output tokens.

- **Minimal and Grouped Logging**:  
  Suppresses verbose logging from the OpenAI client and groups multiple log entries into a single combined message for a cleaner output.

---

## Installation

### Prerequisites

- **Python 3.9+**  
- An [OpenAI API key](https://platform.openai.com/account/api-keys)  
- Required Python packages:
  - `openai`
  - `pyahocorasick`
  - Optionally, `tiktoken` (for accurate token counting)
  - Other standard libraries (`asyncio`, `logging`, etc.)

### Setup

1. **Clone the Repository** (or copy the code files):

   ```bash
   git clone https://github.com/yourusername/skyrim-mod-translator.git
   cd skyrim-mod-translator
   ```
2. **Install Dependencies:**

  ```bash
    pip install openai pyahocorasick
  ```
3. **If you want to use accurate token counting, install:**

  ```bash
    pip install tiktoken
  ```
4. **Set Environment Variables:**
    Ensure your OpenAI API key is set:

  ```bash
    export OPENAI_API_KEY="your_openai_api_key"
  ```
---

##Directory Structure
```python
skyrim-mod-translator/
├── espTranslator.py          # Main asynchronous converter script.
├── plugin_interface/     # Contains plugin parsing modules (plugin.py, plugin_string.py, etc.)
├── dict.txt              # Term mapping file (format: "EnglishPhrase ChineseTranslation").
└── README.md
```
- Mods Directory Structure:
  Your mod files should be organized as follows:
  ```css
  mods/
  ├── Subfolder1/
  │   └── modName.esp
  ├── Subfolder2/
  │   └── anotherMod.esp
  └── dict.txt
  ```

---
##Usage
Run the converter script by specifying the path to your mods directory:
```bash
python espTranslator.py <path_to_mods_directory>
```
For example:
```bash
python espTranslator.py ./mods
```
The script will:
- Parse each .esp file in the subdirectories of the provided mods folder.
- Apply term replacements based on dict.txt.
- Send translation requests to OpenAI in batches.
- Save the translated output as JSON files in an Output folder, preserving the relative subfolder structure.

---

##
Logging and Cost Estimation
- Grouped Logs:
  Log messages for translation batches are combined into a single log entry every 5 batches. This log shows:
  - Combined batch IDs.
  - API call duration.
  - Input/output token counts.
  - Estimated cost per call.
- Cost Calculation:
  Costs are estimated using the following rates:
  - Input Tokens: USD 0.15 per 1M tokens.
  - Output Tokens: USD 0.6 per 1M tokens.
- Log Suppression:
  Verbose logs from the OpenAI client and `urllib3` are suppressed to keep the output clean.

---

##Future Improvements
- Caching Translations:
  Implement caching to avoid redundant API calls for repeated strings.
- Single-Pass Extraction:
  Optimize plugin parsing to extract strings in a single pass rather than a two-step process.
- Parallel Processing:
  Leverage multi-processing for even faster parsing of large numbers of mod files.
- Enhanced Error Handling:
  Further refine error handling and retries to improve robustness against API timeouts or rate limits.

---

##License
This tool includes code from the SSE Auto Translator project by Cutleast. Please review the corresponding license terms (Attribution-NonCommercial-NoDerivatives 4.0 International) for usage and redistribution guidelines.

---

##Contributing
Contributions and improvements are welcome. Please open issues or submit pull requests with clear explanations of the enhancements.
(Note: Due to licensing restrictions on parts of the code, contributions should respect the original license.)





















