import streamlit as st
import pandas as pd
import pytz
from firebase_admin import firestore
from .dashboard_common import apply_custom_css, display_org_header, get_user_data, display_active_users_table
from auth.login_manager import logout_org
from datetime import datetime
from setup.firebase_setup import db
import html

# Fetch submission data using a collection group query
def fetch_submission_data(org_code):
    """Fetch submission data for all users in an organization."""
    submissions = []
    try:
        # Query all submissions where 'org_code' matches
        submissions_ref = db.collection_group('submissions').where('org_code', '==', org_code)
        submissions_list = list(submissions_ref.stream())

        if not submissions_list:
            # No submissions found for the organization
            return pd.DataFrame()  # Return an empty DataFrame without error

        for submission in submissions_list:
            sub_data = submission.to_dict()
            submit_time = sub_data.get('submit_time')
            if submit_time and isinstance(submit_time, datetime):
                timezone_str = sub_data.get('timezone', 'UTC')
                timezone = pytz.timezone(timezone_str)
                sub_data.update({
                    'user_id': submission.reference.parent.parent.id,  # Get user ID from parent document
                    'timestamp': submit_time,
                    'date': submit_time.astimezone(timezone).date()
                })
                submissions.append(sub_data)
            else:
                pass  # Skip submissions without 'submit_time'

    except Exception as e:
        error_message = str(e)
        if 'indexes?create_composite' in error_message:
            # Provide a user-friendly message about missing indexes
            st.error("提出データを取得するために必要な設定が完了していません。Nuginyサポートにお問い合わせください。")
            return pd.DataFrame()
        else:
            # For other exceptions, display a general error message
            st.error("エラーが発生しました。Nuginyサポートにお問い合わせください。")
            return pd.DataFrame()

    if submissions:
        return pd.DataFrame(submissions)
    else:
        # No valid submissions after processing
        return pd.DataFrame()




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
        # Fetch user data for university, faculty, and department
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            university = user_data.get('university', '')
            faculty = user_data.get('faculty', '')
            department = user_data.get('department', '')
        else:
            university = faculty = department = ''
        
        submissions_ref = user_ref.collection('submissions').order_by(
            'submit_time', direction=firestore.Query.DESCENDING)
        submissions = list(submissions_ref.stream())

        submission_data = []
        submission_details = []
        for idx, submission in enumerate(submissions):
            submission_dict = submission.to_dict()
            submit_time = submission_dict.get('submit_time')
            submit_time_str = submit_time.strftime('%Y-%m-%d %H:%M') if submit_time else '不明'
            
            # Prepare data for the table
            submission_data.append({
                "提出番号": idx + 1,
                "提出日時": submit_time_str,
            })
            
            # Store detailed submission data
            submission_details.append({
                "text": submission_dict.get('text', ''),
                "feedback": submission_dict.get('feedback', '添削なし')
            })

        st.markdown(f"**大学:** {university}")
        st.markdown(f"**学部:** {faculty}")
        if department:
            st.markdown(f"**学科:** {department}")
        
        if submission_data:
            df = pd.DataFrame(submission_data)
            # Display the interactive table
            st.data_editor(
                df,
                use_container_width=True,
                hide_index=True,
                key="submission_data_editor"
            )

            # Create submission options for the selectbox
            submission_options = [f"提出 {item['提出番号']}" for item in submission_data]

            # Display the selectbox below the table
            selected_submission = st.selectbox("表示する提出を選択してください", submission_options)

            # Get the index of the selected submission
            idx = submission_options.index(selected_submission)

            # Retrieve the submission details
            submission_text = submission_details[idx]['text']
            feedback = submission_details[idx]['feedback']

            # Display the submission text and feedback using styled boxes
            with st.expander("入力内容", expanded=False):
                st.write("**志望動機書:**")
                # Use markdown to display the text in a styled box
                box_content = submission_text.replace('\n', '<br>')
                st.markdown(f"""
                    <div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; background-color: #f9f9f9;">
                        {box_content}
                    </div>
                """, unsafe_allow_html=True)
                
                st.write(f'文字数: {len(submission_text.split())} 文字')
                            

            # Display feedback in a styled box with background color
            st.write("**添削内容:**")
            
            # Escape special characters to prevent HTML rendering issues
            with st.chat_message("ai"):
                st.write(feedback)
            
        else:
            st.info("このユーザーの提出は見つかりませんでした。")
    except Exception as e:
        st.error("提出履歴の取得中にエラーが発生しました。")



def full_org_dashboard(organization):
    apply_custom_css()
    display_org_header(organization)

    user_data, registrations_this_month, active_users = get_user_data(organization['org_code'])
    submissions_df = fetch_submission_data(organization['org_code'])

    # Calculate today's date once
    today = datetime.now(pytz.timezone(organization['timezone'])).date()

    if not submissions_df.empty:
        # Ensure 'date' column exists before processing it
        if 'date' in submissions_df.columns:
            todays_submissions = len(submissions_df[submissions_df['date'] == today])
            todays_users = submissions_df[submissions_df['date'] == today]['user_id'].nunique()
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