import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
from setup.firebase_setup import db

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
def display_org_header(organization):
    st.markdown(f"<h1 class='big-font'>Welcome, {organization['org_name']}!</h1>", unsafe_allow_html=True)
    st.markdown(f"<p><strong>Organization Code:</strong> {organization['org_code']}</p>", unsafe_allow_html=True)

# Fetch user data and update statuses
def get_user_data(org_code):
    """Fetch user data, calculate metrics, and update user statuses if necessary."""
    users_ref = db.collection('users').where('org_code', '==', org_code)
    users = users_ref.stream()
    
    current_date = datetime.now(pytz.utc)
    registrations_this_month = 0
    active_users = 0
    user_data = []
    batch = db.batch()  # Initialize Firestore batch for updates

    for user in users:
        user_dict = user.to_dict()
        user_id = user.id
        register_at = user_dict.get('registerAt')
        
        if isinstance(register_at, datetime):
            register_at = register_at.replace(tzinfo=pytz.utc)

        # Check if the user registered this month
        if register_at and register_at.month == current_date.month and register_at.year == current_date.year:
            registrations_this_month += 1

        # Determine the user's expiration date and status
        expiration_date = register_at + timedelta(days=30) if register_at else None
        status = 'Active' if expiration_date and current_date < expiration_date else 'Inactive'
        
        # If the status has changed, update it in Firestore using batch
        if status != user_dict.get('status'):
            user_ref = db.collection('users').document(user_id)
            batch.update(user_ref, {'status': status})

        # Only add active users to the data list
        if status == 'Active':
            active_users += 1

            # Calculate total submissions and today's submissions
            submission_ref = db.collection('users').document(user_id).collection('submissions').stream()
            total_submissions = 0
            todays_submissions = 0
            today = datetime.now(pytz.utc).date()  # Today's date in UTC

            for submission in submission_ref:
                sub_data = submission.to_dict()
                submit_time = sub_data.get('submit_time')
                if submit_time:
                    submit_time = submit_time.replace(tzinfo=pytz.utc)
                    total_submissions += 1
                    if submit_time.date() == today:
                        todays_submissions += 1

            user_data.append({
                'User ID': user_id,
                'registerAt': register_at.strftime('%Y-%m-%d') if register_at else 'Unknown',
                'Expiration Date': expiration_date.strftime('%Y-%m-%d') if expiration_date else 'Unknown',
                'total_submission': total_submissions,
                'todays_submission': todays_submissions,
            })

    # Commit all updates to Firestore at once
    batch.commit()

    return user_data, registrations_this_month, active_users



def display_active_users_table(user_data):
    st.subheader("Active Users")
    df = pd.DataFrame(user_data)
    
    if df.empty:
        st.info("No users found.")
    else:
        st.dataframe(df.style.set_properties(**{'text-align': 'left'}).highlight_max(subset=['total_submission'], color='#e6f3ff'), use_container_width=True)
