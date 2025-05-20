#!/usr/bin/env python3
"""
音声認識機能のStreamlitテスト
"""
import os
import tempfile
import time
import whisper
import numpy as np
import streamlit as st
from pydub import AudioSegment
import sounddevice as sd

# 設定
SAMPLE_RATE = 16000  # サンプリングレート (Hz)
RECORD_DURATION = 5  # 録音時間 (秒)
WHISPER_MODEL = "base"  # Whisperのモデルサイズ

# ページ設定
st.set_page_config(page_title="音声認識テスト", page_icon="🎤")

# Whisperモデルをキャッシュ
@st.cache_resource
def load_whisper_model(model_name="base"):
    return whisper.load_model(model_name)

# タイトル
st.title("音声認識テスト")
st.subheader("sounddeviceを使用した直接音声認識")

# 録音時間スライダー
duration = st.slider("録音時間（秒）", 3, 10, 5)

# 録音ボタン
if st.button("🎤 録音開始", type="primary"):
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
            model = load_whisper_model(WHISPER_MODEL)
            
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
        
        # 認識結果表示
        st.markdown("### 認識結果")
        if recognized_text:
            st.success(f"「{recognized_text}」")
            # セッションに保存
            st.session_state.last_text = recognized_text
        else:
            st.error("音声を認識できませんでした。もう一度試してください。")

# ヒント表示
st.markdown("---")
st.markdown("### 使い方")
st.markdown("1. 「録音開始」ボタンをクリックします")
st.markdown("2. マイクに向かって英語で話します")
st.markdown("3. 指定した秒数が経過すると自動的に録音が停止します")
st.markdown("4. Whisperモデルが音声を認識し、結果が表示されます")

# 以前の結果表示
if "last_text" in st.session_state:
    st.markdown("---")
    st.markdown("### 前回の認識結果")
    st.info(st.session_state.last_text)

# テスト用のサンプルフレーズ表示
st.markdown("---")
st.markdown("### テスト用サンプルフレーズ")
sample_phrases = [
    "Hello, my name is John.",
    "Nice to meet you.",
    "Thank you for your cooperation.",
    "I will send the proposal tomorrow.",
    "Please let me know if you have any questions."
]

for i, phrase in enumerate(sample_phrases):
    st.markdown(f"{i+1}. {phrase}") 