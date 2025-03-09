import json
import logging
import sys
import os
import time
import re
import asyncio
from pathlib import Path
from copy import copy

import openai  # pip install openai
import ahocorasick  # pip install pyahocorasick

# --- SUPPRESS OPENAI/urllib3 LOGS ---
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Attempt to import tiktoken for accurate token counting; if unavailable, fallback to a simple estimate.
try:
    import tiktoken
    tokenizer = tiktoken.encoding_for_model("gpt-4o-mini")
except Exception:
    tokenizer = None

def count_tokens(text: str) -> int:
    """
    Estimate token count for a given text.
    Uses tiktoken if available; otherwise falls back to splitting on whitespace.
    """
    if tokenizer is not None:
        return len(tokenizer.encode(text))
    else:
        return len(text.split())

# Setup logger.
log_fmt = "[%(asctime)s.%(msecs)03d][%(levelname)s]: %(message)s"
root_logger = logging.getLogger()
root_logger.setLevel("INFO")  # Less verbose logging
formatter = logging.Formatter(log_fmt, datefmt="%d.%m.%Y %H:%M:%S")
log_handler = logging.StreamHandler(sys.stdout)
log_handler.setFormatter(formatter)
root_logger.addHandler(log_handler)
log = logging.getLogger("Converter")

# Set API key.
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    log.error("OPENAI_API_KEY environment variable is not set.")
    sys.exit(1)

def load_term_mapping(mods_root: Path) -> dict[str, str]:
    mapping = {}
    mapping_file = mods_root / "dict.txt"
    if not mapping_file.exists():
        log.warning(f"No dict.txt found in {mods_root}. No basic term replacements will be applied.")
        return mapping

    with mapping_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.rsplit(maxsplit=1)
            if len(parts) < 2:
                continue
            english = parts[0].strip()
            chinese = parts[1].strip()
            mapping[english] = chinese
    log.info(f"Loaded {len(mapping)} term translations from {mapping_file}.")
    return mapping

def build_automaton(mapping: dict[str, str]) -> ahocorasick.Automaton:
    automaton = ahocorasick.Automaton()
    for eng, chi in mapping.items():
        automaton.add_word(eng.lower(), (eng, chi))
    automaton.make_automaton()
    return automaton

def apply_term_replacements(text: str, automaton: ahocorasick.Automaton) -> str:
    lower_text = text.lower()
    matches = []
    for end_index, (orig_key, chi) in automaton.iter(lower_text):
        start_index = end_index - len(orig_key) + 1
        # Boundary-check logic: only replace standalone words
        if (start_index == 0 or not lower_text[start_index - 1].isalnum()) and \
           (end_index + 1 == len(lower_text) or not lower_text[end_index + 1].isalnum()):
            matches.append((start_index, end_index + 1, orig_key, chi))
    # Sort matches to handle overlapping segments
    matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))

    selected = []
    last_end = 0
    for start, end, orig_key, chi in matches:
        if start >= last_end:
            selected.append((start, end, orig_key, chi))
            last_end = end

    result = []
    last_index = 0
    for start, end, orig_key, chi in selected:
        result.append(text[last_index:start])
        result.append(chi)
        last_index = end
    result.append(text[last_index:])
    return "".join(result)

# --- LOG BUFFER CHANGES ---
LOG_BUFFER = []
LOG_BUFFER_SIZE = 5
LOG_LOCK = asyncio.Lock()

async def buffer_log_message(batch_index, attempt, duration, input_tokens, output_tokens, cost):
    """
    Buffers log messages. Once 5 messages accumulate, logs them as a single line.

    NOTE: This is just a demonstration. We assume it makes sense to combine all
    these calls into one line, even if each call had different durations/tokens/cost.
    In reality, you might want to store them separately or do an average/sum.
    """
    async with LOG_LOCK:
        # For simplicity, store everything but we only display one set of numeric stats.
        LOG_BUFFER.append((batch_index, attempt, duration, input_tokens, output_tokens, cost))

        if len(LOG_BUFFER) == LOG_BUFFER_SIZE:
            # Combine all batch indices in one line, and just use the stats from the first item.
            first_attempt = LOG_BUFFER[0][1]
            first_duration = LOG_BUFFER[0][2]
            first_input_tokens = LOG_BUFFER[0][3]
            first_output_tokens = LOG_BUFFER[0][4]
            first_cost = LOG_BUFFER[0][5]

            batch_ids = [str(item[0]) for item in LOG_BUFFER]
            combined_ids = ", ".join(batch_ids)

            log.info(
                f"Batch {combined_ids} attempt {first_attempt}: "
                f"API call took {first_duration:.2f}s, "
                f"input tokens: {first_input_tokens}, "
                f"output tokens: {first_output_tokens}, "
                f"cost: ${first_cost:.6f}"
            )

            LOG_BUFFER.clear()

