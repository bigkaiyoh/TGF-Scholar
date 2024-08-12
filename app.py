import streamlit as st
from PIL import Image
from modules import run_assistant, convert_image_to_text, get_secret
from vocabvan import vocabvan_interface
import json
from auth import register_user, login_user, logout_user, login_organization
from extra_pages.organization_dashboard import show_org_dashboard
from firebase_setup import db
from streamlit_option_menu import option_menu
from datetime import datetime


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

def get_org_name(org_code):
    try:
        org_ref = db.collection('organizations').document(org_code).get()
        if org_ref.exists:
            org_data = org_ref.to_dict()
            return org_data.get('org_name', 'Organization not found')
        else:
            return 'Organization not found'
    except Exception as e:
        st.error(f"Error retrieving organization name: {e}")
        return 'Error occurred'

def save_submission(user_id, txt, uni_name, program_name):
    try:
        user_ref = db.collection('users').document(user_id)
        user_ref.collection('submissions').add({
            'text': txt,
            'submit_time': datetime.now(),
            'university': uni_name,
            'program': program_name
        })
        return True
    except Exception as e:
        print(f"Error saving submission: {e}")
        return False

def main():
    # Display Title with Favicon and Catchphrase using Streamlit's layout
    st.markdown("""
        <h1 class='main-title'>TGF-Scholar</h1>
        <p class='catchphrase'>Document Your Journey, Define Your Path</p>
        """, unsafe_allow_html=True)
    
    # Organization Dashboard
    if 'organization' in st.session_state and st.session_state.organization:
        # Redirect to the organization dashboard page
        show_org_dashboard(st.session_state.organization)

    # User Dashboard
    elif 'user' in st.session_state and st.session_state.user:
        user = st.session_state.user
        uni_name = user['university']
        program_name = user['program']
        org_name = get_org_name(user['org_code'])


        with st.sidebar:
            st.image("https://nuginy.com/wp-content/uploads/2024/08/TGF-Scholar_HighRes.png",
                     width=190
                    #  use_column_width=True  # Ensures the image uses the full width of the sidebar column
                    )       
            st.write(f"Welcome back, {user['id']}!")
            st.write(f"University: {uni_name}")
            st.write(f"Program: {program_name}")
            st.write(f"Organization: {org_name}")
        
            if user['status'] == 'Active':
                st.write(f"Days left: {user['days_left']}")
            else:
                st.write("Your account is inactive. Please contact the organization.")

            if st.button("Logout"):
                message = logout_user()
                st.success(message)
                st.rerun()

        with st.expander("📌使い方", expanded=True):
            st.markdown("""
            1. 志望動機書を入力欄に貼り付けるか直接入力してください。  
            (ファイルをアップロードで手書き文章やPDFの添削も行えます)  
            2. 「採点する」ボタンをクリックして、AIによる評価を受けてください。
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
            if user['status'] == 'Active':
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

                # Save submission using the dedicated function
                save_submission(user['id'], txt, uni_name, program_name)
            else:
                st.error("Your account is inactive. You cannot submit evaluations.")


    # --------------- Handling Authentication Below -----------------
    else:
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
                with st.form("register_form"):
                    st.subheader("Create an Account")
                    user_id = st.text_input("User ID", placeholder="Enter a unique user ID")
                    email = st.text_input("Email", placeholder="Enter your email")
                    password = st.text_input("Password", type="password", placeholder="Enter a strong password")
                    university = st.text_input("University you're applying to", placeholder="Enter the university you're applying to")
                    program = st.text_input("Program you're applying to", placeholder="Enter the program you're applying to")
                    org_code = st.text_input("Organization Code", placeholder="Enter your organization code")
                    submit_button = st.form_submit_button("Register", use_container_width=True)

                    if submit_button:
                        if user_id and email and password and university and program and org_code:
                            user_data, message = register_user(user_id, email, password, university, program, org_code)
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
                    user_id = st.text_input("User ID", placeholder="Enter your user ID")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                    submit_button = st.form_submit_button("Login", use_container_width=True)

                    if submit_button:
                        if user_id and password:
                            user, message = login_user(user_id, password)
                            if user:
                                st.success(message)
                                st.session_state.user = user
                                st.rerun()
                            else:
                                st.error(message)
                        else:
                            st.warning("Please enter both user ID and password.")

                # Organization Login
                st.markdown("<hr>", unsafe_allow_html=True)
                st.subheader("Organization Login")
                with st.form("org_login_form"):
                    org_code = st.text_input("Organization Code", placeholder="Enter your organization code")
                    org_password = st.text_input("Password", type="password", placeholder="Enter your organization password")
                    org_submit_button = st.form_submit_button("Login as Organization", use_container_width=True)

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