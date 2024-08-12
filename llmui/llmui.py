import streamlit as st
from langchain_openai import ChatOpenAI
import os
import pickle
import sqlite3
import json

from typing import Annotated, Dict,Any, List, Literal, Optional, Union, TypedDict
from langchain.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from uuid import UUID
from streamlit_option_menu import option_menu
# st.set_page_config(layout="wide")

import sqlite3

def create_tables(conn):
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            llm_config TEXT,
            password TEXT DEFAULT '111111',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS session_details (
            detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            detail_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        )
    ''')
    conn.commit()

def add_user(conn, username, ll_config=None,passowrd='111111'):
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, llm_config,password) VALUES (?, ?,?)', (username, ll_config,passowrd))
    except Exception as e:
        raise e
    finally:
        conn.commit()
    return c.lastrowid

def update_user(conn, user_id, **kwargs):
    c = conn.cursor()
    set_clause = ', '.join([f'{k} = ?' for k in kwargs])
    try:
        c.execute(f'UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?', (*kwargs.values(), user_id))
    except Exception as e:
        raise e
    finally:
        conn.commit()
    

def delete_user(conn, user_id):
    c = conn.cursor()
    try:
        c.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
    except Exception as e:
        raise e
    finally:
        conn.commit()

def get_user_info(conn, user_id):
    c = conn.cursor()
    c.execute(f'SELECT * FROM users where user_id = ?', (str(user_id)))
    return c.fetchall()

def list_users(conn, order_by='updated_at', reverse=True):
    c = conn.cursor()
    order = 'DESC' if reverse else 'ASC'
    c.execute(f'SELECT * FROM users ORDER BY {order_by} {order}')
    return c.fetchall()

def add_session(conn, user_id, session_name):
    c = conn.cursor()
    
    try:
        c.execute('INSERT INTO sessions (user_id, session_name) VALUES (?, ?)', (user_id, session_name))
    except Exception as e:
        raise e
    finally:
        conn.commit()
    return c.lastrowid

def get_newest_session(conn, user_id, order_by='updated_at'):
    c = conn.cursor()
    c.execute(f'SELECT * FROM sessions WHERE user_id = ? ORDER BY {order_by} desc limit 1', (user_id,))
    return c.fetchall()

def get_session_name(conn, session_id):
    c = conn.cursor()
    c.execute(f'SELECT * FROM sessions WHERE session_id = ? ', (session_id,))
    return c.fetchall()

def list_sessions(conn, user_id, order_by='updated_at', reverse=True):
    c = conn.cursor()
    order = 'DESC' if reverse else 'ASC'
    c.execute(f'SELECT * FROM sessions WHERE user_id = ? ORDER BY {order_by} {order}', (user_id,))
    return c.fetchall()

def delete_session(conn, session_id):
    c = conn.cursor()
    
    try:
        c.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
    except Exception as e:
        raise e
    finally:
        conn.commit()

def update_session_name(conn, session_id, new_name):
    c = conn.cursor()
    try:
        c.execute('UPDATE sessions SET session_name = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?', (new_name, session_id))
    except Exception as e:
        raise e
    finally:
        conn.commit()


def add_session_detail(conn, session_id, detail_data):
    c = conn.cursor()
    
    try:
        c.execute('INSERT INTO session_details (session_id, detail_data) VALUES (?, ?)', (session_id, detail_data))
    except Exception as e:
        raise e
    finally:
        conn.commit()
    return c.lastrowid

def update_session_detail(conn, session_id, new_data):
    c = conn.cursor()
    try:
        c.execute('UPDATE session_details SET detail_data = ? , updated_at = CURRENT_TIMESTAMP WHERE session_id = ?', (new_data, session_id))
    except Exception as e:
        raise e
    finally:
        conn.commit()

def get_session_details(conn, session_id):
    c = conn.cursor()
    c.execute(f'SELECT * FROM session_details WHERE session_id = ?', (session_id,))
    return c.fetchall()

def list_session_details(conn, session_id, order_by='updated_at', reverse=True):
    c = conn.cursor()
    order = 'DESC' if reverse else 'ASC'
    c.execute(f'SELECT * FROM session_details WHERE session_id = ? ORDER BY {order_by} {order}', (session_id,))
    return c.fetchall()

st.session_state['db_conn'] = sqlite3.connect('user_sessions.db')
conn = st.session_state['db_conn'] 
create_tables(conn)
conn.execute('PRAGMA foreign_keys = ON;')
conn.commit()

class LLMConsoleIOHandler(BaseCallbackHandler):
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        if self.is_verbose:
            print(f"{token}",end='')
       
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], *, run_id: UUID, parent_run_id: UUID | None = None, tags: List[str] | None = None, metadata: Dict[str, Any] | None = None, **kwargs: Any) -> Any:
        if self.is_verbose:
            print("\n-------------LLM-start--------------------")
            print("prompts:",'\n'.join(prompts))
    

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, parent_run_id: UUID | None = None, **kwargs: Any) -> Any:
        if self.is_verbose:
            print("\n-------------LLM-complete--------------------")

    def set_verbose(self, is_verbose):
        self.is_verbose = is_verbose


if 'login_user_id' not in st.session_state:
    # Login form
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    col_login , col_register,_,_ = st.columns(4)
    if col_login.button("Login"):
        # Authenticate the user
        all_users = list_users(conn)
        user = next((u for u in all_users if u[1] == username and u[3] == password), None)
        if user:
            st.session_state['login_user_id'] = user[0]
            st.session_state['login_user_name'] = user[1]
            st.session_state['user_id'] =  st.session_state['login_user_id']
            st.session_state['user_name'] = st.session_state['login_user_name']
            st.success("Logged in as {}".format(username))
            # Redirect to the main page after login
            st.rerun()
        else:
            st.error("Invalid username or password, try to register a user before login")
    # Register button
    if col_register.button("Register"):
        # Check if the username already exists
        all_users = list_users(conn)
        if any(u[1] == username for u in all_users):
            st.error("Username already exists. Please choose a different username.")
        else:
            # Add the new user to the database
            add_user(conn, username, None, password)
            st.success("Registration successful!")
else:
    with st.sidebar:
        col3,col4 = st.columns(2)
        with col3:
            st.markdown('### current user:')
        with col4:
            all_users = list_users(conn)
            if st.session_state['login_user_name'] == 'root':
                selected_user = st.selectbox('当前用户',options=[u for u in all_users],format_func=lambda i:i[1], label_visibility='collapsed')
                if selected_user and ('user_id' not in st.session_state or selected_user[0] != st.session_state['user_id']): 
                    st.session_state['user_name'] = selected_user[1]
                    st.session_state['user_id'] = selected_user[0]
            else:
                st.markdown('### ***'+st.session_state['user_name'] +'***')
            

        new_session = st.button(" new session ")
        if new_session:
            if  st.session_state["messages"]:
                if 'user_id' in st.session_state:
                    st.session_state['session_id'] = add_session(conn, user_id=st.session_state['user_id'], session_name='empty session')
                    add_session_detail(conn, st.session_state['session_id'] ,'[]')
                    st.session_state["messages"] = []
                else:
                    st.warning('select or register a user first!')


        with st.container(height=353,border=False):
            if 'user_id' not in st.session_state:
                st.info('please select a user first')
            else:
                if 'access_count' not in st.session_state:
                    st.session_state['access_count'] = 0
                    newest_session = get_newest_session(conn, user_id=st.session_state['user_id'])
                    if not newest_session or newest_session and newest_session[0][2] != 'empty session':
                        st.session_state['session_id'] = add_session(conn, user_id=st.session_state['user_id'], session_name='empty session')
                        add_session_detail(conn, st.session_state['session_id'] ,'[]')
                chat_sessions = list_sessions(conn, st.session_state['user_id'])
                session_name_map = {}
                chat_session_options = []
                manual_select_index = 0
                for e in chat_sessions:
                    if e[2] not in session_name_map:
                        session_name_map[e[2]]=[e[0],0]
                        chat_session_options.append(e[2])
                    else:
                        session_name_map[e[2]][1]+=1
                        new_name = f'{e[2]}-{session_name_map[e[2]][1]}'
                        session_name_map[new_name] = (e[0],0)
                        chat_session_options.append(new_name)
                if chat_sessions:
                    selected_session = option_menu("", chat_session_options,icons=['chat']*len(chat_session_options), default_index=0)
                    if selected_session:
                        st.session_state['session_id'] = session_name_map[selected_session][0]
                        history_sesssion_detail = get_session_details(conn, st.session_state['session_id'] )
                        st.session_state["messages"] = []
                        if history_sesssion_detail and history_sesssion_detail[0][2]:
                            st.session_state["messages"] = json.loads(history_sesssion_detail[0][2])

        st.divider() 

        llm_host=None
        llm_port = None
        llm_model_name = None
        if 'user_id' in st.session_state:
            user_config = get_user_info(conn, st.session_state['user_id'])
            if user_config and user_config[0][2]:
                cur_llm_config = json.loads(user_config[0][2])
                llm_host=cur_llm_config['llm_host']
                llm_port = cur_llm_config['llm_port']
                llm_model_name = cur_llm_config['llm_model_name']
        if not llm_host:
            llm_host=os.getenv("LLM_HOST")
        if not llm_port:
            llm_port = os.getenv("LLM_PORT")
        if not llm_model_name:
            llm_model_name = os.getenv("LLM_MODEL_NAME")

        with st.expander('⚙️Config Openai compatible service',expanded=False):
            llm_host_cur = st.text_input("LLM service host ip",placeholder=llm_host if llm_host else "LLM service host ip")
            if llm_host_cur:
                llm_host = llm_host_cur 
            llm_port_cur = st.text_input("LLM service host port",placeholder=llm_port if llm_port else "LLM service host port")
            if llm_port_cur:
                llm_port = llm_port_cur
            llm_model_name_cur = st.text_input("LLM model name",placeholder=llm_model_name if llm_model_name else "LLM model name")
            if llm_model_name_cur:
                llm_model_name = llm_model_name_cur
            openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
            save_config = st.button('save current config')
            if save_config:
                llm_config = {
                    "llm_host":llm_host,
                    "llm_port":llm_port,
                    "llm_model_name":llm_model_name,
                    "openai_api_key":openai_api_key}
                try:
                    if 'user_id' in st.session_state:
                        update_user(conn,  st.session_state['user_id']  , llm_config = json.dumps(llm_config))
                        st.info("current config saved!")
                    else:
                        st.warning("select or register a user first!")
                except Exception as e:
                    st.error('save config error:'+str(e))
        with st.expander('⚙️User Management',expanded=False):
            st.markdown('#### Change current user password')
            old_password = st.text_input("old password", type="password").strip()
            new_password = st.text_input("new password", type="password").strip()
            if st.button("change password"):
                all_users = list_users(conn)
                user = next((u for u in all_users if u[1] == st.session_state['user_name'] and u[3] == old_password), None)
                if user or st.session_state['login_user_name']=='root':
                    update_user(conn, st.session_state['user_id'],password = new_password)
                    st.info("password updated!")
                else:
                    st.error("Invalid username or old password")

            if st.session_state['login_user_name']=='root':
                st.markdown('#### Delete current user')
                delete_user_button = st.button('Delete user')
                if delete_user_button:
                    if 'user_id' not in st.session_state:
                        st.info('No chat session selected~')
                    elif st.session_state['user_name'] == 'root':
                        st.info('root user cannot be deleted~')
                    else:
                        delete_user(conn, st.session_state['user_id'])
                        del st.session_state['user_id'] 
                        st.info('deleted user: '+st.session_state['user_name'] )
                        del st.session_state['user_name'] 
                        st.rerun()
            if st.button("Logout"):
                for k in st.session_state:
                    del st.session_state[k]
                st.rerun()
        st.divider()
        col5,col6 = st.columns(2)
        with col5:
            clean = st.button('clean history')
            if clean:
                if 'session_id' in st.session_state:
                    st.session_state["messages"] = []
                    update_session_detail(conn, st.session_state['session_id'],'[]')
                    update_session_name(conn ,st.session_state['session_id'],'empty session')
                    st.rerun()
        with col6:
            delete_button = st.button('Delete Session')
            if delete_button:
                if 'session_id' not in st.session_state:
                    st.info('No chat session selected~')
                else:
                    delete_session(conn, st.session_state['session_id'])
                    st.session_state['messages'] = []
                    st.rerun()


    st.title("💬 Chatbot")



    @st.cache_resource
    def get_llm(llm_host,llm_port,llm_model_name, openai_api_key):
        llm_cfg = {
            "OPENAI_API_BASE":f"http://{llm_host}:{llm_port}/v1",
            "OPENAI_API_KEY" : 'skxxx' if not openai_api_key else openai_api_key,
            "OPENAI_MODEL" : llm_model_name,
            "TOKENIZE_MODEL" : "gpt-4",
            "TIKTOKEN_CACHE_DIR":"/root/llm_cache/tiktoken/",
            "VERBOSE":True,
            "TEMPERATURE":0.0,
        } 
        handler = LLMConsoleIOHandler()
        handler.set_verbose(True)
        if not (llm_host and llm_port):
            llm = ChatOpenAI( 
                openai_api_key=llm_cfg["OPENAI_API_KEY"],
                streaming=True,
                # verbose=llm_cfg["VERBOSE"],
                callbacks=[handler],
                openai_api_base=llm_cfg["OPENAI_API_BASE"],
                # openai_proxy=config.get("openai_proxy"),
                temperature=llm_cfg["TEMPERATURE"]
                # max_tokens=812,
            )
        llm = ChatOpenAI( 
                openai_api_key=llm_cfg["OPENAI_API_KEY"],
                model_name=llm_cfg["OPENAI_MODEL"],
                streaming=True,
                # verbose=llm_cfg["VERBOSE"],
                callbacks=[handler],
                openai_api_base=llm_cfg["OPENAI_API_BASE"],
                # openai_proxy=config.get("openai_proxy"),
                temperature=llm_cfg["TEMPERATURE"]
                # max_tokens=812,
            )
        return llm

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    prompt = st.chat_input() 

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt:
        if not (llm_host and llm_port and llm_model_name or openai_api_key):
            st.info("Please config your llm")
            st.stop()
        llm = get_llm(llm_host,llm_port,llm_model_name, openai_api_key)
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        llm_iter = llm.stream(st.session_state.messages)
        response = st.chat_message("assistant").write_stream(llm_iter)
        st.session_state.messages.append({"role": "assistant", "content": response})
        # if 'session_id' not in st.session_state:
        #     if 'user_id' in st.session_state:
        #         st.session_state['session_id'] = add_session(conn, user_id=st.session_state['user_id'], session_name=st.session_state.messages[0]['content'][:23])
        #         add_session_detail(conn,st.session_state['session_id'],json.dumps(st.session_state.messages))
        #         st.rerun()
        #     else:
        #         st.info('please select or register a user first')
        # else:
        s_name = get_session_name(conn,st.session_state['session_id'])[0][2]
        update_session_detail(conn, st.session_state['session_id'],json.dumps(st.session_state.messages))
        update_session_name(conn,st.session_state['session_id'], st.session_state.messages[0]['content'][:23])
        if s_name == 'new session' or  chat_session_options.index(selected_session)>0 or s_name == 'empty session':
            st.rerun()
    
