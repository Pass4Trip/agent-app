import base64
from os import getenv
from io import BytesIO
from typing import List

import nest_asyncio
import streamlit as st
from PIL import Image
from phi.agent import Agent
from phi.document import Document
from phi.document.reader import Reader
from phi.document.reader.website import WebsiteReader
from phi.document.reader.pdf import PDFReader
from phi.document.reader.text import TextReader
from phi.document.reader.docx import DocxReader
from phi.document.reader.csv_reader import CSVReader
from phi.tools.streamlit.components import (
    check_password,
    get_openai_key_sidebar,
    get_username_sidebar,
)
from phi.utils.log import logger


from agents.agent_leader import get_agent_leader



#from app.audio import record_audio
#from app.config import Config

from st_audiorec import st_audiorec


from audio_recorder_streamlit import audio_recorder
from transcription import transcribe_audio



nest_asyncio.apply()
st.set_page_config(
    page_title="MyBoun",
    page_icon=":orange_heart:",
)
st.title("MyBoun")
#st.markdown("##### :orange_heart: built using [phidata](https://github.com/phidatahq/phidata)")


def restart_agent():
    logger.debug("---*--- Restarting Agent ---*---")
    st.session_state["agent_leader"] = None
    st.session_state["uploaded_image"] = None
    if "url_scrape_key" in st.session_state:
        st.session_state["url_scrape_key"] += 1
    if "file_uploader_key" in st.session_state:
        st.session_state["file_uploader_key"] += 1
    if "image_uploader_key" in st.session_state:
        st.session_state["image_uploader_key"] += 1
    st.rerun()


def encode_image(image_file):
    image = Image.open(image_file)
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    encoding = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoding}"



