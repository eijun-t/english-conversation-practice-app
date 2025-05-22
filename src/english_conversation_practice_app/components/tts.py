import streamlit as st
from gtts import gTTS
import tempfile
import os
from pydub import AudioSegment
import numpy as np

def text_to_speech(text, lang='en', slow=False):
    """
    テキストを音声に変換し、一時ファイルとして保存して再生用URLを返す
    
    Args:
        text (str): 音声に変換するテキスト
        lang (str): 言語コード（デフォルト: 'en'）
        slow (bool): ゆっくり発音するかどうか
        
    Returns:
        str: 音声ファイルのパス
    """
    try:
        # テキストを音声に変換
        tts = gTTS(text=text, lang=lang, slow=slow)
        
        # 一時ファイルを作成
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            temp_file = fp.name
        
        # 音声ファイルを保存
        tts.save(temp_file)
        
        return temp_file
    
    except Exception as e:
        st.error(f"音声変換エラー: {str(e)}")
        return None

def play_text(text, lang='en', slow=False, autoplay=False, key=None):
    """
    テキストを音声に変換し、Streamlitで再生するUIを提供する
    
    Args:
        text (str): 音声に変換するテキスト
        lang (str): 言語コード（デフォルト: 'en'）
        slow (bool): ゆっくり発音するかどうか
        autoplay (bool): 自動再生するかどうか
        key (str): Streamlitコンポーネントの一意キー
        
    Returns:
        bool: 成功したらTrue
    """
    # キーが指定されていなければデフォルト値を使用
    if key is None:
        key = f"tts_{text[:10]}"
    
    # 音声ファイルを生成
    audio_file = text_to_speech(text, lang, slow)
    
    if audio_file:
        try:
            # 音声プレイヤーを表示
            st.audio(audio_file, autoplay=autoplay)
            
            # 音声ファイルへのリンクを表示（オプション）
            # st.download_button(
            #     label="音声をダウンロード", 
            #     data=open(audio_file, 'rb'), 
            #     file_name="speech.mp3",
            #     mime="audio/mp3"
            # )
            
            # 一時ファイルを削除
            os.unlink(audio_file)
            return True
            
        except Exception as e:
            st.error(f"音声再生エラー: {str(e)}")
            
            # エラー発生時も一時ファイルを削除
            if os.path.exists(audio_file):
                os.unlink(audio_file)
            
            return False
    
    return False

def play_reference_button(reference_text):
    """
    参考回答を読み上げるボタンを表示
    
    Args:
        reference_text (str): 読み上げるテキスト
        
    Returns:
        bool: ボタンが押されたらTrue
    """
    if st.button("🔊 模範回答を聞く", key="play_reference"):
        return play_text(reference_text)
    return False

def slow_play_button(reference_text):
    """
    参考回答をゆっくり読み上げるボタンを表示
    
    Args:
        reference_text (str): 読み上げるテキスト
        
    Returns:
        bool: ボタンが押されたらTrue
    """
    if st.button("🐢 ゆっくり聞く", key="slow_play"):
        return play_text(reference_text, slow=True)
    return False 