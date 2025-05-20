import streamlit as st
from english_conversation_practice_app.components.tts import play_text, text_to_speech

# ページ設定
st.set_page_config(page_title="音声読み上げテスト", page_icon="🔊")

# タイトルとアプリの説明
st.title("4. テキスト読み上げテスト")
st.subheader("テキストを音声に変換する機能の検証")

# テスト用のコンテナ
test_container = st.container()

with test_container:
    st.markdown("## 1. テキスト入力")
    
    # サンプルテキスト
    sample_texts = [
        "Hello, nice to meet you.",
        "Thank you for your cooperation.",
        "I will send the proposal tomorrow.",
        "Let's start the meeting now.",
        "Please introduce yourself."
    ]
    
    text_method = st.radio(
        "テキスト入力方法を選択",
        options=["サンプルテキストから選択", "直接入力"]
    )
    
    if text_method == "サンプルテキストから選択":
        text_index = st.selectbox(
            "読み上げるテキストを選択してください",
            options=range(len(sample_texts)),
            format_func=lambda i: sample_texts[i]
        )
        selected_text = sample_texts[text_index]
    else:
        selected_text = st.text_input(
            "読み上げるテキストを入力してください", 
            value="Hello, this is a test for text to speech function."
        )
    
    st.info(f"選択したテキスト: {selected_text}")
    
    st.markdown("## 2. 読み上げ言語選択")
    language = st.selectbox(
        "言語を選択してください",
        options=["英語", "日本語"],
        index=0
    )
    
    lang_code = "en" if language == "英語" else "ja"
    
    st.markdown("## 3. 読み上げ速度")
    slow_mode = st.checkbox("ゆっくり読み上げる", value=False)
    
    st.markdown("## 4. 読み上げテスト実行")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("通常読み上げ", type="primary"):
            with st.spinner("音声を生成中..."):
                success = play_text(selected_text, lang=lang_code, slow=False)
                if success:
                    st.session_state.tts_result = "normal"
                else:
                    st.error("音声の生成に失敗しました")
    
    with col2:
        if st.button("ゆっくり読み上げ"):
            with st.spinner("音声を生成中..."):
                success = play_text(selected_text, lang=lang_code, slow=True)
                if success:
                    st.session_state.tts_result = "slow"
                else:
                    st.error("音声の生成に失敗しました")

# テスト結果
st.markdown("## テスト結果")
if "tts_result" in st.session_state:
    st.success("✅ テキスト読み上げ機能が正常に動作しました")
    
    # テスト項目
    st.markdown("### テスト項目")
    st.markdown("- [x] テキストから音声ファイルの生成")
    st.markdown("- [x] 音声の再生")
    if st.session_state.tts_result == "slow":
        st.markdown("- [x] ゆっくりモードの動作確認")
else:
    st.info("「通常読み上げ」または「ゆっくり読み上げ」ボタンをクリックしてテストを実行してください")

# テスト手順
with st.sidebar:
    st.header("テスト手順")
    st.markdown("1. テキストを選択または入力")
    st.markdown("2. 言語を選択")
    st.markdown("3. 速度設定（ゆっくり／通常）")
    st.markdown("4. 読み上げボタンをクリック")
    st.markdown("5. 音声が再生されることを確認")
    
    st.markdown("---")
    st.markdown("#### 注意事項")
    st.markdown("- スピーカーまたはヘッドフォンが必要です")
    st.markdown("- 初回は少し時間がかかることがあります")
    st.markdown("- ブラウザの自動再生設定を確認してください") 