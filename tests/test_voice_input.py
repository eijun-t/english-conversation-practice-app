import streamlit as st
from english_conversation_practice_app.components.voice_input import record_audio

# ページ設定
st.set_page_config(page_title="音声・テキスト入力テスト", page_icon="🎤")

# タイトルとアプリの説明
st.title("2. 音声・テキスト入力テスト")
st.subheader("ブラウザベースの音声入力とテキスト入力機能の検証")

# テスト用のコンテナ
test_container = st.container()

with test_container:
    st.write("音声で回答する場合は「録音開始」ボタンをクリックして英語で話すか、テキストで回答を入力してください。")
    
    # 音声・テキスト入力を直接呼び出し
    result = record_audio()
    
    # 入力結果がある場合はセッションに保存
    if result:
        st.session_state.input_result = result

    # 入力結果の表示
    if "input_result" in st.session_state:
        st.markdown("### 入力結果")
        st.success(st.session_state.input_result)

# テスト用のサンプルフレーズ
st.markdown("## テスト用サンプルフレーズ")
sample_phrases = [
    "Hello, my name is John.",
    "Nice to meet you.",
    "Thank you for your cooperation.",
    "I will send the proposal tomorrow.",
    "Please let me know if you have any questions."
]

for i, phrase in enumerate(sample_phrases):
    st.markdown(f"{i+1}. {phrase}")

# テスト結果
st.markdown("## テスト結果")
if "input_result" in st.session_state:
    st.success("✅ 入力が完了しました")
    
    # テスト項目
    st.markdown("### テスト項目")
    st.markdown("- [x] ブラウザベースの音声入力")
    st.markdown("- [x] テキスト入力（フォールバック）")
    st.markdown("- [x] 入力結果の表示")
else:
    st.info("音声入力または「回答を送信」ボタンをクリックしてテストを実行してください")

# テスト手順
with st.sidebar:
    st.header("テスト手順")
    st.markdown("#### 音声入力の場合:")
    st.markdown("1. 「音声で回答」タブを選択")
    st.markdown("2. 「録音開始」ボタンをクリック")
    st.markdown("3. マイクに向かって英語でサンプルフレーズを話す")
    st.markdown("4. 「録音停止」ボタンをクリック")
    st.markdown("5. 音声認識結果が正しく表示されることを確認")
    
    st.markdown("#### テキスト入力の場合:")
    st.markdown("1. 「テキストで回答」タブを選択")
    st.markdown("2. 入力欄に英語でサンプルフレーズを入力")
    st.markdown("3. 「回答を送信」ボタンをクリック")
    st.markdown("4. 入力結果が正しく表示されることを確認")
    
    st.markdown("---")
    st.markdown("#### 注意事項")
    st.markdown("- マイクへのアクセス許可が必要です")
    st.markdown("- 音声認識では静かな環境で試してください")
    st.markdown("- テキスト入力ではサンプルフレーズをコピー＆ペーストしても構いません") 