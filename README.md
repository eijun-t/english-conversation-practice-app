# english-conversation-practice-app

## 概要
ビジネスマン向けの英会話学習アプリです。
日本語のビジネステキスト（csv）をもとに、英会話の練習やテストができます。
音声入力やOpenAI APIを活用し、発音・文法・スピードなど多角的に学習をサポートします。

## 主な機能
### csv読み込みページ
  - 日本語ビジネステキストが記載されたcsvファイルをアップロード
  - アップロードしたcsvデータの表示・ダウンロード

### 回答画面
  - csvからランダムにビジネス英会話の質問を出題
  - ユーザーは音声で回答（音声→テキスト変換）

### 回答内容の表示
  - 文法・発音・スピード等のテスト結果を表示
  - OpenAI API連携
  - 回答内容の評価やフィードバックを自動生成

## セットアップ手順

### 主な使用技術

- Streamlit（Webアプリ作成）
- LangChain（AI連携）
- langchain-openai（OpenAI API連携）
- pydub（音声処理）
- SpeechRecognition（音声認識）
- gTTS（テキスト読み上げ）

1. 必要なツールのインストール
   - Python 3.9以上
   - Rye（Pythonのパッケージ管理ツール）

2. プロジェクトディレクトリに移動

   ```bash
   cd english-conversation-practice-app
   ```

3. 依存パッケージのインストール

   ```bash
   rye sync
   ```

4. アプリの起動（例）

   ```bash
   rye run streamlit run src/english_conversation_practice_app/app.py
   ```
   ※app.pyのパスやファイル名は実際のものに合わせてください。
