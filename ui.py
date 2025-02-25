import streamlit as st
from main import invokeChatbot
from time import sleep

st.title("Medical Chatbot")

if "messages" not in st.session_state:
    sleep(0.5)
    st.session_state.messages = [{"role": "ai", "content": "Hello! Im here to assist you with your medical queries."}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input(placeholder="Send your query"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Thinking..."):
        response = invokeChatbot(prompt)

    st.session_state.messages.append({"role": "ai", "content": response})
    with st.chat_message("ai"):
        st.markdown(response)
