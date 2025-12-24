import streamlit as st
import pandas as pd

# Load the data you just processed
df = pd.read_csv("processed_data.csv")

st.title("🛒 Australia Grocery Price Compare")
st.write(f"Analyzing {len(df)} products from major supermarkets.")

# Search functionality
query = st.text_input("Search for a product (e.g., 牛奶 or Milk):")

if query:
    # Filter results by English or Chinese name
    results = df[df['name'].str.contains(query, case=False, na=False) | 
                 df['chinese_name'].str.contains(query, case=False, na=False)]
    
    st.dataframe(results[['chinese_name', 'name', 'current_price', 'min_price', 'price_gap']])
    
    # Simple Insight
    best_deal = results.loc[results['price_gap'].idxmin()] if not results.empty else None
    if best_deal is not None:
        st.success(f"Best Deal Found: {best_deal['name']} at ${best_deal['current_price']}")
