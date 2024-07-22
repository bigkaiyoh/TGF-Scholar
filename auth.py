import streamlit as st
import firebase_admin
from firebase_admin import auth, credentials, firestore
import bcrypt

def register_user(email, password, university, program):
    try:
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        user = auth.create_user(email=email, password=password)
        user_ref = db.collection('users').document(user.uid)
        user_ref.set({
            'email': email,
            'password': hashed_password.decode(),
            'university': university,
            'program': program
        })
        st.success("Registration successful!")
        return {"email": email, "uid": user.uid}
    except Exception as e:
        st.error(f"Registration failed: {str(e)}")
        return None

def login_user(email, password):
    try:
        users = db.collection('users').where('email', '==', email).stream()
        for user in users:
            user_data = user.to_dict()
            if bcrypt.checkpw(password.encode(), user_data['password'].encode()):
                st.success("Login successful!")
                return {"email": email, "uid": user.id}
        st.error("Invalid email or password")
        return None
    except Exception as e:
        st.error(f"Login failed: {str(e)}")
        return None

def logout_user():
    st.session_state.user = None
    st.success("Logout successful!")
