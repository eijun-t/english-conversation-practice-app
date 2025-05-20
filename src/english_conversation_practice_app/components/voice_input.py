import streamlit as st
import numpy as np
import tempfile
import os
from pydub import AudioSegment
import sounddevice as sd
import time
import logging
import whisper

# ロガーのセットアップ
logger = logging.getLogger(__name__)

# 設定
SAMPLE_RATE = 16000  # サンプリングレート (Hz)
DEFAULT_RECORD_DURATION = 5  # デフォルト録音時間 (秒)

# Whisper音声認識モデルのキャッシュ
@st.cache_resource
def load_whisper_model(model_size="base"):
    """Whisperモデルを読み込み、キャッシュする"""
    return whisper.load_model(model_size)

def record_audio_device(duration=DEFAULT_RECORD_DURATION):
    """
    sounddeviceを使用したマイク録音機能
    duration: 録音時間（秒）
    戻り値: 認識されたテキスト、または None（キャンセル時）
    """
    # 現在のステートを確認
    if "recording_state" not in st.session_state:
        st.session_state.recording_state = "inactive"
        st.session_state.recognized_text = None
    
    # Whisperモデルを読み込む（キャッシュされるので効率的）
    whisper_model = load_whisper_model()
    
    # UI用のプレースホルダー
    status_placeholder = st.empty()
    button_col1, button_col2 = st.columns(2)
    text_placeholder = st.empty()
    
    # 録音完了後のテキスト表示エリア
    if st.session_state.recording_state == "completed" and st.session_state.recognized_text:
        text_placeholder.success(f"認識されたテキスト: {st.session_state.recognized_text}")
    
    # 録音状態に応じたUIの表示
    if st.session_state.recording_state == "inactive":
        status_placeholder.info("🎤 「録音開始」ボタンをクリックして、英語で話してください")
    elif st.session_state.recording_state == "recording":
        status_placeholder.warning("🔴 録音中... 英語で話してください")
    elif st.session_state.recording_state == "processing":
        status_placeholder.info("⏳ 音声を処理中...")
    elif st.session_state.recording_state == "completed":
        if st.session_state.recognized_text:
            status_placeholder.success("✅ 音声認識完了！")
        else:
            status_placeholder.error("❌ 音声認識に失敗しました。もう一度試してください。")
    
    # 録音開始ボタン
    if button_col1.button("🎤 録音開始", type="primary", disabled=st.session_state.recording_state == "recording"):
        st.session_state.recording_state = "recording"
        
        with st.spinner(f"{duration}秒間録音中..."):
            # プログレスバー
            progress_bar = st.progress(0)
            
            # 音声録音
            audio_data = sd.rec(
                int(duration * SAMPLE_RATE),
                samplerate=SAMPLE_RATE, 
                channels=1,
                dtype='float32'
            )
            
            # 録音中の進捗表示
            for i in range(duration):
                # 進捗バーを更新
                progress_bar.progress((i + 1) / duration)
                time.sleep(1)
                
            sd.wait()  # 録音完了まで待機
            
            # 状態更新
            st.session_state.recording_state = "processing"
            status_placeholder.info("⏳ 音声を処理中...")
            
            try:
                # 音声データの処理
                with st.spinner("音声を処理中..."):
                    # 音声データを正規化
                    audio_data = audio_data.flatten()
                    
                    # 音量を増幅
                    audio_data = audio_data * 1.5
                    
                    # int16形式に変換（WAVファイル保存用）
                    audio_int16 = (audio_data * 32767).astype(np.int16)
                    
                    # 一時ファイルに保存
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                        temp_filename = f.name
                    
                    # pydubでAudioSegmentに変換して保存
                    audio_segment = AudioSegment(
                        audio_int16.tobytes(),
                        frame_rate=SAMPLE_RATE,
                        sample_width=2,
                        channels=1
                    )
                    
                    # 音量を増幅して認識精度を向上
                    audio_segment = audio_segment + 15  # 15dB増幅
                    
                    # ノイズリダクション
                    audio_segment = audio_segment.strip_silence(
                        silence_len=300,  # 300ms以上の無音を無視
                        silence_thresh=-35,  # -35dB以下を無音と判断
                        padding=200  # 前後に200msのパディングを追加
                    )
                    
                    audio_segment.export(temp_filename, format="wav")
                
                # Whisperモデルによる音声認識
                with st.spinner("Whisperで音声を分析中..."):
                    # 音声認識実行
                    result = whisper_model.transcribe(
                        temp_filename,
                        language="en",
                        fp16=False,
                        temperature=0.0,
                        condition_on_previous_text=False
                    )
                    
                    recognized_text = result["text"].strip()
                    
                    # 一時ファイルを削除
                    os.unlink(temp_filename)
                    
                    if recognized_text:
                        st.session_state.recognized_text = recognized_text
                    else:
                        st.session_state.recognized_text = None
                        raise Exception("音声を認識できませんでした。もう少し大きな声ではっきりと話してください。")
                
                st.session_state.recording_state = "completed"
                st.rerun()
                
            except Exception as e:
                logger.error(f"音声認識エラー: {e}")
                st.session_state.recording_state = "completed"
                st.session_state.recognized_text = None
                st.rerun()
    
    # 録音キャンセルボタン
    if button_col2.button("⏹️ キャンセル", disabled=st.session_state.recording_state != "recording"):
        st.session_state.recording_state = "inactive"
        st.rerun()
    
    # 現在の状態に応じて結果を返す
    if st.session_state.recording_state == "completed" and st.session_state.recognized_text:
        return st.session_state.recognized_text
    return None

def record_audio_text():
    """
    テキスト入力を使用して回答を取得する関数（フォールバック）
    戻り値: 入力されたテキスト、または None（キャンセル時）
    """
    # エラーメッセージ表示用
    error_placeholder = st.empty()
    
    # 入力状態表示
    status_placeholder = st.empty()
    status_placeholder.info("🖊️ 英語で回答を入力してください。")
    
    try:
        # テキスト入力
        user_input = st.text_input("英語で回答を入力:", key="voice_replacement_input")
        
        if st.button("回答を送信", key="submit_text_answer"):
            if user_input:
                # 入力完了表示
                status_placeholder.success("✓ 回答を受け付けました！")
                return user_input
            else:
                error_placeholder.error("テキストが入力されていません。")
                return None
            
    except Exception as e:
        error_placeholder.error(f"エラーが発生しました: {e}")
    
    # 入力がない場合はNoneを返す
    return None

def record_audio():
    """
    音声入力またはテキスト入力を提供する関数
    戻り値: 認識されたテキストまたは入力されたテキスト、または None
    """
    # タブを作成して音声入力とテキスト入力を切り替え可能に
    tab1, tab2 = st.tabs(["🎤 音声で回答", "⌨️ テキストで回答"])
    
    with tab1:
        result = record_audio_device()
        if result:
            return result
    
    with tab2:
        result = record_audio_text()
        if result:
            return result
    
    return None

def voice_input_button():
    """
    回答入力ボタンとその処理を提供する関数
    戻り値: 入力されたテキスト、または None（未入力時やエラー時）
    """
    if st.button("🎤 回答する", type="primary", key="voice_input_button"):
        # 音声またはテキスト入力を実行
        recognized_text = record_audio()
        
        # 入力結果を返す
        return recognized_text
    
    # ボタンが押されていない場合はNoneを返す
    return None 