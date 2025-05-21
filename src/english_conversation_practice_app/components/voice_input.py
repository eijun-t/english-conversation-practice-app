import streamlit as st
import numpy as np
import tempfile
import os
from pydub import AudioSegment
import sounddevice as sd
import time
import logging
import whisper
import traceback

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

def record_audio(duration=DEFAULT_RECORD_DURATION):
    """
    音声入力を処理するメイン関数
    duration: 録音時間（秒）
    戻り値: 認識されたテキスト、または None（キャンセル時）
    """
    # デバッグ情報表示
    st.write("### デバッグ情報")
    debug_area = st.empty()
    
    # タブを作成して音声入力とテキスト入力を切り替え可能に
    tab1, tab2 = st.tabs(["🎤 音声で回答", "⌨️ テキストで回答"])
    
    with tab1:
        # エラーメッセージ表示用のプレースホルダー
        error_placeholder = st.empty()
        
        # 録音ボタン
        if st.button("🎤 録音開始", type="primary", key="voice_record_btn"):
            # デバッグ情報を表示
            debug_area.info("録音ボタンが押されました！")
            st.write(f"現在時刻: {time.strftime('%H:%M:%S')}")
            
            try:
                with st.spinner(f"{duration}秒間録音中..."):
                    # デバッグ情報追加
                    st.write("録音を開始します...")
                    
                    # プログレスバー
                    progress_bar = st.progress(0)
                    
                    # 音声録音
                    try:
                        audio_data = sd.rec(
                            int(duration * SAMPLE_RATE),
                            samplerate=SAMPLE_RATE, 
                            channels=1,
                            dtype='float32'
                        )
                    except Exception as e:
                        error_traceback = traceback.format_exc()
                        error_placeholder.error(f"録音開始エラー: {str(e)}\n\n詳細:\n{error_traceback}")
                        logger.error(f"録音開始エラー: {e}\n{error_traceback}")
                        return None
                    
                    # 録音中の進捗表示
                    for i in range(duration):
                        # 進捗バーを更新
                        st.write(f"録音中... {i+1}/{duration}秒")
                        progress_bar.progress((i + 1) / duration)
                        time.sleep(1)
                    
                    try:
                        sd.wait()  # 録音完了まで待機
                    except Exception as e:
                        error_traceback = traceback.format_exc()
                        error_placeholder.error(f"録音待機エラー: {str(e)}\n\n詳細:\n{error_traceback}")
                        logger.error(f"録音待機エラー: {e}\n{error_traceback}")
                        return None
                    
                    st.write("録音完了！")
                    
                    # 成功メッセージ
                    st.success("✅ 録音完了!")
                    
                    # 音声データの処理
                    with st.spinner("音声を処理中..."):
                        try:
                            st.write("音声データを処理します...")
                            # 音声データを正規化
                            audio_data = audio_data.flatten()
                            
                            # 音量を増幅
                            audio_data = audio_data * 1.5
                            
                            # int16形式に変換（WAVファイル保存用）
                            audio_int16 = (audio_data * 32767).astype(np.int16)
                            
                            # 一時ファイルに保存
                            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                                temp_filename = f.name
                                st.write(f"一時ファイル作成: {temp_filename}")
                            
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
                            
                            st.write("一時ファイルに音声を書き出します...")
                            audio_segment.export(temp_filename, format="wav")
                            st.write("ファイル書き出し完了")
                        
                            # Whisperモデルによる音声認識
                            with st.spinner("Whisperで音声を分析中..."):
                                st.write("Whisperモデルを読み込みます...")
                                # Whisperモデル読み込み
                                model = load_whisper_model()
                                
                                st.write("音声認識を実行します...")
                                # 音声認識実行
                                result = model.transcribe(
                                    temp_filename,
                                    language="en",
                                    fp16=False,
                                    temperature=0.0,
                                    condition_on_previous_text=False
                                )
                                
                                recognized_text = result["text"].strip()
                                st.write(f"認識結果: {recognized_text}")
                                
                                # 一時ファイルを削除
                                os.unlink(temp_filename)
                                st.write("一時ファイル削除完了")
                            
                            # 認識結果表示
                            if recognized_text:
                                st.session_state.recognized_text = recognized_text
                                st.success(f"認識結果: 「{recognized_text}」")
                                return recognized_text
                            else:
                                error_placeholder.error("音声を認識できませんでした。もう一度試してください。")
                                return None
                        
                        except Exception as e:
                            error_traceback = traceback.format_exc()
                            error_placeholder.error(f"音声処理エラー: {str(e)}\n\n詳細:\n{error_traceback}")
                            logger.error(f"音声処理エラー: {e}\n{error_traceback}")
                            return None
            except Exception as e:
                error_traceback = traceback.format_exc()
                error_placeholder.error(f"録音プロセス全体エラー: {str(e)}\n\n詳細:\n{error_traceback}")
                logger.error(f"録音プロセス全体エラー: {e}\n{error_traceback}")
                return None
        
        # 前回の結果があれば表示
        if "recognized_text" in st.session_state and st.session_state.recognized_text:
            st.info(f"前回の認識結果: {st.session_state.recognized_text}")
    
    with tab2:
        # テキスト入力フォーム
        user_input = st.text_input("英語で回答を入力:", key="text_input_key")
        
        if st.button("回答を送信", key="submit_text_btn"):
            if user_input:
                st.success("✓ テキスト回答を受け付けました！")
                return user_input
            else:
                st.error("テキストが入力されていません。")
    
    # どちらのタブでも入力がなければNoneを返す
    return None

# 以下の2つの関数は互換性のために残しておく
def record_audio_text():
    """
    テキスト入力を使用して回答を取得する関数（フォールバック）
    """
    return None

def voice_input_button():
    """
    回答入力ボタンとその処理を提供する関数（互換性のため）
    """
    return None