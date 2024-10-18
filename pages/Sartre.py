import streamlit as st
from modules.modules import run_assistant, get_secret
from modules.menu import menu

if 'user' not in st.session_state:
    st.session_state.user = None

def chat_with_sartre():
    menu()
    secrets = get_secret()
    assistant = secrets['Friedrich_Sartre']

    # Title
    st.markdown("<h1 style='text-align: center; font-size: 3rem;'>Friedrich Sartreの部屋</h1>", unsafe_allow_html=True)
    
    # Explanatory text
    st.markdown("""
    <p style="text-align: center; font-size: 1.2rem; color: #555;">
    Friedrich Sartreは、あなたに理解があり博識な哲学者です。彼に素直な思いを相談しながら、志望動機書に役立つ重要な視点を得ることができます。<br>
    哲学的な問いかけや反応を通して、あなたの価値観や目標を掘り下げ、明確にしましょう。
    </p>
    """, unsafe_allow_html=True)


    # ---------- APP BEGINS --------------
    user_input = st.chat_input("受験や進路に関する悩みを相談してください")

    temporary = st.empty()
    t = temporary.container()

    with t:
        st.write("自己理解を深め、大学選びや将来設計を考える際の対話にご利用ください。サルトルの哲学的視点を通じて、新しいアイデアや気づきを提供します。")

        m1 = st.chat_message("user")
        m1.write(""" 例
1. 自分の強みが何かわかりません
2. 将来の選択について迷っています。自分に合った学問分野はどうやって見つかるのでしょうか。 """)

    if user_input:
        temporary.empty()
        # Pass custom names for user and assistant
        run_assistant(assistant_id=assistant, txt=user_input, assistant_name="ai")

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
