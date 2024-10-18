import streamlit as st
from setup.firebase_setup import db
import bcrypt
from datetime import datetime
import pytz

# Get all timezones from pytz
timezones = pytz.all_timezones

def register_user():
    st.title("Register for TGF-Scholar")

    # Initialize session state to track form progress
    if 'step' not in st.session_state:
        st.session_state.step = 1

    with st.container():
        st.subheader("Registration Form")

        # Step 1: Input User Information
        if st.session_state.step == 1:
            user_id = st.text_input("Enter User ID:")
            email = st.text_input("Enter Email:")
            password = st.text_input("Enter Password:", type="password")
            
            if st.button("Next (User Info)", key="step1"):
                if not user_id or not email or not password:
                    st.error("Please fill in User ID, Email, and Password.")
                else:
                    # Check if user ID already exists
                    user_ref = db.collection('users').document(user_id).get()
                    if user_ref.exists():
                        st.error("User with this ID already exists")
                    else:
                        st.session_state.user_id = user_id
                        st.session_state.email = email
                        st.session_state.password = password
                        st.session_state.step = 2

        # Step 2: Input Organization Information
        if st.session_state.step >= 2:
            org_code = st.text_input("Enter Organization Code:", key="org_code")

            if st.session_state.step == 2:
                if st.button("Next (Organization)", key="step2"):
                    if not org_code:
                        st.error("Please enter the Organization Code.")
                    else:
                        # Fetch organization details from Firestore
                        org_ref = db.collection('organizations').document(org_code).get()
                        if not org_ref.exists():
                            st.error("Invalid Organization Code")
                        else:
                            st.session_state.org_code = org_code
                            st.session_state.org_data = org_ref.to_dict()
                            universities_data = st.session_state.org_data.get("universities", [])
                            if not universities_data:
                                st.error("No universities found for this organization.")
                            else:
                                st.session_state.universities_data = universities_data
                                st.session_state.university_names = [uni.get("name") for uni in universities_data]
                                st.session_state.step = 3

        # Step 3: University and Program Selection
        if st.session_state.step >= 3:
            university = st.selectbox("Select Your University:", st.session_state.university_names, key="university_select")
            
            if university:
                selected_university = next((uni for uni in st.session_state.universities_data if uni.get("name") == university), None)
                programs = selected_university.get("programs", []) if selected_university else []

                program = st.selectbox("Select Your Program:", programs, key="program_select")

            if st.session_state.step == 3 and university and program:
                if st.button("Next (University & Program)", key="step3"):
                    st.session_state.university = university
                    st.session_state.program = program
                    st.session_state.step = 4

        # Step 4: Timezone and Final Submission
        if st.session_state.step >= 4:
            user_timezone = st.selectbox("Select Your Timezone:", timezones, key="timezone_select")
            
            if st.session_state.step == 4:
                if st.button("Register", key="step4"):
                    if st.session_state.user_id and st.session_state.email and st.session_state.password and st.session_state.university and st.session_state.program and user_timezone:
                        # Call the function to complete registration
                        user_data, message = register_user_in_firestore(
                            st.session_state.user_id, st.session_state.email, st.session_state.password,
                            st.session_state.university, st.session_state.program,
                            st.session_state.org_code, user_timezone
                        )
                        if user_data:
                            st.success(message)
                            # Reset step to 1 for a new registration
                            st.session_state.step = 1
                        else:
                            st.error(message)
                    else:
                        st.error("Please fill in all fields.")


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

        # Calculate days left
        days_left = 30

        user_data = {
            "email": email,
            "id": user_id,
            "university": university,
            "program": program,
            "org_code": org_code,
            "status": 'Active',
            "registerAt": register_at,
            'timezone': user_timezone,
            "days_left": days_left
        }
        return user_data, "Registration successful"
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return None, f"Registration failed: {str(e)}"