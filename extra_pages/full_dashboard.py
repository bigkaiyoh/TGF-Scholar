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
        user_id = user['User ID']  # Use document ID which represents 'id'
        try:
            submission_ref = db.collection('users').document(user_id).collection('submissions').stream()
            for submission in submission_ref:
                sub_data = submission.to_dict()
                if sub_data.get('submit_time'):
                    sub_data.update({
                        'user_id': user_id,  # This 'user_id' is the document ID
                        'timestamp': sub_data.get('submit_time'),
                        'date': sub_data.get('submit_time').date()  # Make sure date field exists
                    })
                    submissions.append(sub_data)
                else:
                    st.warning(f"ユーザー {user_id} の提出に 'submit_time' がありません。スキップします。")
        except Exception as e:
            st.error(f"ユーザー {user_id} の提出を取得中にエラーが発生しました: {str(e)}")
    if submissions:
        return pd.DataFrame(submissions)
    else:
        st.warning("有効な提出がまだありません。")
        return pd.DataFrame()  # Return an empty DataFrame if no valid data

# Display full metrics (for full dashboard view)
def display_full_metrics(registrations_this_month, active_users, todays_submissions, todays_users):
    col1, col2, col3, col4 = st.columns(4)
    metrics = [
        ("本日の提出数", todays_submissions),
        ("本日のアクティブユーザー数", todays_users),
        ("今月の登録数", registrations_this_month),
        ("アクティブユーザー数", active_users)
    ]
    
    for i, (label, value) in enumerate(metrics):
        with [col1, col2, col3, col4][i]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
            </div>
            """, unsafe_allow_html=True)

# Display submission history for a user
def display_submission_history(user_id):
    st.subheader(f"{user_id}の提出履歴")
    
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
                "提出日時": submission_dict.get('submit_time').strftime('%Y-%m-%d %H:%M:%S') if submission_dict.get('submit_time') else '不明',
                "提出志望動機書": submission_dict.get('text', '')
            })

        st.markdown(f"**大学:** {university}")
        st.markdown(f"**プログラム:** {program}")
        
        if submission_data:
            df = pd.DataFrame(submission_data)
            st.dataframe(df.style.set_properties(**{'text-align': 'left', 'white-space': 'pre-wrap'}).set_table_styles([{'selector': 'th', 'props': [('text-align', 'left')]}]), use_container_width=True)
        else:
            st.info("このユーザーの提出は見つかりませんでした。")
    except Exception as e:
        st.error(f"提出履歴の取得中にエラーが発生しました: {str(e)}")

def full_org_dashboard(organization):
    apply_custom_css()
    display_org_header(organization)

    user_data, registrations_this_month, active_users = get_user_data(organization['org_code'])
    submissions_df = fetch_submission_data(user_data)

    if not submissions_df.empty:
        # Ensure 'date' column exists before processing it
        if 'date' in submissions_df.columns:
            todays_submissions = len(submissions_df[submissions_df['date'] == datetime.now(pytz.timezone(organization['timezone'])).date()])
            todays_users = submissions_df[submissions_df['date'] == datetime.now(pytz.timezone(organization['timezone'])).date()]['user_id'].nunique()
        else:
            st.warning("有効な日付のある提出がありません。")
            todays_submissions = 0
            todays_users = 0
    else:
        todays_submissions = 0
        todays_users = 0

    display_full_metrics(registrations_this_month, active_users, todays_submissions, todays_users)

    st.markdown("---")

    display_active_users_table(user_data)

    st.markdown("---")

    # Create the DataFrame here
    df = pd.DataFrame(user_data)

    if not df.empty:
        selected_user_id = st.selectbox("提出履歴を表示するユーザーIDを選択してください", df['User ID'].tolist())
        if selected_user_id:
            display_submission_history(selected_user_id)

    st.markdown("---")

    if st.button("ログアウト", key="logout", help="クリックしてログアウト"):
        logout_message = logout_org()
        st.success(logout_message)
        st.rerun()
