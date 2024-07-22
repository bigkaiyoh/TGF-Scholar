import streamlit as st
from firebase_setup import db
import bcrypt

def register_user(email, password, university, program):
    users_ref = db.collection("users")
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    user_data = {
        "email": email,
        "password": hashed_password.decode(),
        "university": university,
        "program": program
    }
    users_ref.add(user_data)
    st.success("User registered successfully!")

def login_user(email, password):
    users_ref = db.collection("users")
    query = users_ref.where("email", "==", email).stream()

    for user in query:
        user_data = user.to_dict()
        if bcrypt.checkpw(password.encode(), user_data["password"].encode()):
            return user_data  # Returning user data for session state
        else:
            st.error("Invalid password.")
            return None
    
    st.error("User not found.")
    return None

def logout_user():
    st.session_state.user = None
    st.success("Logged out successfully!")
