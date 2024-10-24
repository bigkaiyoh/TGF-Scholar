import streamlit as st
from .dashboard_common import apply_custom_css, display_org_header, get_user_data, display_active_users_table
from auth.login_manager import logout_org
from setup.firebase_setup import db
from auth.login_manager import logout_org

# Display basic metrics
def display_metrics(registrations_this_month, active_users):
    col1, col2 = st.columns(2)

    metrics = [
        ("今月の登録数", registrations_this_month),
        ("アクティブユーザー数", active_users)
    ]
    
    for i, (label, value) in enumerate(metrics):
        with [col1, col2][i]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
            </div>
            """, unsafe_allow_html=True)

def show_org_dashboard():
    """Basic Organization Dashboard."""
    apply_custom_css()
    display_org_header()
    

    # Fetch user data and update statuses
    user_data, registrations_this_month, active_users = get_user_data()


    # Display metrics
    display_metrics(registrations_this_month, active_users)

    # Display user table
    display_active_users_table(user_data)

    # Logout button
    if st.button("ログアウト", key="logout", help="クリックしてログアウト"):
        logout_message = logout_org()  # No need to manually delete session state here
        st.success(logout_message)
        st.rerun()