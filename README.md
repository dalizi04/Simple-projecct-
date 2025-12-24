🛒 AussiePrice Scout: Australian Grocery Price Tracker
This project is a personal data science tool designed to combat inflation by providing a transparent, bilingual price comparison across major Australian supermarkets (Coles, Woolworths, and Aldi).

🙏 Acknowledgements & Credits
This project would not be possible without the incredible work of the Grocermatic team.

Data Source: Raw pricing data is sourced from the Grocermatic GitHub Repository.

Credit: I am deeply grateful for their commitment to making Australian grocery data open and accessible. This project serves as a personalized analytical layer built on top of their robust data collection.

🔍 Methodology & Data Challenges
As part of the development process, I implemented custom data cleaning logic to handle inconsistencies across different retail chains:

Unit Price Normalization: To solve the issue of comparing different package sizes (e.g., $7.50 for 1.5kg vs. $0.72 for 160g), I developed a logic to calculate the Price per Unit (kg/L).

Weight Extraction Logic: * For Coles, my script utilizes a custom Regex parser to extract weight information directly from product URLs (e.g., parsing -400g- from the link).

For Woolworths (WWS), where URLs do not contain weight strings, the system falls back to the quantity metadata provided in the JSON.

Translation Engine: To serve the local community, I built a batch-processing translation pipeline with a local JSON caching mechanism to handle 24,000+ items efficiently without exceeding API rate limits.

📂 Project Structure
1.py: The main data processing, cleaning, and translation pipeline.

app.py: The Streamlit-based web interface for real-time price searching and comparison.

translation_cache.json: Local dictionary to optimize translation speed.

processed_data.csv: The final cleaned and normalized dataset.
