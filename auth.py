import streamlit as st
from firebase_admin import firestore
import bcrypt
from firebase_setup import db
from datetime import datetime, timedelta


def register_user(user_id, email, password, university, program, org_code):
    try:
        user_ref = db.collection('users').document(user_id).get()
        if user_ref.exists:
            return None, "User with this ID already exists"

        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        register_at = datetime.now()
        
        db.collection('users').document(user_id).set({
            'email': email,
            'password': hashed_password,
            'university': university,
            'program': program,
            'org_code': org_code,
            'registerAt': register_at,
            'status': 'Active'
        })

        user_data = {
            "email": email,
            "id": user_id,
            "university": university,
            "program": program,
            "org_code": org_code,
            "status": 'Active',
            "registerAt": register_at
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
            status, days_left = check_user_status(user_data['registerAt'])
            
            # Update user status in database only if it has changed
            if status != user_data['status']:
                db.collection('users').document(user_id).update({'status': status})
            
            return {
                "id": user_id,
                "email": user_data['email'],
                "university": user_data['university'],
                "program": user_data['program'],
                "org_code": user_data['org_code'],
                "status": status,
                "days_left": days_left
            }, "Login successful"
        else:
            return None, "Invalid ID or password"
    except Exception as e:
        return None, f"Login failed: {str(e)}"

def check_user_status(register_at):
    now = datetime.now()
    days_passed = (now - register_at).days
    if days_passed <= 30:
        return 'Active', 30 - days_passed
    else:
        return 'Inactive', 0
    
# def update_user_status(user_id):
#     try:
#         user_ref = db.collection('users').document(user_id).get()
#         user_data = user_ref.to_dict()
#         status, days_left = check_user_status(user_data['registerAt'])
#         db.collection('users').document(user_id).update({'status': status})
#         return status, days_left
#     except Exception as e:
#         print(f"Error updating user status: {e}")
#         return None, None

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
                "org_name": org_data['org_name']
            }, "Organization login successful"
        else:
            return None, "Invalid organization code or password"
    except Exception as e:
        return None, f"Organization login failed: {str(e)}"