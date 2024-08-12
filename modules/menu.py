import streamlit as st
from auth import logout_user
from firebase_setup import db


if 'user' not in st.session_state:
    st.session_state.user = None

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
        st.write(f"University: {uni_name}")
        st.write(f"Program: {program_name}")
        st.write(f"Organization: {org_name}")  

        if st.button("Home"):
            st.switch_page("app.py")
        st.page_link("pages/Settings.py", label="Settings", icon="⚙️")
        if st.button("Logout"):
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


def menu():
    # Determine if a user is logged in or not, then show the correct
    # navigation menu
    
    

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
    