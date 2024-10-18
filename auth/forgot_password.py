import streamlit as st
from setup.firebase_setup import db
import bcrypt
import pytz
from datetime import datetime

def render_forgot_password_form():
    """Renders the forgot password form and handles password reset."""
    with st.form("forgot_password_form"):
        st.subheader("パスワードをリセット")
        user_id = st.text_input("ユーザーID", placeholder="ユーザーIDを入力してください")
        email = st.text_input("メールアドレス", placeholder="登録済みのメールアドレスを入力してください")
        new_password = st.text_input("新しいパスワード", type="password", placeholder="新しいパスワードを入力してください")
        confirm_password = st.text_input("新しいパスワード（確認）", type="password", placeholder="新しいパスワードを再度入力してください")
        submit_button = st.form_submit_button("パスワードをリセット")

    if submit_button:
        if not user_id or not email or not new_password or not confirm_password:
            st.warning("すべてのフィールドに入力してください。")
            return

        if new_password != confirm_password:
            st.error("新しいパスワードが一致しません。")
            return

        reset_password(user_id, email, new_password)

def reset_password(user_id, email, new_password):
    """Resets the user's password after verifying their identity."""
    try:
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()

        if not user_doc.exists:
            st.error("ユーザーが見つかりません。")
            return

        user_data = user_doc.to_dict()

        if user_data.get('email') != email:
            st.error("メールアドレスが一致しません。")
            return

        # Hash the new password
        hashed_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

        # Update the password in Firestore
        user_ref.update({
            'password': hashed_password,
            'password_reset_at': datetime.now(pytz.utc)
        })

        st.success("パスワードがリセットされました。新しいパスワードでログインしてください。")
    except Exception as e:
        st.error(f"パスワードのリセット中にエラーが発生しました: {str(e)}")
