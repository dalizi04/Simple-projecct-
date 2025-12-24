import requests
import pandas as pd
import os
import re
import json
import time
import gc
from deep_translator import GoogleTranslator

# --- Configuration ---
DATA_URL = "https://product.grocermatic.org/cleanProductInfo.json"
SAVE_PATH = "processed_data.csv"
CACHE_FILE = "translation_cache.json"

# --- Utils ---
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def create_slug(name):
    if not name: return "unknown"
    return "-".join(re.findall(r'[a-z0-9]+', str(name).lower()))

# --- Core Logic ---
def extract_prices(history_list):
    """Finds latest price by daySinceEpoch and calculates stats."""
    if not isinstance(history_list, list) or not history_list:
        return pd.Series([None, None, None, None])
    
    # Filter valid records
    valid = [h for h in history_list if 'price' in h and 'daySinceEpoch' in h]
    if not valid: return pd.Series([None, None, None, None])
    
    # Get latest entry
    latest = max(valid, key=lambda x: x['daySinceEpoch'])
    curr_p = latest['price']
    
    all_p = [h['price'] for h in valid]
    min_p = min(all_p)
    max_p = max(all_p)
    gap = round(curr_p - min_p, 2)
    
    return pd.Series([curr_p, min_p, max_p, gap])

def translate_batch(names, translator):
    """Speeds up translation by joining names with a separator."""
    if not names: return {}
    combined = " ||| ".join(names)
    try:
        translated = translator.translate(combined)
        results = [t.strip() for t in translated.split("|||")]
        if len(results) == len(names):
            return dict(zip(names, results))
    except:
        pass
    return {}

# --- Main Pipeline ---
def main():
    print("Step 1: Fetching data from remote source...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        resp = requests.get(DATA_URL, headers=headers, timeout=20)
        data = resp.json()
    except Exception as e:
        print(f"Fetch failed: {e}")
        return

    # Convert to DataFrame
    df = pd.DataFrame(data)
    del data # Free memory
    
    print("Step 2: Extracting prices and cleaning memory...")
    # Apply extraction
    df[['current_price', 'min_price', 'max_price', 'price_gap']] = df['history'].apply(extract_prices)
    
    # Memory Management: Drop large 'history' column immediately
    df = df.drop(columns=['history'])
    gc.collect() 

    print("Step 3: Translating unique products with cache...")
    cache = load_cache()
    translator = GoogleTranslator(source='en', target='zh-CN')
    
    all_names = df['name'].unique()
    to_translate = [n for n in all_names if n not in cache]
    
    print(f"Items to translate: {len(to_translate)}")

    # Batch process to save time and avoid IP ban
    batch_size = 20
    # You can increase limit to 2000 or more if system is stable
    limit = 30000
    processed_count = 0

    for i in range(0, len(to_translate), batch_size):
        if processed_count >= limit:
            print(f"Reached session limit ({limit}). Saving...")
            break
            
        batch = to_translate[i : i + batch_size]
        print(f"Processing batch {i//batch_size + 1}...")
        
        results = translate_batch(batch, translator)
        if results:
            cache.update(results)
            processed_count += len(results)
            save_cache(cache)
        
        # Cooling down to prevent overheating and IP ban
        time.sleep(1)

    # Apply translations
    df['chinese_name'] = df['name'].map(cache).fillna(df['name'])

    print("Step 4: Exporting results...")
    cols = ['chinese_name', 'name', 'current_price', 'min_price', 'max_price', 'price_gap']
    df[cols].to_csv(SAVE_PATH, index=False, encoding='utf-8-sig')
    
    print(f"Process complete. File saved to {SAVE_PATH}")
    print(df[cols].head())

if __name__ == "__main__":
    main()