import streamlit as st
import pandas as pd
import json
import _snowflake
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import col, lit, concat_ws, lower

st.title('Chat with your Cortex Agent! :ninja:')

# Configuration
API_ENDPOINT = "/api/v2/cortex/agent:run"
API_TIMEOUT = 50000  # in milliseconds
MAX_DATAFRAME_ROWS = 1000
session = get_active_session()

@st.cache_data
def get_stages():
    stages = (
        session.sql('SHOW STAGES IN ACCOUNT')
        .filter(col('"type"') == 'INTERNAL NO CSE')
        .select(
            col('"database_name"').alias('"Database"'),
            col('"schema_name"').alias('"Schema"'),
            col('"name"').alias('"Stage"')
        )
        .distinct()
        .order_by(['"Database"','"Schema"','"Stage"'])
    ).to_pandas()
    return stages

@st.cache_data
def get_files_from_stage(database, schema, stage):
    try:
        files = (
            session.sql(f'LS @"{database}"."{schema}"."{stage}"')
            .filter(col('"size"') < 1000000)
            .filter(
                (lower(col('"name"')).endswith('.yaml')) | 
                (lower(col('"name"')).endswith('.yml'))
            )
            .select(
                col('"name"').alias('"File Name"'),
            )
            .distinct()
            .order_by(['"File Name"'])
        ).to_pandas()
    except Exception as e:
        st.error(e)
        return 
    return files


if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'api_history' not in st.session_state:
    st.session_state.api_history = []
    
if 'analyst_services' not in st.session_state:    
    available_services = pd.DataFrame(
        columns=['Active', 'Name', 'Database','Schema','Stage','File']
        )
    st.session_state['analyst_services'] = available_services

if 'tools' not in st.session_state:
    st.session_state['tools'] = []

if 'custom_tools' not in st.session_state:
    available_tools = pd.DataFrame(
        columns=['Active', 'Name', 'Type']
        )
    st.session_state['custom_tools'] = available_tools

if 'stages' not in st.session_state:
    st.session_state['stages'] = get_stages()

if 'agent_model' not in st.session_state:
    st.session_state['agent_model'] = 'claude-3-5-sonnet'

if 'response_instruction' not in st.session_state:
    st.session_state['response_instruction'] = ''

if 'search_services' not in st.session_state:
    available_services = (
        session.sql('SHOW CORTEX SEARCH SERVICES IN ACCOUNT')
        .select(
            col('"database_name"').alias('"Database"'),
            col('"schema_name"').alias('"Schema"'),
            col('"name"').alias('"Name"')
        )
        .with_column('"Full Name"', concat_ws(lit('.'), col('"Database"'), col('"Schema"'), col('"Name"')))
    ).to_pandas()
    available_services['Active'] = False
    available_services['Max Results'] = 1
    available_services = available_services[['Active','Name','Database','Schema','Max Results','Full Name']]
    st.session_state['search_services'] = available_services
    
def get_tool_resources():
    # Get tool_resources for API call
    tool_resources = {}
    search_services = st.session_state['search_services']
    search_services = search_services[search_services['Active']]
    for ix, row in search_services.iterrows():
        tool_resources[row['Name']] = {
            'name':row['Full Name'],
            'max_results':row['Max Results']
        }
    analyst_services = st.session_state['analyst_services']
    analyst_services = analyst_services[analyst_services['Active']]
    for ix, row in analyst_services.iterrows():
        tool_resources[row['Name']] = {
            'semantic_model_file':f"@{row['Database']}.{row['Schema']}.{row['File']}"
        }
    return tool_resources

def get_tools():
    # Get tools for API call
    tools = st.session_state['tools'].copy()
    search_services = st.session_state['search_services']
    search_services = search_services[search_services['Active']]
    analyst_services = st.session_state['analyst_services']
    analyst_services = analyst_services[analyst_services['Active']]
    custom_tools = st.session_state['custom_tools']
    custom_tools = custom_tools[custom_tools['Active']]
    
    for ix, row in search_services.iterrows():
        tools.append(
            {
                'tool_spec': {
                    'type':'cortex_search',
                    'name':row['Name']
                }
            }
        )
    for ix, row in analyst_services.iterrows():
        tools.append(
            {
                'tool_spec': {
                    'type':'cortex_analyst_text_to_sql',
                    'name':row['Name']
                }
            }
        )
    for ix, row in custom_tools.iterrows():
        tools.append(
            {
                'tool_spec': {
                    'type':row['Type'],
                    'name':row['Name']
                }
            }
        )
    return tools

