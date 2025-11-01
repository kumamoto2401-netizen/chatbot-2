import streamlit as st

# This implementation uses Google's Generative AI (Gemini) via the
# `google-generativeai` package. Install with:
#   pip install google-generativeai
#
# Notes:
# - You can use an API key (recommended for quick tests) by entering it below.
# - If you're using Google Cloud service account credentials / application
#   default credentials, you can adapt the auth flow accordingly.
#
# If you want streaming support (token-by-token), tell me and I can update
# the example to use streaming endpoints (and adjust UI accordingly).


try:
    import google.generativeai as genai
except Exception:
    genai = None

st.title("💬 Chatbot (Gemini)")
st.write(
    "This is a simple chatbot that uses Google Gemini (Generative AI). "
    "Provide a Gemini API key (or Google API key) and choose a model. "
    "You can get an API key from Google Cloud Console and enable the "
    "Generative AI API / Vertex AI if necessary."
)

if genai is None:
    st.error(
        "The `google-generativeai` package is not installed. Install it with:\n"
        "`pip install google-generativeai`",
        icon="🚨",
    )
else:
    gemini_api_key = st.text_input("Gemini / Google API Key", type="password")
    model = st.selectbox(
        "Model",
        options=[
            # Common names — update if you need a specific Gemini model name.
            # Examples: "models/chat-bison-001", "models/text-bison-001", "models/gemini-1.5"
            "models/chat-bison-001",
        ],
        index=0,
        help="Choose the model name. Use the exact model id you have access to.",
    )

    if not gemini_api_key:
        st.info("Please add your Gemini / Google API key to continue.", icon="🗝️")
    else:
        # Configure the client with the provided API key.
        # genai.configure accepts api_key for simple API-key based auth.
        genai.configure(api_key=gemini_api_key)

        # session messages: each message is {"role": "user"/"assistant", "content": "..."}
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # render previous messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("What is up?"):
            # show user message immediately
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Build messages in the format the Gemini chat API expects.
            # Each message: {"author": "user"|"assistant", "content": [{"type":"text","text":"..."}]}
            api_messages = []
            for m in st.session_state.messages:
                api_messages.append(
                    {
                        "author": m["role"],
                        "content": [{"type": "text", "text": m["content"]}],
                    }
                )

            # Call the chat.create endpoint (synchronous).
            # If you need streaming, ask and I will add streaming support.
            try:
                response = genai.chat.create(
                    model=model,
                    messages=api_messages,
                    temperature=0.2,
                    max_output_tokens=512,
                )
            except Exception as e:
                st.error(f"API request failed: {e}")
                # keep conversation state as-is
            else:
                # Extract text from the response robustly.
                def extract_text(resp):
                    # preferred attribute (library may provide .output_text)
                    try:
                        text = getattr(resp, "output_text", None)
                        if text:
                            return text
                    except Exception:
                        pass

                    # try candidates structure
                    try:
                        candidates = getattr(resp, "candidates", None)
                        if candidates and len(candidates) > 0:
                            # candidates[0].content is usually a list of dicts
                            content = candidates[0].get("content", [])
                            out_texts = []
                            for c in content:
                                if isinstance(c, dict) and c.get("type") == "text":
                                    t = c.get("text")
                                    if t:
                                        out_texts.append(t)
                            if out_texts:
                                return "\n".join(out_texts)
                    except Exception:
                        pass

                    # fallback to dict-like parsing
                    try:
                        if isinstance(resp, dict):
                            cand = resp.get("candidates", [])
                            if cand:
                                cont = cand[0].get("content", [])
                                texts = []
                                for c in cont:
                                    if c.get("type") == "text":
                                        t = c.get("text")
                                        if t:
                                            texts.append(t)
                                if texts:
                                    return "\n".join(texts)
                            # some responses include output[0].content[0].text
                            output = resp.get("output", {})
                            if isinstance(output, dict):
                                maybe_text = output.get("text")
                                if maybe_text:
                                    return maybe_text
                    except Exception:
                        pass

                    # final fallback
                    try:
                        return str(resp)
                    except Exception:
                        return "<no text in response>"

                assistant_text = extract_text(response)

                # display assistant message
                with st.chat_message("assistant"):
                    st.markdown(assistant_text)

                # save to session state
                st.session_state.messages.append({"role": "assistant", "content": assistant_text})
