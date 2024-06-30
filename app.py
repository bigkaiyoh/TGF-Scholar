import streamlit as st
from modules import run_assistant, convert_image_to_text
from vocabvan import vocabvan_interface
import json

# Load the university data from the JSON file
with open('programs.json', 'r') as f:
    data = json.load(f)
# Extract the university names and programs
uni_names = [uni["name"] for uni in data["universities"]] + ["Other"]


# Initialize assistant
assistant = st.secrets.Unicke_id

# Initialize session state
if 'txt' not in st.session_state:
    st.session_state.txt = ""
if 'transcription_done' not in st.session_state:
    st.session_state.transcription_done = False

st.set_page_config(
    page_title="英語志望動機書対策ニッケ",
    page_icon="🎓",
    layout="wide"
)

# Custom CSS for improved styling
st.markdown("""
<style>
    .main-title {
        font-size: 50px;
        text-align: center;
        color: #0097b2;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


def get_input():
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.subheader("基本情報")

        # Create a select box for university names
        uni_name = st.selectbox("志望校名", options=uni_names)

        # Based on the selected university, create a select box for program names
        program_name = ""
        for uni in data["universities"]:
            if uni["name"] == uni_name:
                program_name = st.selectbox("学部名", options=uni["programs"] + ["Other"]) 
                break

        # File uploader for additional input method with help text
        uploaded_file = st.file_uploader(
            "ファイルをアップロードしてください",
            type=["pdf", "jpg", "jpeg", "png"],
            help="手書きの志望動機書やPDFファイルを評価するためにご利用ください"
        )
        
        if uploaded_file is not None and not st.session_state.transcription_done:
            # Transcribe the uploaded file
            with st.spinner("Reading..."):
                try:
                    result = convert_image_to_text(uploaded_file)
                    st.session_state.txt = result  # Update session state
                    st.session_state.transcription_done = True
                    st.success("Transcription completed successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

    
    with col2:
        st.subheader("志望動機書")
        txt = st.text_area("こちらに志望動機書を入力してください", height=220, value = st.session_state.txt)
        st.info(f'現在の文字数: {len(txt.split())} 文字')


    information = f"University: {uni_name}\nProgram: {program_name}\n\nWriting: {txt}"
    return information, uni_name, program_name, txt


def main():
    st.markdown("<h1 class='main-title'>🎓 英語志望動機書対策ニッケ</h1>", unsafe_allow_html=True)
    st.info("このアプリは、あなたの英語の志望動機書を評価し、フィードバックを提供します。")

    with st.expander("📌使い方", expanded=True):
        st.markdown("""
        1. 志望校名と学部名を入力してください。
        2. 志望動機書を入力欄に貼り付けるか直接入力してください。  
        (ファイルをアップロードで手書き文章やPDFの添削も行えます)  
        3. 「採点する」ボタンをクリックして、AIによる評価を受けてください。
        """)

    # Chatbot Button and Popover
    with st.popover("🧠 AIに質問"):
        vocabvan_interface()

    information, uni_name, program_name, txt = get_input()
    
    # 提出ボタン
    submit_button = st.button("採点する🚀", type="primary")

    # 評価表示画面
    if submit_button:
        # Reset transcription_done to False
        st.session_state.transcription_done = False  

        with st.expander("入力内容", expanded=False):
            st.write(f"**志望校名**: {uni_name}")
            st.write(f"**学部名**: {program_name}")
            st.write("**志望動機書**:")
            
            # Use markdown to display the text in a styled box
            box_content = txt.replace('\n', '<br>')
            st.markdown(f"""
                <div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; background-color: #f9f9f9;">
                    {box_content}
                </div>
            """, unsafe_allow_html=True)
            
            st.write(f'文字数: {len(txt.split())} 文字')
        
        st.subheader("AIからのフィードバック")
        feedback = run_assistant(assistant_id=assistant, txt=information, return_content=True, display_chat=False)
        st.success("評価が完了しました！")

        # Display feedback in a styled box with background color
        st.markdown(f"""
            <div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; background-color: #e8f4f8;">
                {feedback}
            </div>
        """, unsafe_allow_html=True)


    


if __name__ == "__main__":
    main()