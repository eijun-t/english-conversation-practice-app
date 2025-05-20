import streamlit as st
from english_conversation_practice_app.utils.csv_loader import load_conversation_csv
import random

# ページ設定
st.set_page_config(page_title="問題抽出テスト", page_icon="📝")

# タイトルとアプリの説明
st.title("1. CSV問題抽出テスト")
st.subheader("CSVからランダムに問題を抽出する機能の検証")

# テスト用のコンテナ
test_container = st.container()

with test_container:
    # CSVファイルから問題を読み込む
    try:
        csv_path = "data/business_english_mvp_3cols.csv"
        questions = load_conversation_csv(csv_path)
        st.success(f"{len(questions)}件の問題が読み込まれました！")
    except Exception as e:
        st.error(f"問題の読み込みに失敗しました: {e}")
        st.stop()

    # ランダムに選択ボタン
    if st.button("ランダムに問題を選択", type="primary"):
        if questions:
            random_question = random.choice(questions)
            st.session_state.selected_question = random_question
        else:
            st.error("問題が読み込まれていません")
    
    # 選択された問題を表示
    if "selected_question" in st.session_state:
        question = st.session_state.selected_question
        st.markdown("### 選択された問題")
        st.info(f"日本語: {question['japanese_source']}")
        st.success(f"英語: {question['english_reference']}")
        st.text(f"ID: {question['id']}")
    
    # 全問題リスト（参考用）
    with st.expander("CSVの全問題リスト"):
        for i, q in enumerate(questions):
            st.write(f"{i+1}. 日本語: {q['japanese_source']}")
            st.write(f"   英語: {q['english_reference']}")
            st.write("---")

# テスト結果
st.markdown("## テスト結果")
if "selected_question" in st.session_state:
    st.success("✅ 問題を正常に抽出できました")
    
    # テスト項目
    st.markdown("### テスト項目")
    st.markdown("- [x] CSVからのデータ読み込み")
    st.markdown("- [x] ランダムな問題抽出")
    st.markdown("- [x] 問題データの表示")
else:
    st.info("「ランダムに問題を選択」ボタンをクリックしてテストを実行してください")

# テスト手順
with st.sidebar:
    st.header("テスト手順")
    st.markdown("1. アプリ起動時にCSVデータが読み込まれることを確認")
    st.markdown("2. 「ランダムに問題を選択」ボタンをクリック")
    st.markdown("3. 選択された問題が正しく表示されることを確認")
    st.markdown("4. ボタンを複数回クリックして、異なる問題が表示されることを確認") 