def main() -> None:
    # Record audio from the microphone and save it as 'test.wav'
    #record_audio(INPUT_AUDIO)    
    
    # Get Model Id
    # with st.sidebar:
    #     wav_audio_data = st_audiorec()

    #     if wav_audio_data is not None:
    #         st.audio(wav_audio_data, format='audio/wav')
            
 
    # Get OpenAI key from environment variable or user input
    get_openai_key_sidebar()

    # Get username
    # username = "streamlit" if getenv("RUNTIME_ENV") == "dev" else get_username_sidebar()
    # if username:
    #     st.sidebar.info(f":technologist: User: {username}")
    # else:
    #     st.markdown("---")
    #     st.markdown("#### :technologist: Please enter a username")
    #     return

    # Get Model Id
    # model_id = st.sidebar.selectbox("Model", options=["gpt-4o-mini"])
    # Set model_id in session state
    # if "model_id" not in st.session_state:
    #     st.session_state["model_id"] = model_id
    # # Restart the agent if model_id has changed
    # elif st.session_state["model_id"] != model_id:
    #     st.session_state["model_id"] = model_id
    #     restart_agent()

    model_id ="gpt-4o-mini"

    with st.sidebar:
        audio_bytes = audio_recorder() 



    # Get the Agent
    agent_leader: Agent
    if "agent_leader" not in st.session_state or st.session_state["agent_leader"] is None:
        logger.info(f"---*--- Creating {model_id} Agent ---*---")
        agent_leader = get_agent_leader(model_id=model_id, debug_mode=True)
        st.session_state["agent_leader"] = agent_leader
    else:
        agent_leader = st.session_state["agent_leader"]

    # Create Agent session (i.e. log to database) and save session_id in session state
    try:
        st.session_state["rag_restaurant_searcher_session_id"] = agent_leader.create_session()
    except Exception:
        st.warning("Could not create Agent session, is the database running?")
        return


        
    # Store uploaded image in session state
    uploaded_image = None
    if "uploaded_image" in st.session_state:
        uploaded_image = st.session_state["uploaded_image"]

    # Load existing messages
    agent_chat_history = agent_leader.memory.get_messages()
    if len(agent_chat_history) > 0:
        logger.debug("Loading chat history")
        st.session_state["messages"] = agent_chat_history
        # Search for uploaded image
        if uploaded_image is None:
            for message in agent_chat_history:
                if message.get("role") == "user":
                    content = message.get("content")
                    if isinstance(content, list):
                        for item in content:
                            if item["type"] == "image_url":
                                uploaded_image = item["image_url"]["url"]
                                st.session_state["uploaded_image"] = uploaded_image
                                break
    else:
        logger.debug("No chat history found")
        st.session_state["messages"] = [{"role": "assistant", "content": "Bonjour je suis MyBoun ton compagnon..."}]


   


    if audio_bytes:
        ##Save the Recorded File
        audio_location = "app/audio_file4.wav"
        with open(audio_location, "wb") as f:
            f.write(audio_bytes)

        #Transcribe the saved file to text
        prompt = transcribe_audio(audio_location)
        st.session_state["messages"] = [{"role": "user", "content": prompt}]



    
    # Upload Image
    if uploaded_image is None:
        if "image_uploader_key" not in st.session_state:
            st.session_state["image_uploader_key"] = 200
        uploaded_file = st.sidebar.file_uploader(
            "Upload Image",
            key=st.session_state["image_uploader_key"],
        )
        if uploaded_file is not None:
            alert = st.sidebar.info("Processing Image...", icon="ℹ️")
            image_file_name = uploaded_file.name.split(".")[0]
            if f"{image_file_name}_uploaded" not in st.session_state:
                logger.info(f"Encoding {image_file_name}")
                uploaded_image = encode_image(uploaded_file)
                st.session_state["uploaded_image"] = uploaded_image
                st.session_state[f"{image_file_name}_uploaded"] = True
            alert.empty()

    # Prompt for user input
    if uploaded_image:
        with st.expander("Uploaded Image", expanded=False):
            st.image(uploaded_image, use_column_width=True)
            
    if prompt := st.chat_input():
        st.session_state["messages"].append({"role": "user", "content": prompt})

    # Display existing chat messages
    for message in st.session_state["messages"]:
        # Skip system and tool messages
        if message.get("role") in ["system", "tool"]:
            continue
        # Display the message
        message_role = message.get("role")
        if message_role is not None:
            with st.chat_message(message_role):
                content = message.get("content")
                if isinstance(content, list):
                    for item in content:
                        if item["type"] == "text":
                            st.write(item["text"])
                        elif item["type"] == "image_url":
                            st.image(item["image_url"]["url"], use_column_width=True)
                else:
                    st.write(content)

    # If last message is from a user, generate a new response
    last_message = st.session_state["messages"][-1]
    if last_message.get("role") == "user":
        question = last_message["content"]
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                resp_container = st.empty()
                response = ""
                for delta in agent_leader.run(
                    message=question, images=[uploaded_image] if uploaded_image else [], stream=True
                ):
                    response += delta.content  # type: ignore
                    resp_container.markdown(response)
            st.session_state["messages"].append({"role": "assistant", "content": response})

    # Load knowledge base
    if agent_leader.knowledge:
        # -*- Add websites to knowledge base
        if "url_scrape_key" not in st.session_state:
            st.session_state["url_scrape_key"] = 0
        input_url = st.sidebar.text_input(
            "Add URL to Knowledge Base", type="default", key=st.session_state["url_scrape_key"]
        )
        add_url_button = st.sidebar.button("Add URL")
        if add_url_button:
            if input_url is not None:
                alert = st.sidebar.info("Processing URLs...", icon="ℹ️")
                if f"{input_url}_scraped" not in st.session_state:
                    scraper = WebsiteReader(max_links=2, max_depth=1)
                    web_documents: List[Document] = scraper.read(input_url)
                    if web_documents:
                        agent_leader.knowledge.load_documents(web_documents, upsert=True)
                    else:
                        st.sidebar.error("Could not read website")
                    st.session_state[f"{input_url}_uploaded"] = True
                alert.empty()

        # -*- Add documents to knowledge base
        if "file_uploader_key" not in st.session_state:
            st.session_state["file_uploader_key"] = 100
        uploaded_file = st.sidebar.file_uploader(
            "Add a Document (.pdf, .csv, .txt, or .docx)",
            key=st.session_state["file_uploader_key"],
        )
        if uploaded_file is not None:
            alert = st.sidebar.info("Processing document...", icon="🧠")
            document_name = uploaded_file.name.split(".")[0]
            if f"{document_name}_uploaded" not in st.session_state:
                file_type = uploaded_file.name.split(".")[-1].lower()

                reader: Reader
                if file_type == "pdf":
                    reader = PDFReader()
                elif file_type == "csv":
                    reader = CSVReader()
                elif file_type == "txt":
                    reader = TextReader()
                elif file_type == "docx":
                    reader = DocxReader()
                auto_rag_documents: List[Document] = reader.read(uploaded_file)
                if auto_rag_documents:
                    agent_leader.knowledge.load_documents(auto_rag_documents, upsert=True)
                else:
                    st.sidebar.error("Could not read document")
                st.session_state[f"{document_name}_uploaded"] = True
            alert.empty()

        if agent_leader.knowledge.vector_db:
            if st.sidebar.button("Delete Knowledge Base"):
                agent_leader.knowledge.vector_db.delete()
                st.sidebar.success("Knowledge base deleted")

    if agent_leader.storage:
        rag_restaurant_searcher_session_ids: List[str] = agent_leader.storage.get_all_session_ids()
        new_rag_restaurant_searcher_session_id = st.sidebar.selectbox("Session ID", options=rag_restaurant_searcher_session_ids)
        if st.session_state["rag_restaurant_searcher_session_id"] != new_rag_restaurant_searcher_session_id:
            logger.info(f"---*--- Loading {model_id} session: {new_rag_restaurant_searcher_session_id} ---*---")
            st.session_state["agent_leader"] = get_agent_leader(
                model_id=model_id, session_id=new_rag_restaurant_searcher_session_id, debug_mode=True
            )
            st.session_state["rag_restaurant_searcher_session_id"] = new_rag_restaurant_searcher_session_id
            st.session_state["uploaded_image"] = None
            st.rerun()

    if st.sidebar.button("New Session"):
        restart_agent()


if check_password():
    main()