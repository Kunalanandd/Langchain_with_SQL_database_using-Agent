import streamlit as st
from  pathlib import Path
from langchain_community.agent_toolkits import create_sql_agent
from langchain_classic.sql_database import SQLDatabase
from langchain_classic.agents.agent_toolkits import SQLDatabaseToolkit
from langchain_classic.agents.agent_types import AgentType
from langchain_classic.callbacks import StreamlitCallbackHandler
from sqlalchemy import create_engine
import sqlite3
from langchain_openai import ChatOpenAI


st.set_page_config(page_title="Langchain with SQL database",page_icon="🤖")
st.title("🤖 Langchain: chat with SQL Database")


LOCALDB = "USE _LOCALDB"
MYSQL = "USE _MYSQL"


## radio 
radio_opt = ["Use SQLlite 3 Database-student.db","connect to your Sql database"]

selected_opt = st.sidebar.radio(label="Choose the DB which you want to chat",options=radio_opt)


if radio_opt.index(selected_opt) == 1:
    db_uri = MYSQL
    mysql_host = st.sidebar.text_input("Provide MYSQL Host")
    mysql_user = st.sidebar.text_input("Provide MYSQL User")
    mysql_password = st.sidebar.text_input("Provide MYSQL password",type="password")
    mysql_db = st.sidebar.text_input("Provide MYSQL Database")

else:
    db_uri = LOCALDB

api_key = st.sidebar.text_input(label="OpenAI api key ", type="password")

if not db_uri:
    st.info("Please enter your Sql database information")


if not api_key:
    st.info("Please enter your OpenAI api key")

llm = ChatOpenAI(api_key=api_key,streaming=True)

@st.cache_resource(ttl="3h")
def configure_db(db_uri,mysql_host=None,mysql_user=None,mysql_password=None,mysql_db=None):
    if db_uri == LOCALDB:
        dbfilepath = (Path(__file__).parent/"student.db").absolute()
        print(dbfilepath)
        creator = lambda:sqlite3.connect(f"file:{dbfilepath}?mode=ro",uri=True)
        return  SQLDatabase(create_engine("sqlite:///",creator=creator))
    elif db_uri == MYSQL:
        if not (mysql_host and mysql_user and mysql_password and mysql_db):
            st.error("Please provide all information of your sql database")
            st.stop()
        return SQLDatabase(create_engine(f"mysql+mysqlconnector://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_db}"))
if db_uri==MYSQL:
    db = configure_db(db_uri,mysql_host,mysql_user,mysql_password,mysql_db)
else:
    db = configure_db(db_uri)


## toolkit 

toolkit =SQLDatabaseToolkit(db=db,llm=llm)
agent = create_sql_agent(
    llm = llm,
    toolkit=toolkit,
    verbose=True,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION)


if 'messages' not in st.session_state or st.sidebar.button("Clear chat history"):
    st.session_state['messages']=[{"role":'assistant',"content":"How can i help you?"}]
for msg in st.session_state.messages:
    st.chat_message(msg['role']).write(msg['content'])

user_query = st.chat_input(placeholder='Ask anythink from the database')

if user_query:
    st.session_state.messages.append({"role":"user","content":user_query})
    st.chat_message("user").write(user_query)

    with st.chat_message("assistant"):
        streamlit_Callback = StreamlitCallbackHandler(st.container())
        response = agent.run(user_query,callbacks=[streamlit_Callback])
        st.session_state.messages.append({"role":"assistant","content":response})
        st.write(response)




