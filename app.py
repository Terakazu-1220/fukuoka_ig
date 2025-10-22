import pandas as pd, streamlit as st
import numpy as np
import folium
import streamlit.components.v1 as components
from datetime import datetime

st.set_page_config(page_title="Fukuoka IG Insights", layout="wide")

@st.cache_data
def load_data(path):
    df = pd.read_csv(path, parse_dates=["posted_at"])
    df["engagement"] = df["likes"] + 2*df["comments"]
    df["hashtags_list"] = df["hashtags"].fillna("").str.split(",")
    return df

df = load_data("data/posts.csv")

# ---- Language refinement (split zh into zh-cn / zh-tw)
SIMPL_CHARS = set("国门体级线风广车饭饮馆厦观爱历乐医铁龙鲜汉阳湾岛厦厦厦湾际气购麦麦当劳云宝丽丽丽馆点话线网产证飞刘刘刘")
TRAD_CHARS  = set("國門體級線風廣車飯飲館廈觀愛歷樂醫鐵龍鮮漢臺灣島臺灣際氣購麥當勞雲寶麗館點話線網產證飛劉劉劉香港臺臺臺")
TW_HINTS = ["台灣","臺灣","🇹🇼","TW","Taiwan","台北","高雄","新北","台中","台南","花蓮","桃園","嘉義","宜蘭","澎湖"]
CN_HINTS = ["中国","中國","大陆","大陸","🇨🇳","CN","Beijing","Shanghai","Shenzhen","广州","廣州","成都","重庆","重慶"]
HK_HINTS = ["香港","🇭🇰","HK","HongKong","Kowloon","九龍"]

def refine_zh_lang(text: str) -> str:
    if not text:
        return "zh"
    t = str(text)
    # direct hints first
    if any(h in t for h in TW_HINTS):
        return "zh-tw"
    if any(h in t for h in HK_HINTS):
        return "zh-tw"  # treat HK with traditional for this MVP
    if any(h in t for h in CN_HINTS):
        return "zh-cn"
    # character-based heuristic
    s_count = sum(c in SIMPL_CHARS for c in t)
    t_count = sum(c in TRAD_CHARS for c in t)
    if t_count > s_count:
        return "zh-tw"
    if s_count > t_count:
        return "zh-cn"
    return "zh"

# create lang2 (refined language)
df["lang2"] = df["lang"].astype(str)
mask_zh = df["lang2"].eq("zh")
if mask_zh.any():
    texts = (df.loc[mask_zh, "caption"].fillna("") + " " + df.loc[mask_zh, "hashtags"].fillna(""))
    df.loc[mask_zh, "lang2"] = texts.apply(refine_zh_lang)

# Default any remaining 'zh' to 'zh-cn' for tagging/filters
df.loc[df["lang2"].eq("zh"), "lang2"] = "zh-cn"

st.title("Fukuoka Instagram Insights — Inbound Focus (MVP)")
st.caption("Build: 2025-10-22  (UI v1.2) — If you don't see the new charts, click ↻ Rerun.")

# ---- Filters
st.sidebar.header("Filters")
langs = st.sidebar.multiselect("Languages", sorted(df["lang2"].dropna().unique().tolist()))
areas = st.sidebar.multiselect("Areas", sorted(df["location_name"].dropna().unique().tolist()))
ctypes = st.sidebar.multiselect("Content Types", sorted(df["content_type"].dropna().unique().tolist()))
date_from, date_to = st.sidebar.date_input(
    "Date range",
    value=[df["posted_at"].min(), df["posted_at"].max()]
)

q = df.copy()
if langs: q = q[q["lang2"].isin(langs)]
if areas: q = q[q["location_name"].isin(areas)]
if ctypes: q = q[q["content_type"].isin(ctypes)]
q = q[(q["posted_at"]>=pd.to_datetime(date_from)) & (q["posted_at"]<=pd.to_datetime(date_to))]


# ---- End Filters ----

# ---- Debug Panel
debug = st.sidebar.checkbox("Show debug info", value=False)
if debug:
    st.markdown("#### 🔧 Debug")
    st.write({
        "df_shape": df.shape,
        "q_shape": q.shape,
        "langs": sorted(df["lang2"].dropna().unique().tolist()),
        "ctypes": sorted(df["content_type"].dropna().unique().tolist()),
        "areas": sorted(df["location_name"].dropna().unique().tolist()),
    })
    st.write("Date filter:", date_from, date_to)

