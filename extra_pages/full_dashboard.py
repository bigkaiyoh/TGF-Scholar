import streamlit as st
import pandas as pd
import pytz
from firebase_admin import firestore
from .dashboard_common import apply_custom_css, display_org_header, get_user_data, display_active_users_table
from auth.login_manager import logout_org
from datetime import datetime
from setup.firebase_setup import db



def fetch_submission_data(users_data):
    """Fetch submission data for users."""
    submissions = []
    for user in users_data:
        user_id = user['User ID']
        try:
            submission_ref = db.collection('users').document(user_id).collection('submissions').stream()
            for submission in submission_ref:
                sub_data = submission.to_dict()
                sub_data.update({
                    'user_id': user_id,
                    'timestamp': sub_data.get('submit_time'),
                    'date': sub_data.get('submit_time').date() if sub_data.get('submit_time') else None
                })
                submissions.append(sub_data)
        except Exception as e:
            st.error(f"Error fetching submissions for user {user_id}: {str(e)}")
    return pd.DataFrame(submissions)

# Display full metrics (for full dashboard view)
def display_full_metrics(registrations_this_month, active_users, todays_submissions, todays_users):
    col1, col2, col3, col4 = st.columns(4)
    metrics = [
        ("Today's Submissions", todays_submissions),
        ("Today's Active Students", todays_users),
        ("Monthly Signups", registrations_this_month),
        ("Active Users", active_users)
    ]
    
    for i, (label, value) in enumerate(metrics):
        with [col1, col2, col3, col4][i]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
            </div>
            """, unsafe_allow_html=True)

# Display detailed user info (for full dashboard)
def display_detailed_user_info(user_data):
    """Display detailed user information with a clickable submission history."""
    st.subheader("Active Users")
    df = pd.DataFrame(user_data)
    
    selected_user_id = st.selectbox("Select User ID to View Submission History", df['User ID'].tolist())
    
    if selected_user_id:
        st.write(f"Selected User: {selected_user_id}")
    
    st.dataframe(df.style.set_properties(**{'text-align': 'left'}), use_container_width=True)
    
    return selected_user_id

# Display submission history for a user
def display_submission_history(user_id):
    st.subheader(f"Submission History for {user_id}")
    
    try:
        submissions_ref = db.collection('users').document(user_id).collection('submissions')
        submissions = submissions_ref.order_by('submit_time', direction=firestore.Query.DESCENDING).stream()

        university = ""
        program = ""
        submission_data = []

        for submission in submissions:
            submission_dict = submission.to_dict()
            if not university and not program:
                university = submission_dict.get('university', '')
                program = submission_dict.get('program', '')

            submission_data.append({
                "Submission Date": submission_dict.get('submit_time').strftime('%Y-%m-%d %H:%M:%S') if submission_dict.get('submit_time') else 'Unknown',
                "Submission Text": submission_dict.get('text', '')
            })

        st.markdown(f"**University:** {university}")
        st.markdown(f"**Program:** {program}")
        
        if submission_data:
            df = pd.DataFrame(submission_data)
            st.dataframe(df.style.set_properties(**{'text-align': 'left', 'white-space': 'pre-wrap'}).set_table_styles([{'selector': 'th', 'props': [('text-align', 'left')]}]), use_container_width=True)
        else:
            st.info("No submissions found for this user.")
    except Exception as e:
        st.error(f"Error fetching submission history: {str(e)}")


def full_org_dashboard(organization):
    apply_custom_css()
    display_org_header(organization)
    
    user_data, registrations_this_month, active_users = get_user_data(organization['org_code'])
    submissions_df = fetch_submission_data(user_data)

    todays_submissions = len(submissions_df[submissions_df['date'] == datetime.now(pytz.timezone(organization['timezone'])).date()])
    todays_users = submissions_df[submissions_df['date'] == datetime.now(pytz.timezone(organization['timezone'])).date()]['user_id'].nunique()

    display_full_metrics(registrations_this_month, active_users, todays_submissions, todays_users)

    st.markdown("---")

    display_active_users_table(user_data)

    st.markdown("---")

    # Create the DataFrame here
    df = pd.DataFrame(user_data)

    selected_user_id = st.selectbox("Select User ID to View Submission History", df['User ID'].tolist())
    if selected_user_id:
        display_submission_history(selected_user_id)

    st.markdown("---")

    if st.button("Logout", key="logout", help="Click to log out"):
        logout_message = logout_org()
        st.success(logout_message)
        st.rerun()