async def async_translate_chunk(batch_index: int, chunk: list[str], max_retries: int = 3, delay: float = 1.0) -> tuple[int, list[str]]:
    for attempt in range(1, max_retries + 1):
        lines_prompt = "\n".join(f"{i + 1}. {txt}" for i, txt in enumerate(chunk))
        user_content = (
            "You are a professional translator specialized in Traditional Chinese. "
            "Translate the following numbered lines from English to Traditional Chinese. "
            "Output ONLY a valid JSON array of strings with the translations corresponding to each input line in order. "
            "Do not include any additional text, code fences, or formatting. "
            f"The input contains {len(chunk)} lines:\n{lines_prompt}\n"
            "Provide your answer as a JSON array exactly in this format:\n"
            "[\"translation for line 1\", \"translation for line 2\", ...]"
        )

        # Count input tokens.
        input_tokens = count_tokens(user_content)

        try:
            start_api = time.perf_counter()
            response = await openai.ChatCompletion.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful translation assistant."},
                    {"role": "user", "content": user_content},
                ],
                temperature=0,
            )
            end_api = time.perf_counter()
            duration = end_api - start_api

            response_text = response["choices"][0]["message"]["content"].strip()
            # Count output tokens.
            output_tokens = count_tokens(response_text)
            cost = (input_tokens / 1_000_000 * 0.15) + (output_tokens / 1_000_000 * 0.6)

            # Instead of logging here individually, push to the log buffer.
            await buffer_log_message(batch_index, attempt, duration, input_tokens, output_tokens, cost)

            if not response_text:
                raise ValueError("Empty response text")

            translations = json.loads(response_text)
            if not isinstance(translations, list) or len(translations) != len(chunk):
                # We'll produce a short warning, but not the same big line.
                log.warning(
                    f"Batch {batch_index} attempt {attempt}: "
                    f"Expected {len(chunk)} translations, got {len(translations) if isinstance(translations, list) else 'invalid output'}. Retrying..."
                )
                await asyncio.sleep(delay)
                continue
            return batch_index, translations
        except Exception as e:
            log.error(f"Batch {batch_index} attempt {attempt}: Error during translation: {e}")
            await asyncio.sleep(delay)
    log.error(f"Batch {batch_index}: Failed after {max_retries} attempts. Using original texts as fallback.")
    return batch_index, chunk

async def async_translate_in_batches(strings_to_translate: list[str], batch_size: int = 10, max_workers: int = 64) -> list[str]:
    batches = [(i, strings_to_translate[i : i + batch_size]) for i in range(0, len(strings_to_translate), batch_size)]
    log.info(f"Total async batches to process: {len(batches)}")
    tasks = [async_translate_chunk(batch_index, chunk) for batch_index, chunk in batches]
    results = await asyncio.gather(*tasks)
    # Sort results by batch index to preserve original order
    results.sort(key=lambda x: x[0])
    final_translations = []
    for _, translations in results:
        final_translations.extend(translations)
    return final_translations

async def async_process_plugin_file(plugin_path: Path, output_path: Path, term_automaton: ahocorasick.Automaton) -> None:
    file_start = time.perf_counter()
    log.info(f"Processing {plugin_path}...")
    try:
        from plugin_interface import Plugin  # import local plugin interface
        plugin = Plugin(plugin_path)
    except Exception as e:
        log.error(f"Error loading plugin {plugin_path}: {e}")
        return

    try:
        extracted_strings = plugin.extract_strings()
    except Exception as e:
        log.error(f"Error extracting strings from {plugin_path}: {e}")
        return

    if not extracted_strings:
        log.info(f"No strings found in {plugin_path}. Skipping.")
        return

    log.info(f"Extracted {len(extracted_strings)} strings from {plugin_path}.")
    texts_to_translate = []
    for s in extracted_strings:
        text = (s.translated_string if s.translated_string else s.original_string) or ""
        text = apply_term_replacements(text, term_automaton)
        texts_to_translate.append(text)
    
    log.info("Starting async batch translation...")
    translations = await async_translate_in_batches(texts_to_translate, batch_size=10, max_workers=64)

    processed_strings = []
    for s, translated_text in zip(extracted_strings, translations):
        new_s = copy(s)
        # Force replacement of "Knows" if missed, then remove all whitespace.
        translated_text = translated_text.replace("Knows", "知道")
        translated_text = re.sub(r"\s+", "", translated_text)
        
        new_s.translated_string = translated_text
        new_s.status = new_s.Status.TranslationComplete
        processed_strings.append(new_s)

    string_data = [s.to_string_data() for s in processed_strings]
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf8") as f:
            json.dump(string_data, f, ensure_ascii=False, indent=4)
        log.info(f"Written {len(processed_strings)} string(s) to {output_path}")
    except Exception as e:
        log.error(f"Error writing to {output_path}: {e}")
    
    file_end = time.perf_counter()
    log.info(f"Processing of {plugin_path} completed in {file_end - file_start:.2f} seconds.")

async def async_main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python converter.py <path_to_mods_directory>")
        sys.exit(1)

    mods_root = Path(sys.argv[1])
    if not mods_root.is_dir():
        log.error(f"Provided path {mods_root!r} is not a valid directory.")
        sys.exit(1)

    term_mapping = load_term_mapping(mods_root)
    term_automaton = build_automaton(term_mapping)
    output_root = Path("Output")

    # Gather all .esp files in immediate subdirectories.
    esp_files = []
    for subfolder in mods_root.iterdir():
        if subfolder.is_dir():
            esp_files.extend(list(subfolder.glob("*.esp")))

    if not esp_files:
        log.warning("No .esp files found in the immediate subfolders of the provided directory.")
        sys.exit(0)

    total_start = time.perf_counter()
    tasks = []
    for esp_file in esp_files:
        relative_path = esp_file.relative_to(mods_root)
        output_file = output_root / relative_path.parent / f"{esp_file.stem}_output{esp_file.suffix}.json"
        tasks.append(async_process_plugin_file(esp_file, output_file, term_automaton))
    await asyncio.gather(*tasks)
    total_end = time.perf_counter()
    log.info(f"Total processing time for all files: {total_end - total_start:.2f} seconds.")

if __name__ == "__main__":
    asyncio.run(async_main())
