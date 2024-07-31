import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from firebase_setup import db
import pytz
from auth import logout_user

def show_org_dashboard(organization):
    st.markdown("""
    <style>
    .big-font {
        font-size:30px !important;
        font-weight: bold;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"<h1 class='big-font'>Welcome, {organization['org_name']}!</h1>", unsafe_allow_html=True)
    st.markdown(f"**Organization Code:** {organization['org_code']}")

    # Update statuses for users in the specific organization
    update_user_statuses(organization['org_code'])

    users = db.collection('users').where('org_code', '==', organization['org_code']).where('status', '==', 'Active').stream()

    user_data = []
    current_date = datetime.now(pytz.utc)
    registrations_this_month = 0
    active_users = 0

    for user in users:
        user_dict = user.to_dict()
        user_id = user.id
        register_at = user_dict.get('registerAt')
        if isinstance(register_at, datetime):
            register_at = register_at.replace(tzinfo=pytz.utc)
        
        if register_at and register_at.month == current_date.month and register_at.year == current_date.year:
            registrations_this_month += 1

        active_users += 1
        
        expiration_date = register_at + timedelta(days=30) if register_at else None
        
        user_data.append({
            'User ID': user_id,
            'Expiration Date': expiration_date.strftime('%Y-%m-%d') if expiration_date else 'Unknown'
        })

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Registrations This Month", value=registrations_this_month)
    with col2:
        st.metric(label="Active Users", value=active_users)

    st.subheader("Active Users")
    df = pd.DataFrame(user_data)
    
    search = st.text_input("Search users by ID")
    if search:
        df = df[df['User ID'].str.contains(search, case=False)]

    st.dataframe(df.style.set_properties(**{'text-align': 'left'}), use_container_width=True)

    if st.button("Logout", key="logout", help="Click to log out"):
        logout_message = logout_user()
        st.success(logout_message)
        del st.session_state.organization
        st.rerun()

def update_user_statuses(org_code):
    users = db.collection('users').where('org_code', '==', org_code).stream()
    now = datetime.now(pytz.utc)

    for user in users:
        user_ref = db.collection('users').document(user.id)
        user_data = user.to_dict()
        register_at = user_data.get('registerAt')
        if register_at:
            if isinstance(register_at, datetime):
                register_at = register_at.replace(tzinfo=pytz.utc)
            expiration_date = register_at + timedelta(days=30)
            status = 'Active' if now < expiration_date else 'Inactive'
            user_ref.update({'status': status})