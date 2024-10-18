import streamlit as st
from modules.modules import run_assistant, get_secret
from modules.menu import menu

def chat_with_sartre():
    menu()
    secrets = get_secret()
    assistant = secrets['Friedrich_Sartre']

    user_input = st.chat_input("受験や進路に関する悩みを相談してください")

    temporary = st.empty()
    t = temporary.container()

    with t:
        st.write("自己理解を深め、大学選びや将来設計を考える際の対話にご利用ください。サルトルの哲学的視点を通じて、新しいアイデアや気づきを提供します。")

        m1 = st.chat_message("あなた")
        m1.write(""" 例
1. 自分の強みが何かわかりません
2. 将来の選択について迷っています。自分に合った学問分野はどうやって見つかるのでしょうか。 """)

    if user_input:
        temporary.empty()
        # Pass custom names for user and assistant
        run_assistant(assistant_id=assistant, txt=user_input, user_name="あなた", assistant_name="Friedrich Sartre")

    return user_input


if __name__ == "__main__":
    # Custom CSS with updated hover color
    st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #0097B2;
        color: white;
        padding: 10px 24px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #007A8F;
    }
    </style>
    """, unsafe_allow_html=True)

    chat_with_sartre()
