
# Fukuoka Instagram Insights — Inbound MVP

Local Streamlit app to explore Instagram-like posts for Fukuoka tourism with an inbound focus.

## Quickstart
```bash
# inside a new virtualenv
pip install streamlit pandas numpy matplotlib langid scikit-learn folium
streamlit run app.py
```

## Data Format
`data/posts.csv` columns:
- post_id, post_url, caption, hashtags (comma-separated), likes, comments, posted_at (ISO),
- location_name, lat, lng, lang (`en/ko/zh/ja`), content_type (`food/nature/night/culture`)

## Notes
- Sample dataset has 100 synthetic rows for demo.
- Engagement metric = `likes + 2*comments`.
- Instagram ToS: this MVP uses CSV import. Replace with permitted data sources in production.
