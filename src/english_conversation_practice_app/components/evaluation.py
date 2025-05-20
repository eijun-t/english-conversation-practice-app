import streamlit as st
import json
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain

# OpenAI APIキーの取得（環境変数またはSecrets）
def get_openai_api_key():
    """OpenAI APIキーを取得する関数"""
    # 本番環境ではst.secrets["OPENAI_API_KEY"]などの安全な方法を使用
    return st.text_input("OpenAI APIキー", type="password", key="openai_api_key")

# 評価用のプロンプトテンプレート
EVALUATION_PROMPT = """
あなたは英会話の評価をする先生です。以下の条件で評価してください。

【評価対象】
日本語文: {japanese_text}
参考英語回答: {reference_english}
ユーザーの回答: {user_speech_text}

【評価項目】
以下の項目を100点満点で評価し、JSONフォーマットで返してください。
- pronunciation: 発音の正確さ（実際には音声が聞こえないので、スペルから想定される発音について評価）
- grammar: 文法の正確さ（文法ミスがあれば指摘）
- vocabulary: 語彙の適切さ（より適切な単語があれば提案）
- meaning: 意味の一致度（元の日本語文の意味をどれだけ正確に伝えているか）
- overall: 総合評価
- advice: 改善のためのアドバイス（日本語で具体的に）

【返答フォーマット】
{{
  "pronunciation": 数値,
  "grammar": 数値,
  "vocabulary": 数値,
  "meaning": 数値,
  "overall": 数値,
  "advice": "テキスト"
}}

JSONフォーマットのみを返してください。余計な説明は不要です。
"""

def evaluate_answer(japanese_text, reference_english, user_speech_text, api_key=None):
    """
    ユーザーの音声回答を評価する関数
    
    Args:
        japanese_text (str): 日本語の問題文
        reference_english (str): 参考英語回答
        user_speech_text (str): ユーザーの回答（音声認識結果）
        api_key (str, optional): OpenAI APIキー
        
    Returns:
        dict: 評価結果を含む辞書
    """
    # apiキーがなければダミーの評価結果を返す（デモ用）
    if not api_key:
        return {
            "pronunciation": 85,
            "grammar": 90,
            "vocabulary": 80, 
            "meaning": 95,
            "overall": 88,
            "advice": "APIキーが設定されていないため、実際の評価はできませんでした。これはデモ用の結果です。"
        }
    
    try:
        # LangChainのセットアップ
        prompt = PromptTemplate(
            input_variables=["japanese_text", "reference_english", "user_speech_text"],
            template=EVALUATION_PROMPT
        )
        
        # OpenAI LLMの初期化
        llm = ChatOpenAI(api_key=api_key, model_name="gpt-3.5-turbo")
        
        # チェーンの設定
        chain = LLMChain(llm=llm, prompt=prompt)
        
        # 評価の実行
        result = chain.run({
            "japanese_text": japanese_text,
            "reference_english": reference_english,
            "user_speech_text": user_speech_text
        })
        
        # 結果をJSONに変換
        try:
            evaluation = json.loads(result)
            return evaluation
        except json.JSONDecodeError:
            # JSONデコードに失敗した場合
            return {
                "pronunciation": 0,
                "grammar": 0,
                "vocabulary": 0,
                "meaning": 0,
                "overall": 0,
                "advice": f"評価結果のフォーマットエラー。APIの応答: {result}"
            }
        
    except Exception as e:
        # エラーが発生した場合
        return {
            "pronunciation": 0,
            "grammar": 0,
            "vocabulary": 0,
            "meaning": 0,
            "overall": 0,
            "advice": f"評価中にエラーが発生しました: {str(e)}"
        } 