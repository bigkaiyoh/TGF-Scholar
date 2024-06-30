import streamlit as st
from openai import OpenAI
import time
from PIL import Image
import base64
import requests
import io

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
        with st.spinner('One moment...'):
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
    
# -------------- OCR function -----------------------

# def transcribe_file(uploaded_file):
#     # Determine the file type and process accordingly
#     file_type = uploaded_file.type
#     if file_type == "application/pdf":
#         return transcribe_pdf(uploaded_file)
#     elif file_type in ["image/jpeg", "image/png"]:
#         return transcribe_image(uploaded_file)
#     else:
#         return ""

# def transcribe_image(uploaded_file):
#     # Convert the uploaded file to a PIL Image object
#     image = Image.open(uploaded_file)
#     return pytesseract.image_to_string(image)

# def transcribe_pdf(pdf_file):
#     pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
#     text = ""
#     for page_num in range(len(pdf_document)):
#         page = pdf_document.load_page(page_num)
#         pix = page.get_pixmap()
#         img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
#         page_text = pytesseract.image_to_string(img)
#         text += page_text
#     return text

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