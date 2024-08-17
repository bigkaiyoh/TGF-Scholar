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
        user_timezone = pytz.timezone(timezone)
        today = datetime.now(user_timezone).date()
        todays_data = data[data['date'] == today]
        todays_total_submissions = len(todays_data)
        todays_total_users = todays_data['user_email'].nunique()

        st.metric(label="You received", value=todays_total_submissions, delta="tests today")
        st.metric(label="from", value=todays_total_users, delta="students")


def filter_by_dates(data, selected_date):
    # Filter based on selected dates
    if len(selected_date) == 2:
        start_date, end_date = selected_date
        data = data[
            (data['date'].dt.date >= start_date) & 
            (data['date'].dt.date <= end_date)
        ]
    elif len(selected_date) == 1:
        data = data[
            data['date'].dt.date == selected_date[0]
        ]
    return data

def filters(filtered_data, apply_email_filter=True):
    # Convert the 'date' column to datetime type
    # Make a copy of filtered_data to ensure it's a standalone DataFrame
    filtered_data = filtered_data.copy()
    filtered_data['date'] = pd.to_datetime(filtered_data['date'])


    # Initialize selected frameworks and sections
    unique_frameworks = filtered_data['test_framework'].unique()
    unique_sections = filtered_data['test_section'].unique()

    # Container for selected emails - only used if email filtering is applied
    if apply_email_filter:
        unique_emails = filtered_data['user_email'].unique()
        selected_emails = st.multiselect('Select User Email(s):', unique_emails, default=list(unique_emails))

    col1, col2, col3 = st.columns(3)
    with col1:
        # Allow users to select a single date or a range
        selected_date = st.date_input('Select Date(s):', [])
    with col2:
        selected_frameworks = st.multiselect('Select Test Framework(s):', unique_frameworks, default=list(unique_frameworks))
    with col3:
        selected_sections = st.multiselect('Select Test Section(s):', unique_sections, default=list(unique_sections))

    # Filter based on selected dates
    filtered_data = filter_by_dates(filtered_data, selected_date)

    # Continue to filter based on other selections
    if apply_email_filter:
        filtered_data = filtered_data[filtered_data['user_email'].isin(selected_emails)]

    filtered_data = filtered_data[
        filtered_data['test_framework'].isin(selected_frameworks) &
        filtered_data['test_section'].isin(selected_sections)
    ]

    # Conditionally return selected_emails
    if apply_email_filter:
        return filtered_data, selected_emails
    else:
        return filtered_data



def show_org_dashboard(organization):
    """Display the organization dashboard, showing statistics and active users."""
    
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

    # Update and fetch users in the specific organization
    users, registrations_this_month, active_users = get_user_data(organization['org_code'])

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Registrations This Month", value=registrations_this_month)
    with col2:
        st.metric(label="Active Users", value=active_users)

    st.subheader("Active Users")
    df = pd.DataFrame(users)

    search = st.text_input("Search users by ID")
    if search:
        df = df[df['User ID'].str.contains(search, case=False)]

    st.dataframe(df.style.set_properties(**{'text-align': 'left'}), use_container_width=True)

    if st.button("Logout", key="logout", help="Click to log out"):
        logout_message = logout_org()  # Use the new logout_org function
        st.success(logout_message)
        del st.session_state.organization
        st.rerun()


def get_user_data(org_code):
    """Fetch user data and update statuses for the organization."""
    users_ref = db.collection('users').where('org_code', '==', org_code)
    users = users_ref.stream()
    
    current_date = datetime.now(pytz.utc)
    registrations_this_month = 0
    active_users = 0
    user_data = []
    batch = db.batch()

    for user in users:
        user_dict = user.to_dict()
        user_id = user.id
        register_at = user_dict.get('registerAt')
        if isinstance(register_at, datetime):
            register_at = register_at.replace(tzinfo=pytz.utc)

        expiration_date = register_at + timedelta(days=30) if register_at else None
        status = 'Active' if expiration_date and current_date < expiration_date else 'Inactive'

        if status != user_dict.get('status'):
            batch.update(db.collection('users').document(user_id), {'status': status})

        if register_at and register_at.month == current_date.month and register_at.year == current_date.year:
            registrations_this_month += 1

        if status == 'Active':
            active_users += 1
            user_data.append({
                'User ID': user_id,
                'Expiration Date': expiration_date.strftime('%Y-%m-%d') if expiration_date else 'Unknown'
            })

    batch.commit()  # Commit batch updates
    return user_data, registrations_this_month, active_users