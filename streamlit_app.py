import streamlit as st
import requests

# タイトルと説明の表示
st.title("💬 Claude チャットボット")
st.write("このシンプルなチャットボットは、Anthropic の Claude API を利用して応答を生成します。")

# Streamlit Community CloudのSecretsからAPIキーを取得
# .streamlit/secrets.toml に CLAUDE_API_KEY = "YOUR_API_KEY" を設定してください
claude_api_key = st.secrets.get("CLAUDE_API_KEY")

if not claude_api_key:
    st.info("Streamlit Community CloudのSecretsに `CLAUDE_API_KEY` を設定してください。", icon="🗝️")
else:
    # ユーザーがモデルを選択できるようにする
    # 使用可能な Claude モデル名に更新
    model_name = st.selectbox(
        "使用する Claude モデルを選択",
        (
            "claude-sonnet-4-5",
            "claude-haiku-4-5"      
        )
    )
 
    st.write(f"現在のモデル: **{model_name}**")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 既存のチャットメッセージを表示
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # ユーザーがメッセージを入力するためのチャット入力フィールド
    if prompt := st.chat_input("ここにメッセージを入力"):

        # ユーザーのプロンプトを保存・表示
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
    
            st.markdown(prompt)

        # Claude Messages API用にメッセージ形式を準備
        # Claude APIのロールは 'user' または 'assistant'
        claude_messages = []
        for m in st.session_state.messages:
            # Claudeでは 'model' の代わりに 'assistant' を使用
            api_role = "user" if m["role"] == "user" else "assistant"
            claude_messages.append(
                {
                    "role": api_role,
                    "content": m["content"] # Claude APIでは 'parts' ではなく 'content' に直接テキストを渡す
                }
            )

        # APIキーを含まないクリーンなURLを定義
        # Claude Messages APIのエンドポイント
        api_url = "https://api.anthropic.com/v1/messages" 

        # ヘッダーに Content-Type と APIキー、および Anthropic のバージョンを含める
        headers = {
            "content-type": "application/json",
            "x-api-key": claude_api_key, 
            "anthropic-version": "2023-06-01" 
        }
        
        # Claude Messages APIのデータ構造
        data = {
            "model": model_name,
            "messages": claude_messages,
            "max_tokens": 4096, # Claude APIでは必須。適切な値を設定 (例: 4096)
            "temperature": 0.7,
        }

        try:
            # アシスタントの応答をチャットメッセージコンテナ内に表示
            with st.chat_message("assistant"):
             
                with st.spinner(f"{model_name} が応答を生成中..."):
                    response = requests.post(api_url, headers=headers, json=data, timeout=60) # タイムアウトを長めに設定
                    response.raise_for_status() # HTTPエラーがあれば例外を発生
                    
                    result = response.json()
      
                    # APIからのレスポンス構造のチェックと応答の取得
                    # Claude Messages APIの応答形式に合わせた変更
                    if "content" in result and result["content"] and result["content"][0]["type"] == "text":
                        claude_reply = result["content"][0]["text"]
                    elif "error" in result:
                        claude_reply = f"Claude APIエラーが発生しました: {result['error']['message']}"
                    else:
                        # その他の予期しない応答形式
                        claude_reply = f"エラー: 予期しないAPI応答形式です。詳細: {result}"
            
                st.markdown(claude_reply)
            
            # アシスタントの応答をセッションステートに保存
            st.session_state.messages.append({"role": "assistant", "content": claude_reply})

        except requests.exceptions.RequestException as e:
            error_message = f"APIリクエストエラーが発生しました: {e}"
            st.error(error_message)
            st.session_state.messages.append({"role": "assistant", 
                "content": error_message})
        except Exception as e:
            error_message = f"予期せぬエラーが発生しました: {e}"
            st.error(error_message)
            st.session_state.messages.append({"role": "assistant", "content": error_message})
