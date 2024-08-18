import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from firebase_setup import db
import pytz
from auth import logout_org
from firebase_admin import firestore

if 'organization' not in st.session_state:
    st.session_state.organization = None


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




def display_org_header(organization):
    st.markdown(f"<h1 class='big-font'>Welcome, {organization['org_name']}!</h1>", unsafe_allow_html=True)
    st.markdown(f"<p><strong>Organization Code:</strong> {organization['org_code']}</p>", unsafe_allow_html=True)

def display_metrics(registrations_this_month, active_users):
    col1, col2 = st.columns(2)

    metrics = [
        ("Registrations This Month", registrations_this_month),
        ("Active Users", active_users)
    ]
    
    for i, (label, value) in enumerate(metrics):
        with [col1, col2][i]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
            </div>
            """, unsafe_allow_html=True)
    

def display_full_metrics(registrations_this_month, active_users, todays_submissions, todays_users):
    col1, col2, col3, col4 = st.columns(4)
    metrics = [
        ("Today's Submissions", todays_submissions),
        ("Today's Active Students", todays_users),
        ("Registrations This Month", registrations_this_month),
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

def display_active_users_table(user_data):
    st.subheader("Active Users")
    df = pd.DataFrame(user_data)
    
    if df.empty:
        st.info("No users found.")
    else:
        st.dataframe(df.style.set_properties(**{'text-align': 'left'}).highlight_max(subset=['total_submission'], color='#e6f3ff'), use_container_width=True)



def show_org_dashboard(organization):
    """Basic Organization Dashboard."""
    apply_custom_css()
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