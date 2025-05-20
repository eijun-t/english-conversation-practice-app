import streamlit as st
import speech_recognition as sr
import numpy as np
import tempfile
import os
from pydub import AudioSegment
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import queue
import time
import threading
import io
import logging
from typing import Optional, List
import whisper  # OpenAI Whisperモデルをインポート

# 音声データのキューとフラグ
audio_frames_queue = queue.Queue()
recording_active = threading.Event()
audio_data_buffer = []

# ロガーのセットアップ
logger = logging.getLogger(__name__)

# Whisper音声認識モデルの読み込み（グローバルで1回だけ読み込むことでパフォーマンス向上）
# model_sizeはbase, small, medium, largeから選択可能（精度と速度のトレードオフ）
@st.cache_resource
def load_whisper_model():
    return whisper.load_model("base")

def record_audio_webrtc():
    """
    WebRTCを使用したブラウザベースの音声録音機能
    """
    # 現在のステートを確認
    if "recording_state" not in st.session_state:
        st.session_state.recording_state = "inactive"
        st.session_state.audio_data = None
        st.session_state.recognized_text = None
    
    # Whisperモデルを読み込む（キャッシュされるので効率的）
    whisper_model = load_whisper_model()
    
    # UI用のプレースホルダー
    status_placeholder = st.empty()
    button_col1, button_col2 = st.columns(2)
    text_placeholder = st.empty()
    
    # 録音完了後のテキスト表示エリア
    if st.session_state.recognized_text:
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
        audio_data_buffer.clear()
        st.session_state.recording_state = "recording"
        recording_active.set()
        st.rerun()
    
    # 録音停止ボタン
    if button_col2.button("⏹️ 録音停止", disabled=st.session_state.recording_state != "recording"):
        recording_active.clear()
        st.session_state.recording_state = "processing"
        
        # 音声データをバッファから取得
        if audio_data_buffer:
            # バッファの音声データを結合
            audio_array = np.concatenate(audio_data_buffer)
            
            # 音声認識処理
            try:
                # 一時ファイルに保存
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    temp_filename = f.name
                
                # pydubを使って音声ファイルとして保存
                # sample_widthを2（16ビット）に設定、サンプルレートを16000に設定（Whisperの推奨レート）
                audio_segment = AudioSegment(
                    audio_array.tobytes(), 
                    frame_rate=16000,  # サンプルレートをWhisper推奨の16kHzに変更
                    sample_width=2,
                    channels=1
                )
                
                # 音量を増幅して認識精度を向上
                audio_segment = audio_segment + 10  # 10dB増幅
                
                # ノイズリダクション（無音部分の除去）
                audio_segment = audio_segment.strip_silence(
                    silence_len=500,  # 500ms以上の無音を無視
                    silence_thresh=-40,  # -40dB以下を無音と判断
                    padding=300  # 前後に300msのパディングを追加
                )
                
                audio_segment.export(temp_filename, format="wav")
                
                # Whisperモデルで音声認識
                with st.spinner("Whisperで音声を分析中..."):
                    result = whisper_model.transcribe(
                        temp_filename,
                        language="en",  # 英語として認識
                        fp16=False,  # 精度を優先
                        temperature=0.0  # ランダム性を最小化
                    )
                    recognized_text = result["text"].strip()
                    
                    if recognized_text:
                        st.session_state.recognized_text = recognized_text
                    else:
                        st.session_state.recognized_text = None
                        raise Exception("音声を認識できませんでした。もう少し大きな声ではっきりと話してください。")
                
                # 一時ファイルを削除
                os.unlink(temp_filename)
                
                st.session_state.recording_state = "completed"
                
            except Exception as e:
                logger.error(f"音声認識エラー: {e}")
                st.session_state.recording_state = "completed"
                st.session_state.recognized_text = None
        else:
            st.session_state.recording_state = "inactive"
            
        st.rerun()
    
    # WebRTCコンポーネント (音声のみモード) - バッファサイズをさらに増加
    webrtc_ctx = webrtc_streamer(
        key="speech-to-text",
        mode=WebRtcMode.SENDONLY,
        audio_receiver_size=32768,  # バッファサイズをさらに増加
        media_stream_constraints={
            "video": False, 
            "audio": {
                "echoCancellation": True,  # エコーキャンセル
                "noiseSuppression": True,  # ノイズ抑制
                "autoGainControl": True    # 自動ゲイン制御
            }
        },
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    )
    
    # 音声データを処理
    if webrtc_ctx.audio_receiver and recording_active.is_set():
        try:
            # 音声データを受信
            audio_frames = webrtc_ctx.audio_receiver.get_frames(timeout=1)
            
            # 音声データをバッファに追加
            for audio_frame in audio_frames:
                sound_data = audio_frame.to_ndarray()
                audio_data_buffer.append(sound_data)
                
        except queue.Empty:
            pass
    
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
        result = record_audio_webrtc()
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