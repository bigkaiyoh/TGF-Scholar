import streamlit as st
from modules import run_assistant

def vocabvan_interface():
    assistant = st.secrets.AI_uKnow

    user_input = st.chat_input("疑問を入力してください")
    
    temporary = st.empty()
    t = temporary.container()
    
    with t:
        st.write("志望動機書のチェックや英語表現のアドバイスが必要な場合にご利用ください。")
        m1 = st.chat_message("user")
        a1 = st.chat_message("assistant")
        m2 = st.chat_message("user")
        a2 = st.chat_message("assistant")
        m3 = st.chat_message("user")
        a3 = st.chat_message("assistant")
        
        m1.write("志望動機書の書き出しに困っています。")
        a1.write(""" 1. I am writing to express my sincere interest in the [Program Name] at [University Name].
2. It is with great enthusiasm that I submit my application for the [Program Name] at [University Name].
3. I am eager to join the [Program Name] at [University Name] because of my passion for [Field of Study]. """)
        
        m2.write("志望動機書で自分の強みをどう表現すれば良いでしょうか？")
        a2.write(""" 1. My strongest attribute is my ability to [Specific Skill], which I developed through [Experience].
2. I excel in [Specific Skill], a strength that has been honed through my involvement in [Experience].
3. One of my key strengths is [Specific Skill], which I have continuously improved upon during my time at [Previous Institution or Job]. """)
        
        m3.write("第一志望だと伝えたい")
        a3.write(""" 1. [University Name] is my top choice because of its excellent [Program Name] and the opportunities it offers in [Field of Study].
2. Among all the universities I have considered, [University Name] stands out as my first choice due to its outstanding [Program Name] and innovative approach.
3. I have thoroughly researched many universities, and [University Name] is my number one choice because of its strong emphasis on [Field of Study] and commitment to [Relevant Value or Opportunity]. """)
    
    if user_input:
        temporary.empty()
        run_assistant(assistant_id=assistant, txt=user_input)

    return user_input