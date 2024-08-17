import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from firebase_setup import db
import pytz
from auth import logout_org

if 'organization' not in st.session_state:
    st.session_state.organization = None




# ------------------------- functions for full dashboard -----------------------
def todays_total_submissions(data, timezone):
    """Display today's total submissions based on pre-fetched data, using user_id as the identifier."""
    user_timezone = pytz.timezone(timezone)
    today = datetime.now(user_timezone).date()
    todays_data = data[data['date'] == today]
    todays_total_submissions = len(todays_data)
    todays_total_users = todays_data['user_id'].nunique()  # Use 'user_id' instead of 'user_email'

    st.metric(label="You received", value=todays_total_submissions, delta="tests today")
    st.metric(label="from", value=todays_total_users, delta="students")

def fetch_submission_data(users_data):
    """Fetch submission data for users."""
    submissions = []
    for user_id, user_info in users_data.items():
        submission_ref = db.collection('users').document(user_id).collection('submissions').stream()
        for submission in submission_ref:
            sub_data = submission.to_dict()
            sub_data.update({
                'user_id': user_id,  # Add 'user_id' to the submission data
                'timestamp': sub_data.get('timestamp').strftime("%Y-%m-%d %H:%M:%S"),
                'date': sub_data.get('timestamp').date()  # Add 'date' to use in today's submissions calculation
            })
            submissions.append(sub_data)
    return pd.DataFrame(submissions)

def display_detailed_user_info(user_data):
    """Display detailed user information with a clickable submission history."""
    st.subheader("Active Users")
    df = pd.DataFrame(user_data)
    
    selected_user_id = st.selectbox("Select User ID to View Submission History", df['User ID'].tolist())
    
    if selected_user_id:
        st.write(f"Selected User: {selected_user_id}")
    
    st.dataframe(df.style.set_properties(**{'text-align': 'left'}), use_container_width=True)
    
    return selected_user_id

def display_submission_history(user_id):
    """Display submission history for a selected user."""
    st.subheader(f"Submission History for User {user_id}")
    
    submissions_ref = db.collection('users').document(user_id).collection('submissions')
    submissions = submissions_ref.order_by('submit_time', direction=firestore.Query.DESCENDING).stream()
    
    submission_data = []
    for submission in submissions:
        submission_dict = submission.to_dict()
        submission_data.append({
            "Submission Text": submission_dict.get('text', ''),
            "Submission Date": submission_dict.get('submit_time').strftime('%Y-%m-%d %H:%M:%S'),
            "University": submission_dict.get('university', ''),
            "Program": submission_dict.get('program', '')
        })
    
    if submission_data:
        st.write(pd.DataFrame(submission_data))
    else:
        st.write("No submissions found for this user.")


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
            user_data.append({
                'User ID': user_id,
                'Expiration Date': expiration_date.strftime('%Y-%m-%d') if expiration_date else 'Unknown',
                'registerAt': register_at.strftime('%Y-%m-%d') if register_at else 'Unknown',
                'status': status,
                'submission_count': user_dict.get('submission_count', 0),
                'engagement_score': user_dict.get('engagement_score', 0),  # Placeholder for engagement
            })

    # Commit all updates to Firestore at once
    batch.commit()

    return user_data, registrations_this_month, active_users




def display_org_header(organization):
    st.markdown(f"<h1 class='big-font'>Welcome, {organization['org_name']}!</h1>", unsafe_allow_html=True)
    st.markdown(f"**Organization Code:** {organization['org_code']}")

def display_metrics(registrations_this_month, active_users):
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Registrations This Month", value=registrations_this_month)
    with col2:
        st.metric(label="Active Users", value=active_users)

def display_active_users_table(user_data):
    st.subheader("Active Users")
    df = pd.DataFrame(user_data)
    search = st.text_input("Search users by ID")
    if search:
        df = df[df['User ID'].str.contains(search, case=False)]
    st.dataframe(df.style.set_properties(**{'text-align': 'left'}), use_container_width=True)


def show_org_dashboard(organization):
    """Basic Organization Dashboard."""
    display_org_header(organization)
    
    # Fetch user data and update statuses
    user_data, registrations_this_month, active_users = get_user_data(organization['org_code'])

    # Display metrics
    display_metrics(registrations_this_month, active_users)

    # Display user table
    display_active_users_table(user_data)

    # Logout button
    if st.button("Logout", key="logout", help="Click to log out"):
        logout_message = logout_org()  # No need to manually delete session state here
        st.success(logout_message)
        st.rerun()

def full_org_dashboard(organization):
    """Full Organization Dashboard with additional metrics and features."""
    display_org_header(organization)
    
    # Fetch user data and update statuses
    user_data, registrations_this_month, active_users = get_user_data(organization['org_code'])

    # Fetch submission data for the organization
    submissions_df = fetch_submission_data(user_data)  # Fetch all submission data

    # Display base metrics
    display_metrics(registrations_this_month, active_users)
    
    # Additional metrics: Today's total submissions
    todays_total_submissions(submissions_df, organization['timezone'])  # Pass pre-fetched data
    
    # Display detailed user table with submission history
    selected_user_id = display_detailed_user_info(user_data)
    
    if selected_user_id:
        display_submission_history(selected_user_id)

    # Logout button
    if st.button("Logout", key="logout", help="Click to log out"):
        logout_message = logout_org()
        st.success(logout_message)
        st.rerun()
