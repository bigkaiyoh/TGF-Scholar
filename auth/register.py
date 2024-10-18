import streamlit as st
from setup.firebase_setup import db
import bcrypt
from datetime import datetime
import pytz
import time

def register_user():
    st.title("Register for TGF-Scholar")

    timezones = pytz.all_timezones

    # Initialize session state to store user inputs and progress
    if 'user_inputs' not in st.session_state:
        st.session_state.user_inputs = {}
    if 'step' not in st.session_state:
        st.session_state.step = 1


    if st.session_state.step == 1:
        with st.container(border=True):
            st.subheader("Step 1: Enter User Information")
            user_id = st.text_input("Enter User ID:")
            email = st.text_input("Enter Email:")
            password = st.text_input("Enter Password:", type="password")

            if st.button("Next"):
                if user_id and email and password:
                    # Validate user ID doesn't already exist
                    user_ref = db.collection('users').document(user_id).get()
                    if user_ref.exists:
                        st.error("User with this ID already exists")
                    else:
                        st.session_state.user_inputs['user_id'] = user_id
                        st.session_state.user_inputs['email'] = email
                        st.session_state.user_inputs['password'] = password
                        st.session_state.step = 2
                        st.rerun()
                else:
                    st.warning("Please fill in all fields")

    if st.session_state.step == 2:
        with st.container(border=True):
            st.subheader("Step 2: Enter Organization Information")
            org_code = st.text_input("Enter Organization Code:")
            if org_code:
                # Fetch organization details from Firestore
                org_ref = db.collection('organizations').document(org_code).get()
                if org_ref.exists:
                    org_data = org_ref.to_dict()
                    universities_data = org_data.get("universities", [])
                    university_names = [uni.get("name") for uni in universities_data]

                    university = st.selectbox("Select Your University:", university_names)

                    if university:
                        selected_university = next((uni for uni in universities_data if uni.get("name") == university), None)
                        programs = selected_university.get("programs", []) if selected_university else []

                        program = st.selectbox("Select Your Program:", programs)

                        timezone = st.selectbox("Select Your Timezone:", timezones)

                        if st.button("Next"):
                            if university and program and timezone:
                                st.session_state.user_inputs['org_code'] = org_code
                                st.session_state.user_inputs['university'] = university
                                st.session_state.user_inputs['program'] = program
                                st.session_state.user_inputs['timezone'] = timezone
                                st.session_state.step = 3
                                st.rerun()
                            else:
                                st.warning("Please fill in all fields")
                else:
                    st.error("Invalid Organization Code")

    if st.session_state.step == 3:
        with st.container(border=True):
            st.subheader("Step 3: Confirm Your Information")
            st.write("**User ID**: ", st.session_state.user_inputs.get('user_id'))
            st.write("**Email**: ", st.session_state.user_inputs.get('email'))
            st.write("**Organization Code**: ", st.session_state.user_inputs.get('org_code'))
            st.write("**University**: ", st.session_state.user_inputs.get('university'))
            st.write("**Program**: ", st.session_state.user_inputs.get('program'))
            st.write("**Timezone**: ", st.session_state.user_inputs.get('timezone'))

            if st.button("Confirm and Register"):
                register_user_in_firestore(
                    st.session_state.user_inputs['user_id'],
                    st.session_state.user_inputs['email'],
                    st.session_state.user_inputs['password'],
                    st.session_state.user_inputs['university'],
                    st.session_state.user_inputs['program'],
                    st.session_state.user_inputs['org_code'],
                    st.session_state.user_inputs['timezone']
                )
                st.success("Registration successful!")
                time.sleep(2)
                st.session_State.choice = "Login"
                st.rerun()

            if st.button("Go Back"):
                del st.session_state.user_inputs
                st.session_state.step = 1


def register_user_in_firestore(user_id, email, password, university, program, org_code, user_timezone):
    try:
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        # Use UTC timezone-aware datetime for registration timestamp
        register_at = datetime.now(pytz.utc)

        # Create a new user document in Firestore
        db.collection('users').document(user_id).set({
            'email': email,
            'password': hashed_password,
            'university': university,
            'program': program,
            'org_code': org_code,
            'registerAt': register_at,
            'timezone': user_timezone,
            'status': 'Active'
        })

        # Optionally reset session state
        del st.session_state.user_inputs
        del st.session_state.step

    except Exception as e:
        st.error(f"Registration failed: {str(e)}")