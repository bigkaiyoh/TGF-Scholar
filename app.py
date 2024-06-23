import streamlit as st
from modules import run_assistant 

#Initialize assistant
assistant = st.secrets.Unicke_id


st.set_page_config(
    page_title = "国内大学英語プログラム志望動機支援",
    page_icon = "🎓",
    layout = "wide"
)

def get_input():
    #input 画面
    uni_name = st.text_input("志望校を教えてください")
    program_name = st.text_input("学部名を教えてください")
    txt = st.text_area("志望動機書を添付してください")
    st.write(f'{len(txt.split())} 文字')

    information = "University: " + uni_name + "\n" + "Program: " + program_name + "\n\n" + "Writing: " + txt
    return information

def main():
    st.title("英語プログラムにっけ")

    information = get_input()
    
    # 提出ボタン
    submit_button = st.button("採点")

    #評価表示画面
    if submit_button:
        run_assistant(assistant_id=assistant, txt=information)


if __name__ == "__main__":
    main()