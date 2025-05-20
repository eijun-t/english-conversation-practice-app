import streamlit as st
import json
import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain

# .envファイルの読み込み
load_dotenv()

# OpenAI APIキーの取得（環境変数またはSecrets）
def get_openai_api_key():
    """OpenAI APIキーを取得する関数"""
    # 環境変数からAPIキーを取得
    api_key = os.getenv("OPENAI_API_KEY")
    
    # 環境変数に設定されていない場合はテキスト入力で取得
    if not api_key:
        api_key = st.text_input("OpenAI APIキー", type="password", key="openai_api_key")
        
    return api_key

# 評価用のプロンプトテンプレート
EVALUATION_PROMPT = """
あなたは英会話の評価をする厳格な先生です。以下の条件で正確かつ厳しく評価してください。

【評価対象】
日本語文: {japanese_text}
参考英語回答: {reference_english}
ユーザーの回答: {user_speech_text}

【評価基準】
以下の項目を100点満点で評価し、JSONフォーマットで返してください。各項目は下記のガイドラインに従って厳格に評価してください。

- pronunciation (発音の正確さ)：
  * 90-100: 完璧または非常に近い発音
  * 70-89: 小さな誤りはあるが理解可能
  * 50-69: 複数の発音ミス
  * 30-49: 多くの発音ミス、理解が難しい
  * 0-29: 発音が極めて不正確

- grammar (文法の正確さ)：
  * 90-100: 文法的に完全または些細なミスのみ
  * 70-89: 小さな文法ミスがある
  * 50-69: いくつかの明確な文法ミス
  * 30-49: 多くの文法ミス
  * 0-29: 文法的に非常に不正確

- vocabulary (語彙の適切さ)：
  * 90-100: 非常に適切な語彙選択
  * 70-89: ほぼ適切だが、より良い選択肢がある
  * 50-69: いくつかの不適切な語彙使用
  * 30-49: 多くの不適切な語彙使用
  * 0-29: 語彙選択が極めて不適切

- meaning (意味の一致度)：
  * 90-100: 元の日本語と完全に一致または非常に近い
  * 70-89: 主要な意味は伝わるが、細部に違い
  * 50-69: 部分的に意味が一致している
  * 20-49: 意味がかなり異なる
  * 0-19: 意味が全く異なる（例：「会議を始めましょう」に対して「月に行きましょう」など）

- overall (総合評価)：
  * 各項目の重み付け平均（特に意味の一致度を重視）
  * 意味が全く異なる場合は自動的に40点以下

【評価例】
例1：日本語「会議を始めましょう」、参考回答「Let's start the meeting」
- 回答「Let's begin the meeting」→ meaning: 95点（ほぼ同じ意味）
- 回答「Let's go to the moon」→ meaning: 5点（全く意味が異なる）、overall: 30点以下

例2：日本語「自己紹介をしてください」、参考回答「Please introduce yourself」
- 回答「Please tell me about yourself」→ meaning: 85点（同じ意味だが表現が異なる）
- 回答「I like watching movies」→ meaning: 10点（全く関係ない応答）、overall: 30点以下

【アドバイス】
具体的に何が間違っていたか、どう改善すべきかを日本語で詳しく説明してください。特に意味が異なる場合は、その違いを明確に指摘してください。

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