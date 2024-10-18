import streamlit as st
from auth.login_manager import logout_user
from setup.firebase_setup import db


if 'user' not in st.session_state:
    st.session_state.user = None

def add_footer():
    footer = """
    <style>
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: transparent;
            color: gray;
            text-align: center;
            padding: 10px;
        }
    </style>
    <div class="footer">
        <p>Powered by <a href="https://nuginy.com" target="_blank" style="color:#0097B2; text-decoration:none;">Nuginy</a></p>
    </div>
    """
    st.markdown(footer, unsafe_allow_html=True)

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
    
def check_sartre_enabled(org_code):
    """Check if Sartre is enabled for the user's organization."""
    try:
        org_ref = db.collection('organizations').document(org_code).get()
        if org_ref.exists:
            org_data = org_ref.to_dict()
            return org_data.get('sartre', False)  # Default to False if Sartre field doesn't exist
        else:
            st.error("Organization not found")
            return False
    except Exception as e:
        st.error(f"Error retrieving Sartre field: {e}")
        return False
    
    

def authenticated_menu():
    # Show a navigation menu for authenticated users
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
        st.write(f"志望校: {uni_name}")
        st.write(f"プログラム: {program_name}")
        st.write(f"在籍機関: {org_name}")  

        if user['status'] == 'Active':
            st.write(f"Days left: {user['days_left']}")
        else:
            st.write("Your account is inactive. Please contact the organization.")

        st.divider()

        st.page_link("app.py", label="TGF-Scholar", icon="🏠")
        st.page_link("pages/Settings.py", label="設定", icon="⚙️")
        
        # Check for Friedrich Sartre Option
        if check_sartre_enabled(user['org_code']):
            st.page_link("pages/Sartre.py", label="サルトルの部屋", icon="💭")

        if st.button("ログアウト"):
            logout_user()
            st.rerun()


def unauthenticated_menu():
    # Show a navigation menu for unauthenticated users
    with st.sidebar:
        st.image("https://nuginy.com/wp-content/uploads/2024/08/TGF-Scholar_HighRes.png",
                 width=190
                 #  use_column_width=True  # Ensures the image uses the full width of the sidebar column
                )    
        st.write("Please Log in")
        st.page_link("app.py", label="Log in", icon="🔑")


def menu():
    # Determine if a user is logged in or not, then show the correct
    # navigation menu
    add_footer()
    

    if st.session_state.user:
        authenticated_menu()

        
    else:
        unauthenticated_menu()
    
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
    