def generate_payload(message):
    payload = {
        "response_instruction":st.session_state['response_instruction'],
        "model":st.session_state['agent_model'],
        "tools":get_tools(),
        "tool_resources":get_tool_resources(),
        "messages":[
            {
                "role":"user",
                "content":[
                    {
                        "type":"text",
                        "text":message
                    }
                ]
            }
        ]
    }
    return payload

def display_active_services():
    search_services = st.session_state['search_services']
    search_services = search_services[search_services['Active']]
    analyst_services = st.session_state['analyst_services']
    analyst_services = analyst_services[analyst_services['Active']]

    st.subheader(f'Active Services: {len(search_services)+len(analyst_services)}')
    if (len(search_services)==0) & (len(analyst_services) == 0):
        st.info('No Services selected.')

    for ix, row in search_services.iterrows():
        st.markdown(f"* :mag: **{row['Name']}**")
    for ix, row in analyst_services.iterrows():
        st.markdown(f"* :robot_face: **{row['Name']}**")

def display_active_tools():
    tools = get_tools()

    st.subheader(f'Active Tools: {len(tools)}')
    if (len(tools)==0):
        st.info('No tools selected.')
        
    for tool in tools:
        if tool['tool_spec']['type'] == 'cortex_search':
            st.markdown(f"* :mag: **{tool['tool_spec']['name']}**")
        elif tool['tool_spec']['type'] == 'cortex_analyst_text_to_sql':
            st.markdown(f"* :robot_face: **{tool['tool_spec']['name']}**")
        else:
            st.markdown(f"* :gear: **{tool['tool_spec']['name']}**")

@st.dialog("Manage Cortex Search Services", width='large')
def manage_cortex_search_services():
    st.markdown('Activate or deactive Cortex Search Services for your Agent.')
    st.write('---')
    services_df = st.data_editor(st.session_state['search_services'], use_container_width=True)
    if st.button('Update'):
        st.session_state['search_services'] = services_df
        st.rerun()

@st.dialog("Manage Cortex Analyst Services", width='large')
def manage_cortex_analyst_services():
    st.markdown('Add additional Semantic Models and manage which Models are active.')
    task = st.selectbox('Select:', ['Add a new Service','Manage existing Services'])
    st.write('---')
    if task == 'Add a new Service':
        stages = st.session_state['stages']
        database = st.selectbox('Database:', set(stages['Database']))
        schema = st.selectbox('Schema:', set(stages[stages['Database'] == database]['Schema']))
        stage = st.selectbox('Stage:', set(stages[(stages['Database'] == database) & (stages['Schema'] == schema)]['Stage']))
        files_in_stage = get_files_from_stage(database, schema, stage)
        if files_in_stage is not None:
            if len(files_in_stage) > 0:
                file = st.selectbox('File:', files_in_stage)
                name = st.text_input('Service Name:', value=file.split('/')[-1].split('.')[0])
                # TODO:Check if analyst service already exists
                if st.button('Add'):
                    new_service = {'Active':True, 'Name':name, 'Database':database, 'Schema':schema, 'Stage':stage, 'File':file}
                    st.session_state['analyst_services'].loc[len(st.session_state['analyst_services'])] = new_service
                    st.rerun()
            else:
                st.info('No YAML files smaller than 1MB in stage.')
    if task == 'Manage existing Services':
        services_df = st.data_editor(st.session_state['analyst_services'], use_container_width=True)
        if st.button('Update'):
            st.session_state['analyst_services'] = services_df
            st.rerun()

@st.dialog("Manage Response Instruction", width='large')
def manage_custom_instruction():
    st.markdown('Create a Response Instruction for your Agent.')
    st.write('---')
    custom_instruction = st.text_area('Custom Instruction:', value=st.session_state['response_instruction'])
    if st.button('Update'):
        st.session_state['response_instruction'] = custom_instruction
        st.rerun()

