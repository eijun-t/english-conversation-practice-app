import streamlit as st
import os
import time
from english_conversation_practice_app.utils.csv_loader import load_conversation_csv
from english_conversation_practice_app.components.evaluation import evaluate_answer, get_openai_api_key
from english_conversation_practice_app.components.tts import play_text, play_reference_button, slow_play_button
from english_conversation_practice_app.components.voice_input import record_and_transcribe, load_whisper_model
import random

# 設定
DEFAULT_RECORD_DURATION = 5  # デフォルト録音時間 (秒)

# ページ設定
st.set_page_config(page_title="英会話練習アプリ", page_icon="🎤", layout="wide")

# タイトルとアプリの説明
st.title("英会話練習アプリ")
st.subheader("ビジネス英会話の練習ができます")

# サイドバーにAPIキー入力フィールドを追加
with st.sidebar:
    st.header("設定")
    api_key = get_openai_api_key()
    
    st.markdown("---")
    st.markdown("### 使い方")
    st.markdown("1. 「練習を始める」ボタンをクリックします")
    st.markdown("2. 表示された日本語を英語で話してみましょう")
    st.markdown("3. 「録音開始」ボタンをクリックして録音します")
    st.markdown("4. 評価結果と模範回答を確認します")
    st.markdown("5. 「次の問題へ」ボタンで次の問題に進みます")
    
    st.markdown("---")
    st.markdown("© 2025 英会話練習アプリ")

# セッション状態の初期化
if "questions" not in st.session_state:
    try:
        # CSVファイルから問題を読み込む
        csv_path = "data/business_english_mvp_3cols.csv"
        st.session_state.questions = load_conversation_csv(csv_path)
        st.success(f"{len(st.session_state.questions)}件の問題が読み込まれました！")
    except Exception as e:
        st.error(f"問題の読み込みに失敗しました: {e}")
        st.stop()

if "current_question" not in st.session_state:
    st.session_state.current_question = None

if "user_answer" not in st.session_state:
    st.session_state.user_answer = None

if "evaluation_result" not in st.session_state:
    st.session_state.evaluation_result = None

# 録音状態
if "recording_active" not in st.session_state:
    st.session_state.recording_active = False

# 新しい問題をランダムに選択する関数
def get_new_question():
    if st.session_state.questions:
        st.session_state.current_question = random.choice(st.session_state.questions)
        st.session_state.user_answer = None
        st.session_state.evaluation_result = None
        st.session_state.recording_active = False

# 次の問題へ進むコールバック関数
def next_question_callback():
    get_new_question()

# 練習開始ボタン
if st.session_state.current_question is None:
    st.info("「練習を始める」ボタンをクリックすると、ランダムな日本語文が表示されます。")
    if st.button("練習を始める", type="primary", on_click=next_question_callback):
        pass  # コールバックで処理するため、ここでは何もしない

# 問題表示エリア
if st.session_state.current_question is not None:
    with st.container():
        st.markdown("### 問題")
        st.markdown(f"**この日本語を英語で言ってみましょう:**")
        st.markdown(f"### {st.session_state.current_question['japanese_source']}")
        
        # 回答セクション
        st.markdown("### あなたの回答")
        
        # エラーメッセージエリア
        error_placeholder = st.empty()
        
        # 録音開始ボタン
        if st.button("🎤 録音開始", type="primary", key="direct_record_btn"):
            try:
                # voice_input.pyのrecord_and_transcribe関数を使用
                recognized_text = record_and_transcribe(DEFAULT_RECORD_DURATION)
                
                # 認識結果の処理
                if recognized_text:
                    st.session_state.user_answer = recognized_text
                    
                    # 自動的に評価も実行
                    if not st.session_state.evaluation_result:
                        with st.spinner("回答を評価中..."):
                            st.session_state.evaluation_result = evaluate_answer(
                                st.session_state.current_question["japanese_source"],
                                st.session_state.current_question["english_reference"],
                                st.session_state.user_answer,
                                api_key
                            )
                else:
                    error_placeholder.error("音声を認識できませんでした。もう一度試してください。")
            
            except Exception as e:
                import traceback
                error_traceback = traceback.format_exc()
                error_placeholder.error(f"録音エラー: {str(e)}\n\n詳細:\n{error_traceback}")
        
        # 音声認識結果の表示
        if st.session_state.user_answer:
            st.markdown(f"**あなたの回答:** {st.session_state.user_answer}")
        
        # 評価結果の表示
        if st.session_state.evaluation_result:
            st.markdown("### 評価結果")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("発音", f"{st.session_state.evaluation_result['pronunciation']}/100")
                st.metric("文法", f"{st.session_state.evaluation_result['grammar']}/100")
                st.metric("語彙", f"{st.session_state.evaluation_result['vocabulary']}/100")
            with col2:
                st.metric("意味の一致度", f"{st.session_state.evaluation_result['meaning']}/100")
                st.metric("総合評価", f"{st.session_state.evaluation_result['overall']}/100", 
                         delta="合格" if st.session_state.evaluation_result['overall'] >= 70 else "もう少し")
            
            st.markdown("### アドバイス")
            st.info(st.session_state.evaluation_result["advice"])
            
            st.markdown("### 模範回答")
            st.success(st.session_state.current_question["english_reference"])
            
            # 模範回答の音声再生ボタン
            col1, col2 = st.columns(2)
            with col1:
                play_reference_button(st.session_state.current_question["english_reference"])
            with col2:
                slow_play_button(st.session_state.current_question["english_reference"])
            
            # 次の問題へ
            if st.button("次の問題へ", type="primary", on_click=next_question_callback):
                pass  # コールバックで処理するため、ここでは何もしない 