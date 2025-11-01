import streamlit as st
import google.generativeai as genai

st.title("💬 Chatbot (Gemini)")
st.write(
    "This is a simple chatbot that uses Google Gemini (Generative AI). "
    "Provide a Gemini API key and choose a model. "
    "You can get an API key from Google AI Studio or Google Cloud Console."
)

# --- パッケージインストールの確認 ---
if genai is None:
    st.error(
        "The `google-generativeai` package is not installed. Install it with:\n"
        "`pip install google-generativeai`",
        icon="🚨",
    )
else:
    # --- 1. APIキーとモデルの選択 ---
    gemini_api_key = st.text_input("Gemini / Google API Key", type="password")
    
    # モデルの選択肢を更新 (Geminiモデルと古いPaLMモデル)
    model = st.selectbox(
        "Model",
        options=[
            "gemini-1.5-pro-latest",
            "gemini-pro",
            "models/chat-bison-001", # PaLM 2 (Legacy)
        ],
        index=0,
        help="Choose the model. 'gemini-1.5-pro-latest' or 'gemini-pro' is recommended.",
    )

    if not gemini_api_key:
        st.info("Please add your Gemini / Google API key to continue.", icon="🗝️")
    else:
        try:
            # APIキーを設定
            genai.configure(api_key=gemini_api_key)
        except Exception as e:
            st.error(f"Failed to configure API key: {e}", icon="🔥")
            st.stop() # APIキー設定に失敗したら停止

        # --- 2. セッションステートの初期化 ---
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # --- 3. 過去のメッセージの表示 ---
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # --- 4. チャット入力とAPI呼び出し ---
        if prompt := st.chat_input("What is up?"):
            # ユーザーメッセージをセッションステートとUIに追加
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            try:
                # --- ここからが修正されたAPI呼び出しロジック ---

                # 1. APIに渡すための履歴を作成
                # (Gemini SDKは 'assistant' ではなく 'model' というロール名を要求します)
                api_history = []
                for msg in st.session_state.messages[:-1]: # 最後の(今入力された)メッセージ以外
                    role = "model" if msg["role"] == "assistant" else msg["role"]
                    api_history.append({"role": role, "parts": [msg["content"]]})

                # 2. モデルとチャットセッションを初期化
                chat_model = genai.GenerativeModel(model)
                chat_session = chat_model.start_chat(history=api_history)

                # 3. 生成設定 (temperatureなど)
                generation_config = genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=512,
                )

                # 4. (同期)ストリーミングなしでメッセージを送信
                #    (ストリーミングが必要な場合は chat_session.send_message_async を使います)
                response = chat_session.send_message(
                    prompt, # 現在のユーザープロンプト
                    generation_config=generation_config
                )

                # 5. レスポンスのテキストを取得 (非常にシンプル)
                assistant_text = response.text

                # ----------------------------------------------

            except Exception as e:
                # APIリクエスト失敗時のエラー表示
                st.error(f"API request failed: {e}")
                # 失敗した場合、最後のユーザーメッセージを履歴から削除する (オプション)
                # st.session_state.messages.pop() 
            else:
                # 成功した場合、アシスタントの応答を表示
                with st.chat_message("assistant"):
                    st.markdown(assistant_text)
                
                # アシスタントの応答をセッションステートに保存
                st.session_state.messages.append({"role": "assistant", "content": assistant_text})