@st.dialog("Current Payload", width='large')
def display_payload():
    st.markdown("This is the current payload configuration for your API Calls.")
    prompt = st.text_input('Question:', value='I want to know ...')
    st.json(generate_payload(prompt))

@st.dialog("API History", width='large')
def display_api_call_history():
    st.markdown("Here you'll find all API Requests and Responses.")
    for message in st.session_state.api_history:
        if 'Request' in message:
            with st.chat_message('user'):
                st.json(message['Request'])
            st.write('---')
        if 'Response' in message:
            with st.chat_message('assistant'):
                st.json(message['Response'])
            st.write('---')

@st.dialog("Chat Messages", width='large')
def display_messages():
    st.markdown("Here you'll find all the messages that were logged in for displaying the chat.")
    for message in st.session_state.messages:
        if message['role'] == 'assistant':
            with st.chat_message('assistant'):
                st.json(message)
            st.write('---')
        if message['role'] == 'user':
            with st.chat_message('user'):
                st.json(message)
            st.write('---')
        if message['role'] == '❗':
            with st.chat_message('❗'):
                st.write(message)
            st.write('---')

@st.dialog("Manage Custom Tools", width='large')
def manage_custom_tools():
    st.info('Other tools than Cortex Search and Cortex Analyst are in PrPr!')
    st.info('Consider this dialog as a placeholder for future tools.')
    st.markdown('Add additionalTools and manage which Tools are active.')
    task = st.selectbox('Select:', ['Add a new Service','Manage existing Tools'])
    st.write('---')
    if task == 'Add a new Service':
        tool = st.selectbox('What tool do you want to add?', ['SQL Execution','Custom'])
        if tool == 'Custom':
            type = st.text_input('Tool Type:')
            name = st.text_input('Tool Name:')
        if tool == 'SQL Execution':
            type = st.text_input('Tool Type:', 'cortex_analyst_sql_exec', disabled=True)
            name = st.text_input('Tool Name:')
        if st.button('Add Tool', key='add2'):
            new_tool = {'Active':True, 'Name':name, 'Type':type}
            st.session_state['custom_tools'].loc[len(st.session_state['custom_tools'])] = new_tool
            st.rerun()
    if task == 'Manage existing Tools':
        tools_df = st.data_editor(st.session_state['custom_tools'], use_container_width=True)
        if st.button('Update'):
            st.session_state['custom_tools'] = tools_df
            st.rerun()

# Various functions to format Cortex Agents Response
@st.cache_data
def bot_retrieve_sql_results(sql):
    return session.sql(sql).limit(MAX_DATAFRAME_ROWS).to_pandas()

def bot_message_error(content):
    bot_message =  'Your query returned the following error:\n\n'
    bot_message += f"**Error Code:** {content['code']} \n\n"
    bot_message += f"**Error Message:** {content['message']} \n\n"
    bot_message_object = {}
    bot_message_object['role'] = 'assistant'
    bot_message_object['text'] = bot_message
    bot_message_object['type'] = 'error'
    st.session_state.messages.append(bot_message_object)
    return bot_message_object

def format_message_tool_use(content):
    bot_message =  f"I used the following tool serve your request: **{content['tool_use']['name']}**"
    bot_message_object = {}
    bot_message_object['role'] = 'assistant'
    bot_message_object['text'] = bot_message
    bot_message_object['type'] = 'tool_use'
    st.session_state.messages.append(bot_message_object)
    return

def format_message_tool_results(content):
    bot_message_object = {}
    bot_message_object['role'] = 'assistant'
    bot_message_object['searchResults'] = content.get("tool_results", {}).get("content", [{}])[0].get("json", {}).get("searchResults", [])
    bot_message_object['sql'] = content.get("tool_results", {}).get("content", [{}])[0].get("json", {}).get("sql", [])
    bot_message_object['suggestions'] = content.get("tool_results", {}).get("content", [{}])[0].get("json", {}).get("suggestions", [])
    if bot_message_object['sql'] != [] and len(bot_message_object['sql']) > 1:
        bot_message_object['sql'] = bot_message_object['sql']
        bot_message_object['text'] = content.get("tool_results", {}).get("content", [{}])[0].get("json", {}).get("text", '')#'I generated the following SQL Query for you:'
        bot_message_object['sql_df'] = bot_retrieve_sql_results(bot_message_object['sql'][:-1])
    if bot_message_object['searchResults'] != []:
        bot_message_object['text'] = 'I found the following relevant documents:'
    if bot_message_object['suggestions'] != [] and bot_message_object['sql'] == "":
        bot_message_object['text'] = content.get("tool_results", {}).get("content", [{}])[0].get("json", {}).get("text", [])
    st.session_state.messages.append(bot_message_object)
    return
    
