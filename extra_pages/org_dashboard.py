import streamlit as st
from .dashboard_common import apply_custom_css, display_org_header, get_user_data, display_active_users_table
from auth.login_manager import logout_org
from setup.firebase_setup import db
from auth.login_manager import logout_org


# Display basic metrics
def display_metrics(registrations_this_month, active_users):
    col1, col2 = st.columns(2)

    metrics = [
        ("Monthly Signups", registrations_this_month),
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