import streamlit as st
from setup.firebase_setup import db
import bcrypt
from datetime import datetime
import pytz


def register_user():
    st.title("Register for TGF-Scholar")

    # Step 1: Input User Information
    user_id = st.text_input("Enter User ID:")
    email = st.text_input("Enter Email:")
    password = st.text_input("Enter Password:", type="password")

    if user_id and email and password:
        # Check if user ID already exists
        user_ref = db.collection('users').document(user_id).get()
        if user_ref.exists:
            st.error("User with this ID already exists")
            return

        # Step 2: Input Organization Code
        org_code = st.text_input("Enter Organization Code:")
        if org_code:
            # Fetch organization details from Firestore
            org_ref = db.collection('organizations').document(org_code).get()
            if org_ref.exists:
                org_data = org_ref.to_dict()
                universities_data = org_data.get("universities", [])
                university_names = [uni.get("name") for uni in universities_data]

                # Step 3: Select University
                university = st.selectbox("Select Your University:", university_names)

                if university:
                    # Fetch programs based on selected university
                    selected_university = next((uni for uni in universities_data if uni.get("name") == university), None)
                    programs = selected_university.get("programs", []) if selected_university else []

                    # Step 4: Select Program
                    program = st.selectbox("Select Your Program:", programs)

                    # Step 5: Select Timezone
                    user_timezone = st.selectbox("Select Your Timezone:", ["UTC", "Japan", "America/New_York", "Europe/London"])

                    if st.button("Register"):
                        if user_id and email and password and university and program and user_timezone:
                            # Call the function to complete registration
                            user_data, message = register_user_in_firestore(
                                user_id, email, password, university, program, org_code, user_timezone
                            )
                            if user_data:
                                st.success(message)
                            else:
                                st.error(message)
                        else:
                            st.error("Please fill in all fields")
            else:
                st.error("Invalid Organization Code")
    else:
        st.error("Please fill in User ID, Email, and Password")


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
