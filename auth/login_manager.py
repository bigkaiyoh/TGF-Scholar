import streamlit as st
from firebase_admin import firestore
import bcrypt
from setup.firebase_setup import db
from datetime import datetime
import pytz

# Render the user login form
def render_login_form():
    """Renders the login form UI and returns the inputs."""
    with st.form("login_form"):
        st.subheader("ログイン")
        user_id = st.text_input("ユーザーID", placeholder="ユーザーIDを入力してください")
        password = st.text_input("パスワード", type="password", placeholder="パスワードを入力してください")
        submit_button = st.form_submit_button("ログイン", use_container_width=True)
    
    return user_id, password, submit_button

# Render the organization login form
def render_org_login_form():
    """Renders the organization login form UI and returns the inputs."""
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("教育機関ログイン")
    with st.form("org_login_form"):
        org_code = st.text_input("教育機関コード", placeholder="教育機関コードを入力してください")
        org_password = st.text_input("パスワード", type="password", placeholder="教育機関のパスワードを入力してください")
        org_submit_button = st.form_submit_button("教育機関としてログイン", use_container_width=True)
    
    return org_code, org_password, org_submit_button

# User login logic
def login_user(user_id, password):
    """Handles user login authentication with Firestore."""
    try:
        user_ref = db.collection('users').document(user_id).get()
        if not user_ref.exists:
            return None, "無効なIDまたはパスワードです"
        
        user_data = user_ref.to_dict()
        if bcrypt.checkpw(password.encode(), user_data['password'].encode()):
            # Check if the user is still within the 30-day active period
            register_at = user_data.get('registerAt')
            if register_at is None:
                return None, "登録日が見つかりません"
            
            register_at = register_at.replace(tzinfo=pytz.utc)
            status, days_left = check_user_status(register_at)

            # Update user status in the database only if it has changed
            if status != user_data['status']:
                db.collection('users').document(user_id).update({'status': status})
            
            return {
                "id": user_id,
                "email": user_data['email'],
                "university": user_data['university'],
                "program": user_data['program'],
                "org_code": user_data['org_code'],
                'timezone': user_data['timezone'],
                "status": status,
                "days_left": days_left
            }, "ログインに成功しました"
        else:
            return None, "無効なIDまたはパスワードです"
    except Exception as e:
        return None, f"ログインに失敗しました: {str(e)}"

# Check if the user is still active
def check_user_status(register_at):
    """Calculates the user's status based on the registration date."""
    now = datetime.now(pytz.utc)  # Use UTC timezone-aware datetime
    days_passed = (now - register_at).days
    if days_passed <= 30:
        return 'Active', 30 - days_passed
    else:
        return 'Inactive', 0

# Logout the user
def logout_user():
    """Logs out the user by clearing session state."""
    if 'user' in st.session_state:
        del st.session_state['user']
    return "ログアウトに成功しました"

# Organization login logic
def login_organization(org_code, password):
    """Handles organization login authentication with Firestore."""
    try:
        org_ref = db.collection('organizations').document(org_code).get()
        if not org_ref.exists:
            return None, "無効な教育機関コードまたはパスワードです"

        org_data = org_ref.to_dict()
        # Direct comparison for organization password (consider using hashed password for production)
        if org_data['password'] == password:
            return {
                "org_code": org_code,
                "org_name": org_data['org_name'],
                'timezone': org_data['timezone'],
                'full_dashboard': org_data.get('full_dashboard', False)
            }, "教育機関としてのログインに成功しました"
        else:
            return None, "無効な教育機関コードまたはパスワードです"
    except Exception as e:
        return None, f"教育機関ログインに失敗しました: {str(e)}"

# Logout the organization
def logout_org():
    """Logs out the organization by clearing session state."""
    if 'organization' in st.session_state:
        del st.session_state['organization']
    return "教育機関のログアウトに成功しました"