def format_bot_message(data):
    bot_text_message = ''
    for message in data:
        if message['event'] == 'error':
            bot_message_error(message['data'])
        if message['event'] == 'done':
            break
        if 'data' in message:
            if 'delta' in message['data']:
                if 'content' in message['data']['delta']:
                    for content in message['data']['delta']['content']:
                        if content['type'] == 'tool_use':
                            format_message_tool_use(content)
                        elif content['type'] == 'tool_results':
                            format_message_tool_results(content)
                        else:
                            bot_text_message += content['text']
    if len(bot_text_message) > 1:
        st.session_state.messages.append({'role':'assistant', 'text':bot_text_message})            
    return 

# Function to process Prompts from User using Cortex Agent
def process_prompt(prompt):
    payload = generate_payload(prompt)
    st.session_state.api_history.append({'Request':payload})
    resp = _snowflake.send_snow_api_request(
        "POST",
        API_ENDPOINT,
        {},  # headers
        {'stream':True},
        payload,
        None,
        API_TIMEOUT,  # timeout in milliseconds
    )
    response = json.loads(resp["content"])
    st.session_state.api_history.append({'Response':response})
    return response

with st.sidebar:
    if st.button('New Chat', use_container_width=True, icon='🔄'):
        st.session_state.api_history = []
        st.session_state.messages = []
    with st.container(border=True):
        st.subheader('Agent Configuration')
        if st.button('Cortex Search Services', use_container_width=True, icon='🔍'):
            manage_cortex_search_services()
        if st.button('Cortex Analyst Services', use_container_width=True, icon='🤖'):
            manage_cortex_analyst_services()
        if st.button('Custom Tools', use_container_width=True, icon='🧰'):
            manage_custom_tools()
        if st.button('Response Instruction', use_container_width=True, icon='📝'):
            manage_custom_instruction()
        agent_model = st.selectbox('**Agent LLM:**', ['claude-3-5-sonnet','mistral-large2','llama3.3-70b'])
        st.session_state['agent_model'] = agent_model
    with st.container(border=True):
        st.subheader('Agent Monitoring')
        if st.button('Current Payload', use_container_width=True, icon='📦'):
            display_payload()
        if st.button('API Call History', use_container_width=True, icon='📖'):
            display_api_call_history()
        if st.button('Chat Message History', use_container_width=True, icon='📖'):
            display_messages()
    with st.container(border=True):
        display_active_services()
        display_active_tools()

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "text": prompt})
    if len(get_tool_resources()) == 0:
        st.session_state.messages.append({"role": "❗", "type":"hint", "text": 'Please note that you are using Cortex Agent without any services or tools.'})
    with st.spinner('Thinking ...'):
        response = process_prompt(prompt)
    if response is not None:
        try:
            response = format_bot_message(response)
        except Exception as e:
            st.error(e)
            st.error(response)


# Always display chat history
for message in st.session_state.messages:
    if message["role"] == "user":
        with st.chat_message("user"):
            st.markdown(message['text'])
    elif message["role"] == "assistant":
        with st.chat_message("assistant"):
            st.markdown(message['text'])
            if 'searchResults' in message:
                if message['searchResults'] != []:
                    for doc in message['searchResults']:
                        with st.expander(f"Document {doc['source_id']}"):
                            st.markdown(doc['text'])
            if 'sql' in message:
                if message['sql'] != [] and message['sql'] != '':
                    st.dataframe(message['sql_df'])
                    with st.expander(f"Generated SQL Query"):
                        st.code(message['sql'], language='sql')
            if 'suggestions' in message:
                with st.expander(f"Questions you could ask"):
                    for suggestion in message['suggestions']:
                        st.markdown(f"**{suggestion}**")
            if 'error' in message:
                st.markdown(message['text'])
    elif message["role"] == "❗":
        with st.chat_message("❗"):
            if message['type'] == 'hint':
                st.markdown(message['text'])