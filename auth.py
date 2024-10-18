import streamlit as st
from firebase_admin import firestore
import bcrypt
from firebase_setup import db
from datetime import datetime, timezone as dt_timezone
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
                universities = org_data.get("universities", [])

                # Step 3: Select University
                university = st.selectbox("Select Your University:", universities)

                if university:
                    # Fetch programs based on selected university
                    programs = org_data.get("programs", [])

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

def login_user(user_id, password):
    try:
        user_ref = db.collection('users').document(user_id).get()
        if not user_ref.exists:
            return None, "Invalid ID or password"

        user_data = user_ref.to_dict()
        if bcrypt.checkpw(password.encode(), user_data['password'].encode()):
            # Check if user is still within 30-day active period
            register_at = user_data.get('registerAt')
            if register_at is None:
                return None, "Registration date missing"
            
            register_at = register_at.replace(tzinfo=pytz.utc)
            status, days_left = check_user_status(register_at)
            
            # Update user status in database only if it has changed
            if status != user_data['status']:
                db.collection('users').document(user_id).update({'status': status})
            
            return {
                "id": user_id,
                "email": user_data['email'],
                "university": user_data['university'],
                "program": user_data['program'],
                "org_code": user_data['org_code'],
                'timezone': user_data['timezone'],
                "status": status,
                "days_left": days_left
            }, "Login successful"
        else:
            return None, "Invalid ID or password"
    except Exception as e:
        return None, f"Login failed: {str(e)}"

def check_user_status(register_at):
    now = datetime.now(pytz.utc)  # Use UTC timezone-aware datetime
    days_passed = (now - register_at).days
    if days_passed <= 30:
        return 'Active', 30 - days_passed
    else:
        return 'Inactive', 0

def logout_user():
    if 'user' in st.session_state:
        del st.session_state['user']
    return "Logout successful"

def login_organization(org_code, password):
    try:
        org_ref = db.collection('organizations').document(org_code).get()
        if not org_ref.exists:
            return None, "Invalid organization code or password"

        org_data = org_ref.to_dict()
        if org_data['password'] == password:  # Direct comparison as password is stored in plain text
            return {
                "org_code": org_code,
                "org_name": org_data['org_name'],
                'timezone': org_data['timezone'],
                'full_dashboard': org_data.get('full_dashboard', False)
            }, "Organization login successful"
        else:
            return None, "Invalid organization code or password"
    except Exception as e:
        return None, f"Organization login failed: {str(e)}"

def logout_org():
    """Logout the organization and clear the organization session state."""
    if 'organization' in st.session_state:
        del st.session_state['organization']
    return "Organization logout successful"
