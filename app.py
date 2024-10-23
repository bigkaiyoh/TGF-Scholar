import streamlit as st
from PIL import Image
from modules.modules import run_assistant, convert_image_to_text, get_secret
from modules.menu import menu, add_footer
from utils.vocabvan import vocabvan_interface
import json
from auth.login_manager import login_user, login_organization, render_login_form, render_org_login_form
from auth.register import register_user
from auth.forgot_password import render_forgot_password_form
from extra_pages.org_dashboard import show_org_dashboard
# from extra_pages.full_dashboard import full_org_dashboard
from extra_pages.claude_dashboard import claude_org_dashboard
from setup.firebase_setup import db
from streamlit_option_menu import option_menu
from datetime import datetime
import pytz


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
if 'organization' not in st.session_state:
    st.session_state.organization = None
if 'feedback' not in st.session_state:
    st.session_state.feedback = None


#Page Configuration
fc = Image.open("src/TGF-Scholar-favicon.png")
st.set_page_config(
    page_title="TGF-Scholar",
    page_icon=fc,
    layout="wide"
)

# Custom CSS for improved styling
st.markdown("""
<style>
    .main-title {
        font-size: 50px;
        text-align: center;
        color: #0097b2;
        margin-bottom: 0px; /* Reduce the gap below the title */
    }
    .catchphrase {
        font-size: 20px;
        text-align: center;
        color: #0097b2;
        margin-top: -10px; /* Reduce the gap above the catchphrase */
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
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 24px;
        background-color: transparent;
        border-radius: 4px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: rgba(0, 151, 178, 0.1);
    }
</style>
""", unsafe_allow_html=True)


def get_input():
    st.subheader("志望動機書")
    txt = st.text_area("こちらに志望動機書を入力してください", height=220, value=st.session_state.txt)
    st.info(f'現在の文字数: {len(txt.split())} 文字')

    # ---------------- Disable File Upload until it is fully available --------------------
    # uploaded_file = st.file_uploader(
    #     "ファイルをアップロードしてください",
    #     type=["pdf", "jpg", "jpeg", "png"],
    #     help="手書きの志望動機書やPDFファイルを評価するためにご利用ください"
    # )
    
    # if uploaded_file is not None and not st.session_state.transcription_done:
    #     # Transcribe the uploaded file
    #     with st.spinner("Reading..."):
    #         try:
    #             result = convert_image_to_text(uploaded_file)
    #             st.session_state.txt = result  # Update session state
    #             st.session_state.transcription_done = True
    #             st.success("Transcription completed successfully!")
    #             st.rerun()
    #         except Exception as e:
    #             st.error(f"An error occurred: {str(e)}")

    return txt

def display_feedback():
    if 'feedback' in st.session_state and st.session_state.feedback:
        st.subheader("AIからのフィードバック")
        st.success("評価が完了しました！")

        # Display feedback in a styled box with background color
        st.markdown(f"""
            <div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; background-color: #e8f4f8;">
                {st.session_state.feedback}
            </div>
        """, unsafe_allow_html=True)


def save_submission(user_id, txt, uni_name, faculty_name, department_name):
    """Save submission to Firestore with necessary fields for the organization dashboard."""
    try:
        user_ref = db.collection('users').document(user_id)
        user_data = user_ref.get().to_dict()

        # Fetch 'org_code' and 'timezone' from the user's data
        org_code = user_data.get('org_code', '')
        user_timezone = user_data.get('timezone', 'UTC')

        # Use timezone-aware datetime for 'submit_time'
        submit_time = datetime.now(pytz.timezone(user_timezone))

        user_ref.collection('submissions').add({
            'text': txt,
            'submit_time': submit_time,
            'university': uni_name,
            'faculty': faculty_name,
            'department': department_name if department_name else "",
            'org_code': org_code,
            'timezone': user_timezone,
            'feedback': st.session_state.feedback
        })
        return True
    except Exception as e:
        print(f"Error saving submission: {e}")
        return False


