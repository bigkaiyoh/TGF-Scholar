import streamlit as st
from firebase_admin import firestore
import bcrypt
from firebase_setup import db

def register_user(email, password, university, program):
    try:
        # Check if user already exists
        user_ref = db.collection('users').where('email', '==', email).limit(1).get()
        if len(user_ref) > 0:
            return None, "User with this email already exists"

        # Hash password
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        # Create new user document
        new_user = db.collection('users').add({
            'email': email,
            'password': hashed_password,
            'university': university,
            'program': program
        })

        # Return user data in the expected format
        user_data = {
            "email": email,
            "uid": new_user[1].id,
            "university": university,
            "program": program
        }
        return user_data, "Registration successful"
    except Exception as e:
        print(f"Registration error: {str(e)}")  # For debugging
        return None, f"Registration failed: {str(e)}"

def login_user(email, password):
    try:
        user_ref = db.collection('users').where('email', '==', email).limit(1).get()
        if not user_ref:
            return None, "Invalid email or password"

        user_data = user_ref[0].to_dict()
        if bcrypt.checkpw(password.encode(), user_data['password'].encode()):
            return {"email": email, "uid": user_ref[0].id, "university": user_data['university'], "program": user_data['program']}, "Login successful"
        else:
            return None, "Invalid email or password"
    except Exception as e:
        return None, f"Login failed: {str(e)}"

def logout_user():
    if 'user' in st.session_state:
        del st.session_state['user']
    return "Logout successful"