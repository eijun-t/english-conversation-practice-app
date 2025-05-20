import streamlit as st
from english_conversation_practice_app.components.evaluation import evaluate_answer, get_openai_api_key

# ページ設定
st.set_page_config(page_title="評価機能テスト", page_icon="📊")

# タイトルとアプリの説明
st.title("3. 評価機能テスト")
st.subheader("ユーザーの回答を評価する機能の検証")

# サイドバーにAPIキー入力欄
with st.sidebar:
    st.header("設定")
    api_key = get_openai_api_key()
    
    st.markdown("---")
    st.header("テスト手順")
    st.markdown("1. OpenAI APIキーを入力（オプション）")
    st.markdown("2. サンプル問題を選択")
    st.markdown("3. テスト回答を入力、または選択")
    st.markdown("4. 「評価実行」ボタンをクリック")
    st.markdown("5. 評価結果を確認")
    
    st.markdown("---")
    st.markdown("#### 注意事項")
    st.markdown("- APIキーを入力しない場合はデモモードで動作します")
    st.markdown("- 実際のAPIを使用する場合はクレジットが消費されます")

# テスト用のサンプル問題
sample_questions = [
    {
        "japanese": "会議を始めましょう。",
        "english": "Let's start the meeting."
    },
    {
        "japanese": "自己紹介をしてください。",
        "english": "Please introduce yourself."
    },
    {
        "japanese": "ご協力ありがとうございます。",
        "english": "Thank you for your cooperation."
    }
]

# サンプル問題の選択
st.markdown("## 1. サンプル問題の選択")
question_index = st.selectbox(
    "テストする問題を選択してください",
    options=range(len(sample_questions)),
    format_func=lambda i: f"{sample_questions[i]['japanese']} → {sample_questions[i]['english']}"
)

selected_question = sample_questions[question_index]
st.info(f"日本語: {selected_question['japanese']}")
st.success(f"模範回答: {selected_question['english']}")

# ユーザー回答の入力
st.markdown("## 2. テスト回答の入力")

test_answers = [
    "Let's begin the meeting.",
    "Please introduce yourself to the team.",
    "Thank you for your help.",
    "I will send you the document tomorrow.",
    "I don't understand the question."
]

answer_method = st.radio(
    "回答入力方法を選択",
    options=["サンプル回答から選択", "直接入力"]
)

if answer_method == "サンプル回答から選択":
    answer_index = st.selectbox(
        "テスト回答を選択してください",
        options=range(len(test_answers)),
        format_func=lambda i: test_answers[i]
    )
    user_answer = test_answers[answer_index]
else:
    user_answer = st.text_input("回答を入力してください", value=selected_question['english'])

st.write(f"テスト回答: **{user_answer}**")

# 評価実行
st.markdown("## 3. 評価実行")
if st.button("評価実行", type="primary"):
    with st.spinner("評価中..."):
        # 評価を実行
        evaluation_result = evaluate_answer(
            selected_question['japanese'],
            selected_question['english'],
            user_answer,
            api_key
        )
        
        # 結果をセッションに保存
        st.session_state.evaluation_result = evaluation_result

# 評価結果の表示
if "evaluation_result" in st.session_state:
    st.markdown("## 4. 評価結果")
    result = st.session_state.evaluation_result
    
    # 評価スコア表示
    col1, col2 = st.columns(2)
    with col1:
        st.metric("発音", f"{result['pronunciation']}/100")
        st.metric("文法", f"{result['grammar']}/100")
        st.metric("語彙", f"{result['vocabulary']}/100")
    with col2:
        st.metric("意味の一致度", f"{result['meaning']}/100")
        st.metric("総合評価", f"{result['overall']}/100", delta="合格" if result['overall'] >= 70 else "もう少し")
    
    # アドバイス表示
    st.markdown("### アドバイス")
    st.info(result['advice'])
    
    # JSONデータ
    with st.expander("生の評価データ"):
        st.json(result)
    
    # テスト結果
    st.markdown("## テスト結果")
    st.success("✅ 評価機能が正常に動作しました")
    
    # テスト項目
    st.markdown("### テスト項目")
    st.markdown("- [x] 評価リクエストの送信")
    st.markdown("- [x] 評価スコアの取得と表示")
    st.markdown("- [x] アドバイスの生成と表示")
else:
    st.info("「評価実行」ボタンをクリックしてテストを実行してください") 