# ---- KPIs
col1, col2, col3 = st.columns(3)
col1.metric("Posts", f"{len(q):,}")
col2.metric("Avg Engagement", f"{q['engagement'].mean():.1f}" if len(q) else "-")
col3.metric("Unique Areas", q['location_name'].nunique())

st.markdown("### Language × Area — Avg Engagement")
if len(q):
    pivot = q.pivot_table(index="lang2", columns="location_name", values="engagement", aggfunc="mean").fillna(0).round(1)
    st.dataframe(pivot, use_container_width=True)
else:
    st.info("No data for current filters.")

st.markdown("### Top Attractions by Language")
topN = st.slider("Top N", 3, 10, 5)
if len(q):
    g = (q.groupby(["lang2","location_name"])["engagement"].mean()
           .reset_index().sort_values(["lang2","engagement"], ascending=[True, False]))
    for lg in g["lang2"].unique():
        st.subheader(f"Language: {lg}")
        sub = g[g["lang2"]==lg].head(topN)
        st.dataframe(sub, use_container_width=True)

        # Example picks (top posts URLs per area)
        picks = (q[q["lang2"]==lg]
                 .sort_values("engagement", ascending=False)[["location_name","post_url","engagement"]]
                 .dropna(subset=["post_url"]).head(5))
        with st.expander("Example posts"):
            st.dataframe(picks, use_container_width=True)

# ---- Language × Content Type — Avg Engagement (Bar)
st.markdown("### Language × Content Type — Avg Engagement (Bar)")
if len(q):
    lc = (
        q.groupby(["lang2", "content_type"])['engagement']
         .mean()
         .reset_index()
         .sort_values(["lang2", "engagement"], ascending=[True, False])
    )
    lc_pivot = lc.pivot(index="content_type", columns="lang2", values="engagement").fillna(0)
    st.bar_chart(lc_pivot)
    st.success("Rendered: Language × Content Type bar chart ✅")
else:
    st.info("No data for current filters.")

# ---- Map — Popular Areas (size = posts, color = engagement)
st.markdown("### Map — Popular Areas (size = posts, color = engagement)")
if len(q):
    agg = (
        q.groupby("location_name")
         .agg(lat=("lat", "mean"),
              lng=("lng", "mean"),
              posts=("post_id", "count"),
              engagement=("engagement", "mean"))
         .reset_index()
    )
    # Fallback center if lat/lng are missing
    center_lat = float(q["lat"].mean()) if q["lat"].notna().any() else 33.5902
    center_lng = float(q["lng"].mean()) if q["lng"].notna().any() else 130.4017
    m = folium.Map(location=[center_lat, center_lng], zoom_start=10)

    min_e, max_e = float(agg['engagement'].min()), float(agg['engagement'].max())
    def color(e):
        if max_e == min_e:
            return '#3186cc'  # default blue
        t = (e - min_e) / (max_e - min_e)
        r = int(255 * t)
        g = int(100 * (1 - t))
        b = int(204 * (1 - t))
        return f'#{r:02x}{g:02x}{b:02x}'

    max_posts = max(int(agg['posts'].max()), 1)
    for _, row in agg.iterrows():
        folium.CircleMarker(
            location=[float(row['lat']), float(row['lng'])],
            radius=6 + 8 * (float(row['posts']) / max_posts),
            color=color(float(row['engagement'])),
            fill=True,
            fill_opacity=0.7,
            popup=folium.Popup(
                f"{row['location_name']}<br>Posts: {int(row['posts'])}<br>Avg engagement: {row['engagement']:.1f}",
                max_width=250
            ),
        ).add_to(m)

    components.html(m._repr_html_(), height=480)
    st.success("Rendered: Popular Areas map ✅")
else:
    st.info("No data for current filters.")

