import streamlit as st
from firebase_setup import db

def show_dashboard(organization):
    st.title(f"Welcome, {organization['org_name']}!")
    st.write(f"Organization Code: {organization['org_code']}")

    # Fetch users associated with the organization
    users_ref = db.collection('users').where('org_code', '==', organization['org_code'])
    users = users_ref.stream()

    user_data = []
    for user in users:
        user_dict = user.to_dict()
        user_data.append({
            "User ID": user.id,
            "Expiration Date": user_dict.get('expireAt')
        })

    # Display the data in a table
    st.subheader("Users in this Organization")
    st.table(user_data)

    if st.button("Logout"):
        del st.session_state.organization
        st.rerun()