def main():
    # Display Title with Favicon and Catchphrase using Streamlit's layout
    st.markdown("""
        <h1 class='main-title'>TGF-Scholar</h1>
        <p class='catchphrase'>~Document Your Journey, Define Your Path~</p>
        """, unsafe_allow_html=True)
    
    # Organization Dashboard
    if 'organization' in st.session_state and st.session_state.organization:
        add_footer()
        org = st.session_state.organization
    
        # Decide which dashboard to show based on the 'full_dashboard' setting
        if org.get('full_dashboard', False):
            full_org_dashboard(org)
            claude_org_dashboard(org)
        else:
            show_org_dashboard(org)

    # User Dashboard
    elif 'user' in st.session_state and st.session_state.user:
        user = st.session_state.user
        uni_name = user['university']
        faculty_name = user['faculty']  # Fetching faculty instead of program
        department_name = user.get('department', "")  # Handle missing department

        menu()

        with st.expander("📌使い方", expanded=True):
            st.markdown("""
            1. 志望動機書を入力欄に貼り付けるか直接入力してください。  
            2. 「採点する」ボタンをクリックして、AIによる評価を受けることができます。
            """)

        # Chatbot Button and Popover
        with st.popover("🧠 AIに質問"):
            vocabvan_interface()

        txt = get_input()
        information = f"University: {uni_name}\nFaculty: {faculty_name}\n"
        if department_name:  # Only include department in information if it exists
            information += f"Department: {department_name}\n"
        information += f"\nWriting: {txt}"

        # 提出ボタン
        submit_button = st.button("採点する🚀", type="primary")

        # 評価表示画面
        if submit_button:
            if user['status'] == 'Active':
                # Reset transcription_done and feedback
                st.session_state.transcription_done = False  
                st.session_state.feedback = None

                with st.expander("入力内容", expanded=False):
                    st.write(f"**志望校名**: {uni_name}")
                    st.write(f"**学部名**: {faculty_name}")
                    if department_name:  # Only display department if it exists
                        st.write(f"**学科名**: {department_name}")
                    st.write("**志望動機書**:")
                    
                    # Use markdown to display the text in a styled box
                    box_content = txt.replace('\n', '<br>')
                    st.markdown(f"""
                        <div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; background-color: #f9f9f9;">
                            {box_content}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.write(f'文字数: {len(txt.split())} 文字')
                
                st.session_state.feedback = run_assistant(assistant_id=assistant, txt=information, return_content=True, display_chat=False)
                
                # Save submission using the dedicated function
                save_submission(user['id'], txt, uni_name, faculty_name, department_name)

            else:
                st.error("Your account is inactive. You cannot submit evaluations.")

        #Display feedback
        display_feedback()


    # --------------- Handling Authentication Below -----------------
    else:
        add_footer()
        # Center the content
        _, col, _ = st.columns([1, 2, 1])

        with col:
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
                register_user()

            elif choice == "Login":
                # Create tabs for user and organization login
                user_tab, org_tab = st.tabs(["学生", "教育機関"])
                
                with user_tab:
                    user_id, password, submit_button = render_login_form()
                    forgot_password = st.checkbox("パスワードをお忘れですか？")

                    if forgot_password:
                        render_forgot_password_form()
                    elif submit_button:
                        if user_id and password:
                            user, message = login_user(user_id, password)
                            if user:
                                st.success(message)
                                st.session_state.user = user
                                st.rerun()
                            else:
                                st.error(message)
                        else:
                            st.warning("ユーザーIDとパスワードを入力してください。")
                            
                with org_tab:
                    org_code, org_password, org_submit_button = render_org_login_form()
                    if org_submit_button:
                        if org_code and org_password:
                            org, message = login_organization(org_code, org_password)
                            if org:
                                st.success(message)
                                st.session_state.organization = org
                                st.rerun()
                            else:
                                st.error(message)
                        else:
                            st.warning("Please enter both organization code and password.")

            st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()