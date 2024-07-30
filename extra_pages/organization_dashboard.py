import streamlit as st
import pandas as pd
from datetime import datetime
from firebase_setup import db

def show_org_dashboard(organization):
    st.title(f"Welcome, {organization['org_name']}!")
    st.write(f"Organization Code: {organization['org_code']}")

    # Fetch users associated with the organization
    users = db.collection('users').where('org_code', '==', organization['org_code']).stream()

    user_data = []
    current_month = datetime.now().month
    current_year = datetime.now().year
    registrations_this_month = 0

    for user in users:
        user_dict = user.to_dict()
        user_id = user.id
        expire_at = user_dict.get('expireAt')
        register_at = user_dict.get('registerAt')

        # Check if the user registered in the current month
        if register_at and register_at.month == current_month and register_at.year == current_year:
            registrations_this_month += 1

        # Format the expiration date
        if expire_at:
            expire_at = expire_at.strftime('%B %d')
        else:
            expire_at = 'N/A'
        
        user_data.append({'User ID': user_id, 'Expiration Date': expire_at})

    # Display the number of registrations this month
    st.metric(label="Registrations This Month", value=registrations_this_month)

    # Convert to DataFrame
    df = pd.DataFrame(user_data)

    # Display the table without index and in a more user-friendly date format
    st.dataframe(df)

    if st.button("Logout"):
        del st.session_state.organization
        st.rerun()
