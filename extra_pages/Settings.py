import streamlit as st
import pytz
from firebase_setup import db

if 'user' not in st.session_state:
    st.session_state.user = None

def update_user_settings(user_id, timezone):
    user_ref = db.collection('users').document(user_id)
    user_ref.update({
        'timezone': timezone
    })
    st.session_state.user['timezone'] = timezone
    st.success("設定が正常に更新されました！")

def settings_page():
    st.title("ユーザー設定")
    st.write("ここでプロフィールと設定をカスタマイズできます。")

    if 'user' not in st.session_state:
        st.warning("設定にアクセスするにはログインしてください。")
        return

    user_id = st.session_state.user['id']
    user_data = db.collection('users').document(user_id).get().to_dict()

    with st.form("settings_form"):
        st.subheader("タイムゾーン")

        timezone = st.selectbox(
            "タイムゾーン",
            options=pytz.all_timezones,
            index=pytz.all_timezones.index(user_data.get('timezone', 'UTC')),
            help="正確な時間表示のためにローカルタイムゾーンを選択してください。"
        )

        st.markdown("---")
        
        submit_button = st.form_submit_button("設定を保存")
        
        if submit_button:
            update_user_settings(user_id, timezone)
            st.rerun()

    # Display current settings in the main area instead of the sidebar
    st.header("現在の設定")
    st.write(f"**タイムゾーン:** {st.session_state.user.get('timezone', 'UTC')}")

if __name__ == "__main__":
    # Custom CSS with updated hover color
    st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #0097B2;
        color: white;
        padding: 10px 24px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #007A8F;
    }
    </style>
    """, unsafe_allow_html=True)

    settings_page()
