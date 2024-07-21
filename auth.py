# auth.py
import streamlit as st
from firebase_admin import auth
from firebase_setup import db

def register_user(email, password, university, program):
    try:
        user = auth.create_user(email=email, password=password)
        db.collection('users').document(user.uid).set({
            'email': email,
            'university': university,
            'program': program,
        })
        return user
    except Exception as e:
        st.error(f"Error registering user: {str(e)}")
        return None

def login_user(email, password):
    try:
        user = auth.get_user_by_email(email)
        # In a real app, you'd verify the password here
        return user
    except Exception as e:
        st.error(f"Error logging in: {str(e)}")
        return None
