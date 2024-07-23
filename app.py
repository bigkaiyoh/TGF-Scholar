import streamlit as st
from modules import run_assistant, convert_image_to_text, get_secret
from vocabvan import vocabvan_interface
import json
from auth import register_user, login_user, logout_user
from firebase_setup import db
from streamlit_option_menu import option_menu


# Initialize assistant
secrets = get_secret()
assistant = secrets['Unicke_id']

# Initialize session state
if 'txt' not in st.session_state:
    st.session_state.txt = ""
if 'transcription_done' not in st.session_state:
    st.session_state.transcription_done = False
if 'user' not in st.session_state:
    st.session_state.user = None

st.set_page_config(
    page_title="英語志望動機書対策ニッケ",
    page_icon="🎓",
    layout="wide"
)

# Custom CSS for improved styling
st.markdown("""
<style>
    .main-title {
        font-size: 50px;
        text-align: center;
        color: #0097b2;
    }
    .stButton>button {
        width: 100%;
    }
    .auth-form {
        background-color: #f0f8ff;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)


def get_input():
    st.subheader("志望動機書")
    txt = st.text_area("こちらに志望動機書を入力してください", height=220, value=st.session_state.txt)
    st.info(f'現在の文字数: {len(txt.split())} 文字')

    uploaded_file = st.file_uploader(
        "ファイルをアップロードしてください",
        type=["pdf", "jpg", "jpeg", "png"],
        help="手書きの志望動機書やPDFファイルを評価するためにご利用ください"
    )
    
    if uploaded_file is not None and not st.session_state.transcription_done:
        # Transcribe the uploaded file
        with st.spinner("Reading..."):
            try:
                result = convert_image_to_text(uploaded_file)
                st.session_state.txt = result  # Update session state
                st.session_state.transcription_done = True
                st.success("Transcription completed successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    return txt


def main():
    st.markdown("<h1 class='main-title'>🎓 英語志望動機書対策ニッケ</h1>", unsafe_allow_html=True)
    st.info("このアプリは、あなたの英語の志望動機書を評価し、フィードバックを提供します。")

    # Authentication
    if 'user' not in st.session_state or st.session_state.user is None:
        choice = option_menu(
            menu_title=None,
            options=["Login", "Register"],
            icons=["box-arrow-in-right", "person-plus"],
            menu_icon="cast",
            default_index=0,
            orientation="horizontal",
        )

        st.markdown("<div class='auth-form'>", unsafe_allow_html=True)

        if choice == "Register":
            with st.form("register_form"):
                st.subheader("Create an Account")
                email = st.text_input("Email", placeholder="Enter your email")
                password = st.text_input("Password", type="password", placeholder="Enter a strong password")
                university = st.text_input("University", placeholder="Enter your university")
                program = st.text_input("Program", placeholder="Enter your program")
                submit_button = st.form_submit_button("Register", use_container_width=True)

                if submit_button:
                    if email and password and university and program:
                        user_data, message = register_user(email, password, university, program)
                        if user_data:
                            st.success(message)
                            st.session_state.user = user_data
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.warning("Please fill in all fields.")

        elif choice == "Login":
            with st.form("login_form"):
                st.subheader("Login to Your Account")
                email = st.text_input("Email", placeholder="Enter your email")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submit_button = st.form_submit_button("Login", use_container_width=True)

                if submit_button:
                    if email and password:
                        user, message = login_user(email, password)
                        if user:
                            st.success(message)
                            st.session_state.user = user
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.warning("Please enter both email and password.")

        st.markdown("</div>", unsafe_allow_html=True)

    else:
        user = st.session_state.user
        uni_name = user['university']
        program_name = user['program']

        with st.sidebar:
            st.write(f"Welcome, {user['email']}!")
            st.write(f"University: {uni_name}")
            st.write(f"Program: {program_name}")
            if st.button("Logout"):
                message = logout_user()
                st.success(message)
                st.rerun()

        with st.expander("📌使い方", expanded=True):
            st.markdown("""
            1. 志望校名と学部名を入力してください。
            2. 志望動機書を入力欄に貼り付けるか直接入力してください。  
            (ファイルをアップロードで手書き文章やPDFの添削も行えます)  
            3. 「採点する」ボタンをクリックして、AIによる評価を受けてください。
            """)

        # Chatbot Button and Popover
        with st.popover("🧠 AIに質問"):
            vocabvan_interface()

        txt = get_input()
        information = f"University: {uni_name}\nProgram: {program_name}\n\nWriting: {txt}"
        
        # 提出ボタン
        submit_button = st.button("採点する🚀", type="primary")

        # 評価表示画面
        if submit_button:
            # Reset transcription_done to False
            st.session_state.transcription_done = False  

            with st.expander("入力内容", expanded=False):
                st.write(f"**志望校名**: {uni_name}")
                st.write(f"**学部名**: {program_name}")
                st.write("**志望動機書**:")
                
                # Use markdown to display the text in a styled box
                box_content = txt.replace('\n', '<br>')
                st.markdown(f"""
                    <div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; background-color: #f9f9f9;">
                        {box_content}
                    </div>
                """, unsafe_allow_html=True)
                
                st.write(f'文字数: {len(txt.split())} 文字')
            
            st.subheader("AIからのフィードバック")
            feedback = run_assistant(assistant_id=assistant, txt=information, return_content=True, display_chat=False)
            st.success("評価が完了しました！")

            # Display feedback in a styled box with background color
            st.markdown(f"""
                <div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; background-color: #e8f4f8;">
                    {feedback}
                </div>
            """, unsafe_allow_html=True)



if __name__ == "__main__":
    main()