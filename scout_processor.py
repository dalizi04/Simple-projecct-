import requests
import pandas as pd
import os
import re
import json
import time
import gc
from deep_translator import GoogleTranslator

# --- Config ---
DATA_URL = "https://product.grocermatic.org/cleanProductInfo.json"
SAVE_PATH = "scout_results.csv"
CACHE_FILE = "translation_cache.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def extract_weight_pro(name, url, json_qty):
    search_text = f"{str(name)} {str(url)}".lower()
    match = re.search(r'(\d+\.?\d*)\s*(kg|g|l|ml)\b', search_text)
    if match:
        val = float(match.group(1))
        unit = match.group(2)
        if unit in ['g', 'ml']: return val / 1000
        return val
    return json_qty if (json_qty and json_qty > 0) else 1

def process_row(row):
    history = row.get('history', [])
    weight = extract_weight_pro(row.get('name'), row.get('url'), row.get('quantity'))
    if not isinstance(history, list) or not history:
        return pd.Series([None, None, None, None, None])
    valid = [h for h in history if 'price' in h and 'daySinceEpoch' in h]
    if not valid: return pd.Series([None, None, None, None, None])
    latest = max(valid, key=lambda x: x['daySinceEpoch'])
    curr_p = latest['price']
    all_p = [h['price'] for h in valid]
    unit_p = round(curr_p / weight, 2)
    min_p = min(all_p)
    max_p = max(all_p)
    gap = round(curr_p - min_p, 2)
    return pd.Series([curr_p, unit_p, min_p, max_p, gap])

def translate_batch(names, translator):
    if not names: return {}
    combined = " ||| ".join(names)
    try:
        translated = translator.translate(combined)
        results = [t.strip() for t in translated.split("|||")]
        if len(results) == len(names): return dict(zip(names, results))
    except: pass
    return {}

def main():
    print("--- Step 1: Fetching Raw Data ---")
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        resp = requests.get(DATA_URL, headers=headers, timeout=30)
        df = pd.DataFrame(resp.json())
    except Exception as e:
        print(f"Failed: {e}"); return

    print("--- Step 2: Advanced Analysis ---")
    df[['price', 'unit_price', 'min_p', 'max_p', 'gap']] = df.apply(process_row, axis=1)
    df = df.drop(columns=['history'])
    gc.collect()

    print("--- Step 3: Translation ---")
    cache = load_cache()
    translator = GoogleTranslator(source='en', target='zh-CN')
    to_translate = [n for n in df['name'].unique() if n not in cache]
    batch_size, limit, processed = 15, 30000, 0
    for i in range(0, len(to_translate), batch_size):
        if processed >= limit: break
        batch = to_translate[i : i + batch_size]
        print(f"Batch {i//batch_size + 1}...")
        res = translate_batch(batch, translator)
        if res:
            cache.update(res)
            processed += len(res)
            save_cache(cache)
        time.sleep(0.5)

    df['chinese_name'] = df['name'].map(cache).fillna(df['name'])

    print("--- Step 4: Exporting ---")
    # 【关键更新】这里保留了 url 列
    cols = ['chinese_name', 'name', 'unit_price', 'price', 'min_p', 'max_p', 'gap', 'url']
    df[cols].to_csv(SAVE_PATH, index=False, encoding='utf-8-sig')
    print(f"Success! Data saved to {SAVE_PATH}")

if __name__ == "__main__":
    main()