st.markdown("### PR Suggestions (Rule-based)")
if len(q):
    # --- compute Top Area and Top Content per language
    def _slug(s: str) -> str:
        return str(s).strip().lower().replace(" ", "")

    def _lang_key(lg: str) -> str:
        if lg in ["zh", "zh-cn", "zh-tw"]:
            return "zh-cn" if lg == "zh" else lg
        root = lg.split('-')[0]
        if root in ["en","ko","ja"]:
            return root
        return lg

    # --- Language-specific tag presets
    LANG_BASE_TAGS = {
        "en": ["#fukuoka", "#japantravel", "#visitjapan"],
        "ko": ["#후쿠오카", "#후쿠오카여행", "#일본여행"],
        "zh-cn": ["#福冈", "#日本旅行", "#福冈旅行"],
        "zh-tw": ["#福岡", "#日本旅遊", "#福岡旅遊"],
        "ja": ["#福岡", "#福岡旅行"],
    }

    CONTENT_TAGS = {
        "en": {
            "food":   ["#food", "#ramen", "#streetfood"],
            "nature": ["#nature", "#beach", "#sunset"],
            "night":  ["#nightview", "#lanterns", "#nightlife"],
            "culture":["#shrine", "#temple", "#castle"],
        },
        "ko": {
            "food":   ["#맛집", "#라멘", "#야타이"],
            "nature": ["#자연", "#바다", "#노을"],
            "night":  ["#야경", "#나이트라이프", "#야타이"],
            "culture":["#신社", "#사찰", "#성곽"],
        },
        "zh-cn": {
            "food":   ["#美食", "#拉面", "#路边摊"],
            "nature": ["#自然", "#海滩", "#日落"],
            "night":  ["#夜景", "#街头小吃", "#夜生活"],
            "culture":["#神社", "#寺庙", "#城堡"],
        },
        "zh-tw": {
            "food":   ["#美食", "#拉麵", "#攤販"],
            "nature": ["#自然", "#海邊", "#日落"],
            "night":  ["#夜景", "#街頭小吃", "#夜生活"],
            "culture":["#神社", "#寺廟", "#城堡"],
        },
        "ja": {
            "food":   ["#福岡グルメ", "#博多ラーメン", "#屋台"],
            "nature": ["#糸島", "#海", "#夕日"],
            "night":  ["#中洲", "#夜景", "#提灯"],
            "culture":["#太宰府", "#神社", "#城跡"],
        },
    }

    def build_tags(lg: str, area: str, content: str, limit: int = 8) -> str:
        key = _lang_key(lg)
        base = LANG_BASE_TAGS.get(key, ["#fukuoka"])
        content_list = CONTENT_TAGS.get(key, {}).get(str(content), [])
        dynamic = []
        if pd.notna(area) and str(area).strip():
            dynamic.append(f"#{_slug(area)}")
        if pd.notna(content) and str(content).strip():
            dynamic.append(f"#{_slug(content)}")
        # de-duplicate while preserving order
        seen = set()
        ordered = []
        for t in base + dynamic + content_list:
            if t and t not in seen:
                ordered.append(t); seen.add(t)
        return " ".join(ordered[:limit])

    area_rank = (
        q.groupby(["lang2", "location_name"])['engagement']
         .mean().reset_index()
    )
    top_area = (
        area_rank.sort_values(["lang2", "engagement"], ascending=[True, False])
                 .groupby("lang2").head(1)
                 .rename(columns={"location_name": "top_area", "engagement": "top_area_eng"})
    )

    ctype_rank = (
        q.groupby(["lang2", "content_type"])['engagement']
         .mean().reset_index()
    )
    top_content = (
        ctype_rank.sort_values(["lang2", "engagement"], ascending=[True, False])
                   .groupby("lang2").head(1)
                   .rename(columns={"content_type": "top_content", "engagement": "top_content_eng"})
    )

    recs = pd.merge(top_area[["lang2", "top_area", "top_area_eng"]],
                    top_content[["lang2", "top_content", "top_content_eng"]],
                    on="lang2", how="outer")

    for _, r in recs.iterrows():
        lg = r["lang2"]
        area = r.get("top_area", "-")
        content = r.get("top_content", "-")
        tags_line = build_tags(lg, area, content, limit=8)

        st.write(f"""
**[{lg}] 推し資源**  
・**エリアTop1**：{area}  
・**コンテンツTop1**：{content}  

**推奨運用**  
・投稿時間：金/土 19–22時  
・推奨タグ：{tags_line}  
・内容例：{area} の {content} の魅力が伝わる1枚（人物＋背景）
        """)
else:
    st.info("No data for current filters.")
