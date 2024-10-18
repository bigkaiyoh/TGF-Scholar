import streamlit as st
from openai import OpenAI
import time
from PIL import Image
import base64
import requests
from google.cloud import secretmanager
import json

def get_secret():
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/581656499945/secrets/unicke_apis/versions/latest"
    response = client.access_secret_version(request={"name": name})
    secret_string = response.payload.data.decode("UTF-8")
    return json.loads(secret_string)

secrets = get_secret()
api = secrets['api_key']
# #Initialize OpenAI client and set default assistant_id
client = OpenAI(api_key=api)



def run_assistant(assistant_id, txt, return_content=False, display_chat=True, user_name="user", assistant_name="assistant"):
    # Initialize OpenAI client and set assistant if not already initialized
    st.session_state.client = OpenAI(api_key=api)
    st.session_state.assistant = st.session_state.client.beta.assistants.retrieve(assistant_id)
    st.session_state.thread = st.session_state.client.beta.threads.create()
    content = ""

    if txt:
        # Add a message to the thread from the user
        message = st.session_state.client.beta.threads.messages.create(
            thread_id=st.session_state.thread.id,
            role="user",
            content=txt
        )

        # Run the assistant
        run = st.session_state.client.beta.threads.runs.create(
            thread_id=st.session_state.thread.id,
            assistant_id=st.session_state.assistant.id
        )

        # Spinner for the ongoing process
        with st.spinner('One moment...'):
            while True:
                # Retrieve the run status
                run_status = st.session_state.client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread.id,
                    run_id=run.id
                )

                # If completed, process the messages
                if run_status.status == 'completed':
                    messages = st.session_state.client.beta.threads.messages.list(
                        thread_id=st.session_state.thread.id
                    )

                    # Loop through messages and display based on the role
                    for msg in reversed(messages.data):
                        role = msg.role
                        content = msg.content[0].text.value

                        # Use st.chat_message to display the message with the correct name
                        if display_chat:
                            if role == "user":
                                with st.chat_message(name=user_name):  # Custom user name
                                    st.write(content)
                            else:
                                with st.chat_message(name=assistant_name):  # Custom assistant name
                                    st.write(content)
                    break
                time.sleep(1)

    # Return content if requested
    if return_content:
        return content

    

# ------------------ transcribe with GPT 4 vision -------------------------
def convert_image_to_text(uploaded_file):

    # Function to encode the image
    def encode_image(image_file):
        return base64.b64encode(image_file.read()).decode('utf-8')

    # Encode the uploaded file
    base64_image = encode_image(uploaded_file)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please transcribe the handwritten text in this image."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        raise Exception(f"Error in API call: {response.status_code} - {response.text}")