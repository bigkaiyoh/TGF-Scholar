import streamlit as st
from firebase_admin import firestore
import bcrypt
from firebase_setup import db
from datetime import datetime, timedelta

def register_user(user_id, email, password, university, program, org_code):
    try:
        # Check if user ID already exists
        user_ref = db.collection('users').document(user_id).get()
        if user_ref.exists:
            return None, "User with this ID already exists"

        # Hash password
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        # Calculate the expiration date (e.g., 30 days from registration)
        register_at = datetime.now()
        expire_at = register_at + timedelta(days=30)

        # Create new user document with registration and expiration dates
        db.collection('users').document(user_id).set({
            'email': email,
            'password': hashed_password,
            'university': university,
            'program': program,
            'org_code': org_code,
            'registerAt': register_at,
            'expireAt': expire_at
        })

        # Return user data
        user_data = {
            "email": email,
            "id": user_id,
            "university": university,
            "program": program,
            "org_code": org_code  # Ensure org_code is included in the returned data
        }
        return user_data, "Registration successful"
    except Exception as e:
        print(f"Registration error: {str(e)}")  # For debugging
        return None, f"Registration failed: {str(e)}"

def login_user(user_id, password):
    try:
        user_ref = db.collection('users').document(user_id).get()
        if not user_ref.exists:
            return None, "Invalid ID or password"

        user_data = user_ref.to_dict()
        if bcrypt.checkpw(password.encode(), user_data['password'].encode()):
            return {
                "id": user_id,
                "email": user_data['email'],
                "university": user_data['university'],
                "program": user_data['program'],
                "org_code": user_data['org_code']  # Ensure org_code is included in the returned data
            }, "Login successful"
        else:
            return None, "Invalid ID or password"
    except Exception as e:
        return None, f"Login failed: {str(e)}"

def logout_user():
    if 'user' in st.session_state:
        del st.session_state['user']
    return "Logout successful"