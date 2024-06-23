import streamlit as st
from openai import OpenAI
import time

api = st.secrets.api_key
# #Initialize OpenAI client and set default assistant_id
client = OpenAI(api_key=api)

def run_assistant(assistant_id, txt, return_content=False, display_chat=True):
    # if 'client' not in st.session_state:
    st.session_state.client = OpenAI(api_key=api)

    #retrieve the assistant
    st.session_state.assistant = st.session_state.client.beta.assistants.retrieve(assistant_id)
    #Create a thread 
    st.session_state.thread = st.session_state.client.beta.threads.create()
    content=""
    
    if txt:
        #Add a Message to a Thread
        message = st.session_state.client.beta.threads.messages.create(
            thread_id = st.session_state.thread.id,
            role = "user",
            content = txt
        )

        #Run the Assistant
        run = st.session_state.client.beta.threads.runs.create(
                thread_id=st.session_state.thread.id,
                assistant_id=st.session_state.assistant.id
        )

        # Spinner for ongoing process
        with st.spinner('少々お待ちください ...'):
            while True:
                # Retrieve the run status
                run_status = st.session_state.client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread.id,
                    run_id=run.id
                )

                # If run is completed, process messages
                if run_status.status == 'completed':
                    messages = st.session_state.client.beta.threads.messages.list(
                        thread_id=st.session_state.thread.id
                    )

                    # Loop through messages and print content based on role
                    for msg in reversed(messages.data):
                        role = msg.role
                        content = msg.content[0].text.value
                        
                        # Use st.chat_message to display the message based on the role
                        if display_chat:
                            with st.chat_message(role):
                                st.write(content)
                    break
                # Wait for a short time before checking the status again
                time.sleep(1)
    if return_content:
        return content