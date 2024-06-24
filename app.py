import streamlit as st
from modules import run_assistant

# Initialize assistant
assistant = st.secrets.Unicke_id

st.set_page_config(
    page_title="英語志望動機書対策ニッケ",
    page_icon="🎓",
    layout="wide"
)

def get_input():
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("基本情報")
        uni_name = st.text_input("志望校名", placeholder="例: 早稲田大学")
        program_name = st.text_input("学部名", placeholder="例: SILS")
    
    with col2:
        st.subheader("志望動機書")
        txt = st.text_area("こちらに志望動機書を入力してください", height=200)
        st.write(f'現在の文字数: {len(txt.split())} 文字')

    information = f"University: {uni_name}\nProgram: {program_name}\n\nWriting: {txt}"
    return information, uni_name, program_name, txt


def main():
    st.title("🎓 英語志望動機書対策ニッケ")
    st.markdown("このアプリは、あなたの英語の志望動機書を評価し、フィードバックを提供します。")

    with st.expander("使い方", expanded=True):
        st.markdown("""
        1. 志望校名と学部名を入力してください。
        2. 志望動機書を入力欄に貼り付けるか直接入力してください。
        3. 「採点する」ボタンをクリックして、AIによる評価を受けてください。
        """)

    information, uni_name, program_name, txt = get_input()
    
    # 提出ボタン
    submit_button = st.button("採点する", type="primary")

    # 評価表示画面
    if submit_button:
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
        
        # Display feedback in a styled box with background color
        st.markdown(f"""
            <div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; background-color: #e8f4f8;">
                {feedback}
            </div>
        """, unsafe_allow_html=True)



if __name__ == "__main__":
    main()