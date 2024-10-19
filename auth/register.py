import streamlit as st
from setup.firebase_setup import db
import bcrypt
from datetime import datetime
import pytz
import time

def register_user():
    timezones = pytz.all_timezones

    # Initialize session state to store user inputs and progress
    if 'user_inputs' not in st.session_state:
        st.session_state.user_inputs = {}
    if 'step' not in st.session_state:
        st.session_state.step = 1

    if st.session_state.step == 1:
        with st.container(border=True):
            st.subheader("登録するユーザー情報を設定してください")
            user_id = st.text_input("ユーザーID:")
            email = st.text_input("メールアドレス:")
            password = st.text_input("パスワード:", type="password")

            if st.button("次へ"):
                if user_id and email and password:
                    # Validate user ID doesn't already exist
                    user_ref = db.collection('users').document(user_id).get()
                    if user_ref.exists:
                        st.error("このIDのユーザーは既に存在します")
                    else:
                        st.session_state.user_inputs['user_id'] = user_id
                        st.session_state.user_inputs['email'] = email
                        st.session_state.user_inputs['password'] = password
                        st.session_state.step = 2
                        st.rerun()
                else:
                    st.warning("すべての項目に入力してください")

    if st.session_state.step == 2:
        with st.container(border=True):
            st.subheader("在籍教育機関情報を入力してください")
            org_code = st.text_input("教育機関コード:")

            if org_code:
                # Fetch organization details from Firestore
                org_ref = db.collection('organizations').document(org_code).get()
                if org_ref.exists:
                    org_data = org_ref.to_dict()
                    universities_data = org_data.get("universities", [])
                    university_names = [uni.get("name") for uni in universities_data]

                    university = st.selectbox("大学を選択:", university_names)

                    if university:
                        selected_university = next((uni for uni in universities_data if uni.get("name") == university), None)
                        faculties = selected_university.get("faculties", []) if selected_university else []

                        faculty_names = [fac.get("name") for fac in faculties]
                        faculty = st.selectbox("学部を選択:", faculty_names)

                        if faculty:
                            selected_faculty = next((fac for fac in faculties if fac.get("name") == faculty), None)
                            departments = selected_faculty.get("departments", []) if selected_faculty else []

                            if departments:
                                department = st.selectbox("学科を選択:", departments)
                            else:
                                department = None

                            timezone = st.selectbox("タイムゾーンを選択:", timezones)

                            if st.button("次へ"):
                                if university and faculty and timezone:
                                    st.session_state.user_inputs['org_code'] = org_code
                                    st.session_state.user_inputs['university'] = university
                                    st.session_state.user_inputs['faculty'] = faculty
                                    st.session_state.user_inputs['department'] = department
                                    st.session_state.user_inputs['timezone'] = timezone
                                    st.session_state.step = 3
                                    st.rerun()
                                else:
                                    st.warning("すべてのフィールドに入力してください")
                else:
                    st.error("無効な教育機関コードです")

    if st.session_state.step == 3:
        with st.container(border=True):
            st.subheader("登録情報を確認してください")
            st.write("**ユーザーID**: ", st.session_state.user_inputs.get('user_id'))
            st.write("**メールアドレス**: ", st.session_state.user_inputs.get('email'))
            st.write("**教育機関コード**: ", st.session_state.user_inputs.get('org_code'))
            st.write("**大学**: ", st.session_state.user_inputs.get('university'))
            st.write("**学部**: ", st.session_state.user_inputs.get('faculty'))
            st.write("**学科**: ", st.session_state.user_inputs.get('department'))
            st.write("**タイムゾーン**: ", st.session_state.user_inputs.get('timezone'))

            if st.button("確認して登録"):
                register_user_in_firestore(
                    st.session_state.user_inputs['user_id'],
                    st.session_state.user_inputs['email'],
                    st.session_state.user_inputs['password'],
                    st.session_state.user_inputs['university'],
                    st.session_state.user_inputs['faculty'],
                    st.session_state.user_inputs['department'],
                    st.session_state.user_inputs['org_code'],
                    st.session_state.user_inputs['timezone']
                )
                st.success("登録に成功しました!タブを切り替えてログインをしてください")
                # Optionally reset session state
                del st.session_state.user_inputs
                del st.session_state.step

            if st.button("登録し直す"):
                del st.session_state.user_inputs
                st.session_state.step = 1
                st.rerun()


def register_user_in_firestore(user_id, email, password, university, faculty, department, org_code, user_timezone):
    try:
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        # Use UTC timezone-aware datetime for registration timestamp
        register_at = datetime.now(pytz.utc)

        # Create a new user document in Firestore
        db.collection('users').document(user_id).set({
            'email': email,
            'password': hashed_password,
            'university': university,
            'faculty': faculty,
            'department': department,
            'org_code': org_code,
            'registerAt': register_at,
            'timezone': user_timezone,
            'status': 'Active'
        })

    except Exception as e:
        st.error(f"登録に失敗しました: {str(e)}")
