import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
from setup.firebase_setup import db
from modules.modules import convert_to_timezone

# Custom CSS for styling the dashboard
def apply_custom_css():
    st.markdown("""
    <style>
    .big-font {
        font-size: 2.5rem !important;
        font-weight: 600 !important;
        color: #F39200 !important;
        margin-bottom: 0.5rem !important;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    }
    .metric-label {
        font-size: 1rem;
        color: #555;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1E88E5;
    }
    .stButton>button {
        width: 100%;
        background-color: #1E88E5;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# Display header for the organization
def display_org_header():
    organization = st.session_state.organization
    st.markdown(f"<h1 class='big-font'>{organization['org_name']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p><strong>教育機関コード:</strong> {organization['org_code']}</p>", unsafe_allow_html=True)

# Fetch user data and update statuses
def get_user_data():
    """Fetch user data, calculate metrics, and update user statuses if necessary."""
    organization = st.session_state.organization
    org_code = organization['org_code']
    admin_timezone_str = organization.get('timezone', 'UTC')
    
    users_ref = db.collection('users').where('org_code', '==', org_code)
    users = users_ref.stream()

    # Get the current date in admin's timezone
    current_date_in_admin_timezone = convert_to_timezone(datetime.now(pytz.utc), admin_timezone_str)

    registrations_this_month = 0
    active_users = 0
    user_data = []
    batch = db.batch()  # Initialize Firestore batch for updates

    for user in users:
        user_dict = user.to_dict()
        user_id = user.id
        register_at = user_dict.get('registerAt')
        
        # Convert registration date to admin's timezone
        if isinstance(register_at, datetime):
            register_at = convert_to_timezone(register_at, admin_timezone_str)

        # Check if the user registered this month in admin's timezone
        if register_at and register_at.month == current_date_in_admin_timezone.month and register_at.year == current_date_in_admin_timezone.year:
            registrations_this_month += 1

        # Determine the user's expiration date and status, converting to admin's timezone
        expiration_date = register_at + timedelta(days=30) if register_at else None
        status = 'Active' if expiration_date and current_date_in_admin_timezone < expiration_date else 'Inactive'
        
        # If the status has changed, update it in Firestore using batch
        if status != user_dict.get('status'):
            user_ref = db.collection('users').document(user_id)
            batch.update(user_ref, {'status': status})

        # Only add active users to the data list
        if status == 'Active':
            active_users += 1

            # Calculate total submissions and today's submissions in admin's timezone
            submission_ref = db.collection('users').document(user_id).collection('submissions').stream()
            total_submissions = 0
            todays_submissions = 0
            today_in_admin_timezone = current_date_in_admin_timezone.date()  # Admin's local date

            for submission in submission_ref:
                sub_data = submission.to_dict()
                submit_time = sub_data.get('submit_time')

                if submit_time:
                    submit_time = convert_to_timezone(submit_time, admin_timezone_str)
                    total_submissions += 1
                    if submit_time.date() == today_in_admin_timezone:
                        todays_submissions += 1

            user_data.append({
                'User ID': user_id,
                'registerAt': register_at.strftime('%Y-%m-%d') if register_at else '不明',
                'Expiration Date': expiration_date.strftime('%Y-%m-%d') if expiration_date else '不明',
                'total_submission': total_submissions,
                'todays_submission': todays_submissions,
            })

    # Commit all updates to Firestore at once
    batch.commit()

    return user_data, registrations_this_month, active_users

def display_active_users_table(user_data):
    st.subheader("アクティブユーザー")
    df = pd.DataFrame(user_data)
    
    if df.empty:
        st.info("ユーザーが見つかりませんでした。")
    else:
        # Add search functionality
        search_term = st.text_input("🔍 ユーザーを検索", "")
        
        if search_term:
            # Filter users based on the search term (case-insensitive)
            df = df[df['User ID'].str.contains(search_term, case=False, na=False)]
        
        # Rename columns to Japanese
        df.rename(columns={
            'User ID': 'ユーザーID',
            'registerAt': '登録日',
            'Expiration Date': '有効期限',
            'total_submission': '総提出数',
            'todays_submission': '本日の提出数'
        }, inplace=True)
        st.dataframe(
            df.style.set_properties(**{'text-align': 'left'}).highlight_max(subset=['総提出数'], color='#e6f3ff'),
            use_container_width=True
        )
