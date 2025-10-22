
# 🗾 Fukuoka IG Insights  
**「福岡 × インバウンド × Instagram 分析」**  
言語・地域別の外国人向け観光マーケティング最適化システム  

---

## 🎯 プロジェクト概要
近年、福岡県では訪日外国人観光客が増加しており、特に **食・街歩き・文化体験** が人気です。  
しかし、国や地域ごとに「刺さる観光資源」は異なり、汎用的な情報発信では効果的なプロモーションが難しいという課題があります。  

本プロジェクトでは、  
> **Instagram投稿データ**を分析し、  
> **言語・地域別に人気の観光資源を特定**し、  
> **各言語向けの最適なPRタグを提案する**  
システムを開発しました。  

---

## 🧭 システム構成と流れ

1. **データ入力**
   - CSV形式のInstagram投稿データ（例：`posts.csv`）を読み込み

2. **分析処理**
   - 言語別・コンテンツ別の平均エンゲージメントを算出  
   - エリア別人気投稿を地図（folium）で可視化  
   - 言語ごとに最適なPRタグを提案  

3. **出力・UI**
   - StreamlitによるWebアプリ形式  
   - 言語を選択すると結果が即時反映  

---

## 📊 主な分析機能

- **Language × Content Type — Avg Engagement**  
  言語ごとに、どの投稿ジャンルが人気かを可視化  

- **Map — Popular Areas**  
  投稿数とエンゲージメントをもとに人気エリアを地図上に表示  

- **PR Suggestions**  
  各言語（KR / EN / zh-cn / zh-tw）ごとに、人気エリアとジャンルから自動タグを提案  

📸 *アプリ画面のキャプチャをここに挿入予定*  

---

## ⚙️ 使用技術

- **プログラミング言語**：Python 3.12  
- **フレームワーク**：Streamlit  
- **データ処理**：pandas, numpy  
- **言語判定**：langid  
- **可視化**：matplotlib, folium  
- **分析モデル（拡張予定）**：scikit-learn  

---

## 🧩 データ仕様（`data/posts.csv`）

このCSVファイルは、Instagram投稿データを分析するためのサンプルです。  
主なカラムと内容は以下の通りです。

- **`id`**：投稿を一意に識別するID  
- **`caption`**：投稿本文（テキスト内容）  
- **`likes`**：いいね数（エンゲージメント指標）  
- **`language`**：投稿の言語（`langid`で自動判定）  
- **`area`**：投稿エリア（例：Hakata、Tenjin、Dazaifu など）  
- **`content_type`**：投稿カテゴリ（例：Food、Culture、Nature など）  

💡 *今後の拡張では、投稿日時・画像特徴量（例：食べ物／風景分類）を追加予定。*

---

## 🚀 実行方法（ローカル実行）

```bash
# 仮想環境を作成
python3 -m venv .venv
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate    # Windows

# 依存ライブラリをインストール
pip install -r requirements.txt

# アプリ起動
streamlit run app.py
