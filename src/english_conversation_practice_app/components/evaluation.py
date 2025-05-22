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
必ず日本語でアドバイスを提供してください。英語は使用しないでください。
以下の点について具体的に説明してください：

1. 発音の間違い：
   - どの単語やフレーズの発音が間違っていたか具体的に指摘してください
   - 正しい発音の仕方について簡潔に説明してください
   - 例：「"price"の発音で"i"の音が短すぎます。"ai"と長めに発音しましょう」

2. 文法の間違い：
   - どの部分に文法ミスがあったか具体的に指摘してください
   - 正しい文法形式を示してください
   - 例：「"I going"は動詞の形が不適切です。"I am going"または"I go"が正しい形です」

3. 語彙の選択：
   - 不適切または改善できる語彙を特定してください
   - より適切な言い回しや表現を提案してください
   - 例：「"make a meeting"よりも"schedule a meeting"または"arrange a meeting"の方が自然です」

4. 意味の伝達：
   - ユーザーの回答と期待される回答の意味の違いを説明してください
   - どうすれば意図した意味に近づけるか具体的に提案してください

全体的な改善点をまとめ、次回の練習でどこに注意すべきかを明確に伝えてください。
アドバイスは具体的かつ実用的で、学習者が直接応用できる内容にしてください。

【返答フォーマット】
{{
  "pronunciation": 数値,
  "grammar": 数値,
  "vocabulary": 数値,
  "meaning": 数値,
  "overall": 数値,
  "advice": "※日本語で具体的なアドバイスを記入してください。例：
「発音：単語Xの発音で〇〇の部分が不正確です。△△と発音するとよいでしょう。
文法：『I am go』の部分が間違っています。正しくは『I am going』です。
語彙：『make the document』という表現より『create the document』の方が適切です。
意味：「〇〇してください」という依頼の意味が伝わっていません。『Could you please...』という表現を使うとよいでしょう。
次回の練習では特に△△に注意して、〇〇のような表現を練習しましょう。」"
}}

JSONフォーマットのみを返してください。余計な説明は不要です。
advice欄は必ず日本語で記述してください。
コードブロック記号（```）やマークダウン形式は使用せず、生のJSONデータのみを返してください。
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
        llm = ChatOpenAI(
            api_key=api_key, 
            model_name="gpt-4o", 
            temperature=0.2  # 低い温度で具体的な回答を促す
        )
        
        # 最新のRunnableSequenceパターンを使用
        chain = prompt | llm
        
        # 評価の実行
        result = chain.invoke({
            "japanese_text": japanese_text,
            "reference_english": reference_english,
            "user_speech_text": user_speech_text
        }).content
        
        # 結果をJSONに変換
        try:
            # APIの応答から余分なマークダウン記号などを削除
            cleaned_result = result
            # Markdownコードブロックの記号を削除
            if "```json" in cleaned_result:
                cleaned_result = cleaned_result.replace("```json", "").strip()
            if "```" in cleaned_result:
                cleaned_result = cleaned_result.replace("```", "").strip()
            
            # 前後の空白を削除
            cleaned_result = cleaned_result.strip()
            
            # デバッグ情報
            # st.write(f"クリーニング後のJSON: {cleaned_result}")
            
            evaluation = json.loads(cleaned_result)
            return evaluation
        except json.JSONDecodeError as json_err:
            # JSONデコードに失敗した場合
            return {
                "pronunciation": 0,
                "grammar": 0,
                "vocabulary": 0,
                "meaning": 0,
                "overall": 0,
                "advice": f"評価結果のフォーマットエラー。APIの応答: {result}\nエラー詳細: {str(json_err)}"
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