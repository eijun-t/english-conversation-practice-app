import streamlit as st
import numpy as np
import tempfile
import os
import time
import whisper
import traceback
import logging
from pydub import AudioSegment
import sounddevice as sd

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

def record_and_transcribe(duration=DEFAULT_RECORD_DURATION):
    """
    音声を録音し、Whisperで文字起こしする関数
    
    Args:
        duration (int): 録音時間（秒）
        
    Returns:
        str or None: 認識されたテキスト、または認識失敗時はNone
    """
    # エラーメッセージエリア
    error_placeholder = st.empty()
    
    try:
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
            
            # 成功メッセージ
            st.success("✅ 録音完了!")
            
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
                    silence_len=300,
                    silence_thresh=-35,
                    padding=200
                )
                
                audio_segment.export(temp_filename, format="wav")
            
            # Whisperモデルによる音声認識
            with st.spinner("Whisperで音声を分析中..."):
                # Whisperモデル読み込み
                model = load_whisper_model()
                
                # 音声認識実行
                result = model.transcribe(
                    temp_filename,
                    language="en",
                    fp16=False,
                    temperature=0.0,
                    condition_on_previous_text=False
                )
                
                recognized_text = result["text"].strip()
                
                # 一時ファイルを削除
                os.unlink(temp_filename)
            
            # 認識結果の処理
            if recognized_text:
                return recognized_text
            else:
                error_placeholder.error("音声を認識できませんでした。もう一度試してください。")
                return None
    
    except Exception as e:
        error_traceback = traceback.format_exc()
        error_placeholder.error(f"録音エラー: {str(e)}\n\n詳細:\n{error_traceback}")
        return None

# 以下の関数は互換性のために残しておく（既存コードで使用されている場合）
def record_audio(duration=DEFAULT_RECORD_DURATION):
    """
    互換性のための関数。新しい実装ではrecord_and_transcribeを使用してください。
    """
    return record_and_transcribe(duration)

def record_audio_text():
    """テキスト入力を使用して回答を取得する関数（フォールバック）"""
    return None

def voice_input_button():
    """回答入力ボタンとその処理を提供する関数（互換性のため）"""
    return None