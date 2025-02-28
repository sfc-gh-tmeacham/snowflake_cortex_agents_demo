import streamlit as st
import pandas as pd
import json
import _snowflake
import math
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import col, lit, concat_ws, lower
from streamlit_extras.stylable_container import stylable_container
import plotly.express as px
import numpy as np

# Configuration
API_ENDPOINT = "/api/v2/cortex/agent:run"
API_TIMEOUT = 50000  # in milliseconds
MAX_DATAFRAME_ROWS = 1000
session = get_active_session()
INITIAL_MESSAGE = "Hello! Ask me anything about your data."
USER_AVATAR = "👤"
BOT_AVATAR = "❄️"

# Initialize session state variables
def initialize_session_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = []
        
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []  # Add this for API history

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
        st.session_state['search_services'] = get_search_services()

###############
# STYLE SHEET #
###############

def load_css():
    vLogo = 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/ff/Snowflake_Logo.svg/1024px-Snowflake_Logo.svg.png'      
    st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Source+Sans+Pro:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
    /* Overall App Container */
    .stApp {
        background-color: #f8f9fa; /* Light background for modern look */
        font-family: 'Inter', sans-serif;
    } 
    /* Main content area */
    .main-container {
        max-width: 900px; 
        margin: auto;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        background-color: white;
    }
    /* Chat Messages */
    .chat-message {
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        display: flex;
        align-items: flex-start;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease;
    }
    .chat-message:hover {
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.08);
    }
    .user-message {
        background-color: #e7f5fe;  /* Soft blue */
        color: #0b5394; /* Dark blue text */
        justify-content: flex-end;
        margin-left: 20%;
        border: 1px solid #d0e8ff;
    }
    .bot-message {
        background-color: #ffffff;
        color: #333333;
        justify-content: flex-start;
        margin-right: 20%;
        border: 1px solid #f0f0f0;
    }
    .avatar {
        font-size: 1.5rem;
        margin-right: 1rem;
        background-color: #f0f5ff;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .message-text {
        flex-grow: 1;
        word-wrap: break-word;
        margin-top: 0.2rem;
    }
    /* Input Box */
    .stTextInput>div>div>input {
        border-radius: 24px;
        padding: 0.75rem 1.25rem;
        border: 1px solid #eaeaea;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.03);
        transition: all 0.2s;
        font-family: 'Source Sans Pro', sans-serif;
    }
    .stTextInput>div>div>input:focus {
        border-color: #29b5e8;
        box-shadow: 0 0 0 3px rgba(41, 181, 232, 0.15);
        outline: none;
    }
    /* Send Button */
    .stButton>button {
        background-color: #29b5e8;
        color: white;
        border-radius: 24px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        transition: all 0.2s;
        font-family: 'Source Sans Pro', sans-serif;
        border: none;
    }
    .stButton>button:hover {
        background-color: #0056b3;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        transform: translateY(-1px);
    }
    /* Sidebar */
    .sidebar .sidebar-content {
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        padding: 0 16px;
        border-radius: 4px 4px 0 0;
        transition: all 0.2s;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e7f5fe !important;
        font-weight: 600;
    }
    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #333;
        background-color: #f8f9fa;
        border-radius: 6px;
    }
    /* Data visualization */
    .chart-container {
        border-radius: 8px;
        background-color: white;
        padding: 16px;
        margin-top: 8px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    /* Titles and Headings */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        color: #333;
    }
    /* Card styling for components */
    .info-card {
        border-radius: 8px;
        padding: 16px;
        background-color: white;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        margin-bottom: 16px;
    }
    /* Badge styling */
    .badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        color: white;
        background-color: #29b5e8;
        margin-right: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
    return vLogo

# Cache decorators for performance optimizations
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
        st.error(f"Error fetching files: {e}")
        return pd.DataFrame(columns=['File Name'])
    return files

@st.cache_data
def get_search_services():
    try:
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
        return available_services
    except Exception as e:
        st.error(f"Error fetching search services: {e}")
        return pd.DataFrame(columns=['Active', 'Name', 'Database', 'Schema', 'Max Results', 'Full Name'])

# Utility function to format large numbers more readably
def millify(n, decimal_places=0):
    MILLNAMES = ['',' K',' M',' B',' T']
    n = float(n)
    millidx = max(0, min(len(MILLNAMES)-1, int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))
    return f"{n / 10**(3 * millidx):.{decimal_places}f}{MILLNAMES[millidx]}"

# Function to use LLM to suggest the best chart type and parameters
def get_chart_suggestions(df, prompt=None):
    try:
        # First, check if DataFrame is valid and not empty
        if df.empty:
            return {
                "chart_type": "bar",
                "x_axis": df.columns[0] if len(df.columns) > 0 else "",
                "y_axis": df.columns[1] if len(df.columns) > 1 else None,
                "color": None,
                "title": "Data Visualization"
            }
        
        suggestion_prompt = f"""
        Analyze this dataframe structure and sample data to suggest visualization parameters using visual best practices (as dictated by the Financial Times guidelines).
        
        Columns: {df.columns.tolist()}
        Data Types: {df.dtypes.to_dict()}
        Sample: {df.head(3).to_dict()}
        
        Your response should be a JSON object in the following format only:
        {{
            "chart_type": "bar",     // Most appropriate chart type: bar, line, scatter, pie, histogram, box, or area
            "x_axis": "{df.columns[0]}",        // X-axis column name
            "y_axis": "{df.columns[1] if len(df.columns) > 1 else ''}",        // Y-axis column name (if applicable)
            "color": "",         // Color grouping column (optional)
            "title": "Data Visualization"          // Chart title suggestion
        }}
        The chart_type and x_axis are the only required variables.
        """
        
        # If we have a specific prompt/context from the user query, include it
        if prompt:
            suggestion_prompt = f"User query: {prompt}\n\n{suggestion_prompt}"
        
        # Create default suggestions
        default_suggestions = {
            "chart_type": "bar",
            "x_axis": df.columns[0],
            "y_axis": df.columns[1] if len(df.columns) > 1 else None,
            "color": None,
            "title": "Data Visualization"
        }
        
        # Try the API call, but use defaults if it fails
        try:
            # Format the payload for Claude call
            payload = {
                "model": st.session_state['agent_model'],
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": suggestion_prompt}]
                    }
                ]
            }
            
            # Make the API call
            resp = _snowflake.send_snow_api_request(
                "POST",
                "/api/v2/cortex/llm:complete",
                {},  # headers
                {},  # query params
                payload,
                None,
                30000,  # timeout in milliseconds
            )
            
            # Handle the response
            if resp and "content" in resp and resp["content"]:
                try:
                    response_json = json.loads(resp["content"])
                    # Print the response for debugging
                    print(f"LLM Response: {response_json}")
                    
                    if "content" in response_json:
                        suggestions = json.loads(response_json["content"])
                        
                        # Merge with defaults
                        for key, value in default_suggestions.items():
                            if key not in suggestions or not suggestions[key]:
                                suggestions[key] = value
                                
                        return suggestions
                except Exception as json_error:
                    print(f"JSON parsing error: {json_error}")
                    # Fall back to default suggestions
                    return default_suggestions
            else:
                print("Empty or invalid response from API")
                return default_suggestions
                
        except Exception as api_error:
            print(f"API call error: {api_error}")
            return default_suggestions
            
    except Exception as e:
        print(f"Chart suggestion error: {e}")
        # Fall back to basic defaults
        return {
            "chart_type": "bar",
            "x_axis": df.columns[0] if len(df.columns) > 0 else "",
            "y_axis": df.columns[1] if len(df.columns) > 1 else None,
            "color": None,
            "title": "Data Visualization"
        }

# Function to create an interactive chart with customization options
# Function to create an interactive chart with customization options
def create_interactive_chart(df, suggestions, message_index):
    # Initialize session state for chart parameters if not exists
    if f"chart_type_{message_index}" not in st.session_state:
        st.session_state[f"chart_type_{message_index}"] = suggestions.get("chart_type", "bar")
    if f"x_axis_{message_index}" not in st.session_state:
        st.session_state[f"x_axis_{message_index}"] = suggestions.get("x_axis", df.columns[0])
    if f"y_axis_{message_index}" not in st.session_state:
        st.session_state[f"y_axis_{message_index}"] = suggestions.get("y_axis", df.columns[1] if len(df.columns) > 1 else None)
    if f"color_{message_index}" not in st.session_state:
        st.session_state[f"color_{message_index}"] = suggestions.get("color", None)
    if f"title_{message_index}" not in st.session_state:
        st.session_state[f"title_{message_index}"] = suggestions.get("title", "Data Visualization")
    
    # Get chart parameters from session state
    chart_type = st.session_state[f"chart_type_{message_index}"]
    x_axis = st.session_state[f"x_axis_{message_index}"]
    y_axis = st.session_state[f"y_axis_{message_index}"]
    color = st.session_state[f"color_{message_index}"]
    title = st.session_state[f"title_{message_index}"]
    
    # Configure chart parameters based on selections
    chart_map = {
        "bar": px.bar,
        "line": px.line,
        "scatter": px.scatter,
        "pie": px.pie,
        "histogram": px.histogram,
        "box": px.box,
        "area": px.area
    }

    # Basic arguments for the chart
    args = {
        "data_frame": df,
        "title": title,
        "template": "plotly_white",
    }

    # Add conditional parameters based on chart type
    if chart_type == "pie":
        args.update({
            "names": x_axis,
            "values": y_axis,
            "color": x_axis,
            "color_discrete_sequence": px.colors.sequential.Viridis
        })
    elif chart_type == "histogram":
        args.update({
            "x": x_axis,
            "color": color,
            "opacity": 0.8,
            "nbins": 20
        })
    else:
        args.update({
            "x": x_axis,
            "y": y_axis,
            "color": color,
            "labels": {
                x_axis: x_axis,
                y_axis: y_axis if y_axis else ""
            }
        })
    
    # Create the chart
    try:
        fig = chart_map[chart_type](**args)
        
        # Apply consistent styling
        fig.update_layout(
            font_family="Inter, sans-serif",
            title_font_family="Plus Jakarta Sans, sans-serif",
            title_font_size=16,
            plot_bgcolor="rgba(250, 250, 252, 0.9)",
            paper_bgcolor="rgba(255, 255, 255, 0)",
            title={
                'x': 0.5,
                'xanchor': 'center'
            },
            margin=dict(l=40, r=40, t=60, b=40),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Add grid lines for most chart types
        if chart_type not in ["pie"]:
            fig.update_yaxes(
                showgrid=True, 
                gridwidth=1, 
                gridcolor="rgba(226, 232, 240, 0.6)"
            )
            fig.update_xaxes(
                showgrid=True, 
                gridwidth=1, 
                gridcolor="rgba(226, 232, 240, 0.6)"
            )
        
        return fig
        
    except Exception as e:
        st.error(f"Error generating chart: {e}")
        return None
        
# Function to determine the best visualization based on dataframe content
def generate_auto_visualization(df, prompt=None):
    if df.empty or len(df) < 2:
        return None, "Not enough data to visualize"
    
    try:
        # Get chart suggestions using LLM
        suggestions = get_chart_suggestions(df, prompt)
        
        # Generate visualization from suggestions
        message_index = len(st.session_state.messages)
        visualization = create_interactive_chart(df, suggestions, message_index)
        
        return visualization, suggestions.get("chart_type", "bar")
            
    except Exception as e:
        # Fall back to default visualization logic if LLM suggestion fails
        st.error(f"Error generating visualization: {e}")
        
        # Determine column types
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # If there's a datetime column, it's likely time-series data
        if datetime_cols and numeric_cols:
            fig = px.line(
                df, 
                x=datetime_cols[0], 
                y=numeric_cols[0:3],  # Take up to 3 numeric columns
                title=f"Time Series: {numeric_cols[0:3]} over {datetime_cols[0]}",
                labels={col: col for col in numeric_cols[0:3]},
                template="plotly_white"
            )
            return fig, "time_series"
        
        # If there are 2+ numeric columns, create a scatter plot or bar chart
        elif len(numeric_cols) >= 2:
            # If there are many rows, a scatter plot is better
            if len(df) > 10:
                fig = px.scatter(
                    df, 
                    x=numeric_cols[0], 
                    y=numeric_cols[1],
                    color=categorical_cols[0] if categorical_cols else None,
                    title=f"Scatter Plot: {numeric_cols[1]} vs {numeric_cols[0]}",
                    template="plotly_white"
                )
                return fig, "scatter"
            # For fewer rows, a bar chart works well
            else:
                fig = px.bar(
                    df, 
                    x=df.index if len(df) <= 15 else numeric_cols[0], 
                    y=numeric_cols[0] if len(df) <= 15 else numeric_cols[1],
                    title=f"Bar Chart: {numeric_cols[0]}" if len(df) <= 15 else f"Bar Chart: {numeric_cols[1]} by {numeric_cols[0]}",
                    template="plotly_white"
                )
                return fig, "bar"
        
        # If there's one numeric and one categorical column, create a grouped bar chart
        elif numeric_cols and categorical_cols:
            fig = px.bar(
                df, 
                x=categorical_cols[0], 
                y=numeric_cols[0],
                title=f"{numeric_cols[0]} by {categorical_cols[0]}",
                template="plotly_white"
            )
            return fig, "categorical_bar"
        
        # If only categorical columns exist, create a count plot
        elif categorical_cols:
            # Only use the first categorical column with the top 10 values
            counts = df[categorical_cols[0]].value_counts().reset_index()
            counts.columns = [categorical_cols[0], 'count']
            
            if len(counts) > 10:
                counts = counts.head(10)
                
            fig = px.bar(
                counts, 
                x=categorical_cols[0], 
                y='count',
                title=f"Count of {categorical_cols[0]}",
                template="plotly_white"
            )
            return fig, "count"
        
        # If only one numeric column exists, create a histogram
        elif numeric_cols:
            fig = px.histogram(
                df, 
                x=numeric_cols[0],
                title=f"Distribution of {numeric_cols[0]}",
                template="plotly_white"
            )
            return fig, "histogram"
        
        else:
            return None, "No suitable columns for visualization"

# Resource and tools management functions
def get_tool_resources():
    # Get tool_resources for API call
    tool_resources = {}
    search_services = st.session_state['search_services']
    search_services = search_services[search_services['Active']]
    for ix, row in search_services.iterrows():
        tool_resources[row['Name']] = {
            'name': row['Full Name'],
            'max_results': row['Max Results']
        }
    analyst_services = st.session_state['analyst_services']
    analyst_services = analyst_services[analyst_services['Active']]
    for ix, row in analyst_services.iterrows():
        tool_resources[row['Name']] = {
            'semantic_model_file': f"@{row['Database']}.{row['Schema']}.{row['File']}"
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
        tools.append({
            'tool_spec': {
                'type': 'cortex_search',
                'name': row['Name']
            }
        })
    for ix, row in analyst_services.iterrows():
        tools.append({
            'tool_spec': {
                'type': 'cortex_analyst_text_to_sql',
                'name': row['Name']
            }
        })
    for ix, row in custom_tools.iterrows():
        tools.append({
            'tool_spec': {
                'type': row['Type'],
                'name': row['Name']
            }
        })
    return tools

def generate_payload(message):
    payload = {
        "response_instruction": st.session_state['response_instruction'],
        "model": st.session_state['agent_model'],
        "tools": get_tools(),
        "tool_resources": get_tool_resources(),
        "messages": st.session_state.conversation_history + [
            {
                "role": "user",
                "content": message,
                "type": "text"
            }
        ]
    }
    return payload

# Display functions for sidebar 
def display_active_services():
    search_services = st.session_state['search_services']
    search_services = search_services[search_services['Active']]
    analyst_services = st.session_state['analyst_services']
    analyst_services = analyst_services[analyst_services['Active']]

    st.subheader('Active Services', anchor=False)
    
    if (len(search_services) == 0) & (len(analyst_services) == 0):
        st.info('No services selected.', icon="ℹ️")
        return

    services_count = len(search_services) + len(analyst_services)
    services_text = "service" if services_count == 1 else "services"
    st.caption(f"{services_count} active {services_text}")
    
    for idx, row in search_services.iterrows():
        st.markdown(f"🔍 **{row['Name']}**")
    for idx, row in analyst_services.iterrows():
        st.markdown(f"🤖 **{row['Name']}**")

def display_active_tools():
    tools = get_tools()

    st.subheader('Active Tools', anchor=False)
    
    if len(tools) == 0:
        st.info('No tools selected.', icon="ℹ️")
        return
        
    tools_count = len(tools)
    tools_text = "tool" if tools_count == 1 else "tools"
    st.caption(f"{tools_count} active {tools_text}")
    
    for tool in tools:
        tool_type = tool['tool_spec']['type']
        tool_name = tool['tool_spec']['name']
        
        if tool_type == 'cortex_search':
            st.markdown(f"🔍 **{tool_name}**")
        elif tool_type == 'cortex_analyst_text_to_sql':
            st.markdown(f"🤖 **{tool_name}**")
        else:
            st.markdown(f"⚙️ **{tool_name}**")

# Dialog management functions
@st.dialog("Manage Cortex Search Services", width='large')
def manage_cortex_search_services():
    st.subheader('Manage Cortex Search Services', anchor=False)
    st.markdown('Activate or deactivate Cortex Search Services for your Agent.')
    st.divider()
    
    services_df = st.data_editor(
        st.session_state['search_services'], 
        use_container_width=True,
        column_config={
            "Active": st.column_config.CheckboxColumn(
                "Active",
                help="Enable/disable this service",
                width="small",
            ),
            "Max Results": st.column_config.NumberColumn(
                "Max Results",
                help="Maximum number of search results to return",
                min_value=1,
                max_value=10,
                step=1,
                width="small",
            ),
        },
        disabled=["Database", "Schema", "Full Name"]
    )
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button('Update Services', use_container_width=True):
            st.session_state['search_services'] = services_df
            st.rerun()

@st.dialog("Manage Cortex Analyst Services", width='large')
def manage_cortex_analyst_services():
    st.subheader('Manage Cortex Analyst Services', anchor=False)
    st.markdown('Add new Semantic Models or manage existing ones.')
    
    task = st.radio("Select action:", ['Add a new Service', 'Manage existing Services'], horizontal=True)
    st.divider()
    
    if task == 'Add a new Service':
        stages = st.session_state['stages']
        
        col1, col2 = st.columns(2)
        with col1:
            database = st.selectbox('Database:', sorted(set(stages['Database'])))
        with col2:
            schema_options = sorted(set(stages[stages['Database'] == database]['Schema']))
            schema = st.selectbox('Schema:', schema_options)
        
        stage_options = sorted(set(stages[(stages['Database'] == database) & (stages['Schema'] == schema)]['Stage']))
        stage = st.selectbox('Stage:', stage_options)
        
        files_in_stage = get_files_from_stage(database, schema, stage)
        
        if not files_in_stage.empty:
            file = st.selectbox('YAML File:', files_in_stage['File Name'])
            
            col1, col2 = st.columns(2)
            with col1:
                default_name = file.split('/')[-1].split('.')[0] if '/' in file else file.split('.')[0]
                name = st.text_input('Service Name:', value=default_name)
            
            with col2:
                st.write("")
                st.write("")
                if st.button('Add Service', use_container_width=True):
                    # Check if service with same name already exists
                    if name in st.session_state['analyst_services']['Name'].values:
                        st.error(f"Service with name '{name}' already exists!")
                    else:
                        new_service = {'Active': True, 'Name': name, 'Database': database, 'Schema': schema, 'Stage': stage, 'File': file}
                        st.session_state['analyst_services'].loc[len(st.session_state['analyst_services'])] = new_service
                        st.success(f"Added service '{name}'")
                        st.rerun()
        else:
            st.info('No YAML files smaller than 1MB found in selected stage.', icon="ℹ️")
    
    if task == 'Manage existing Services':
        if st.session_state['analyst_services'].empty:
            st.info('No analyst services have been added yet.', icon="ℹ️")
        else:
            services_df = st.data_editor(
                st.session_state['analyst_services'], 
                use_container_width=True,
                column_config={
                    "Active": st.column_config.CheckboxColumn(
                        "Active",
                        help="Enable/disable this service",
                        width="small",
                    ),
                    "Name": st.column_config.TextColumn(
                        "Name",
                        help="Service name",
                        width="medium",
                    ),
                },
                disabled=["Database", "Schema", "Stage", "File"]
            )
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button('Update Services', use_container_width=True):
                    st.session_state['analyst_services'] = services_df
                    st.rerun()

@st.dialog("Manage Response Instruction", width='large')
def manage_custom_instruction():
    st.subheader('Response Instructions', anchor=False)
    st.markdown('Create a custom instruction to guide how the agent responds.')
    st.divider()
    
    custom_instruction = st.text_area(
        'Response Instruction:',
        value=st.session_state['response_instruction'],
        height=200,
        placeholder="Enter instructions for the agent, e.g., 'Always format SQL results in a table and explain key findings.'"
    )
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button('Update Instructions', use_container_width=True):
            st.session_state['response_instruction'] = custom_instruction
            st.rerun()

@st.dialog("Manage Custom Tools", width='large')
def manage_custom_tools():
    st.subheader('Custom Tools Management', anchor=False)
    st.info('Other tools besides Cortex Search and Cortex Analyst are in preview!', icon="ℹ️")
    
    task = st.radio("Select action:", ['Add a new Tool', 'Manage existing Tools'], horizontal=True)
    st.divider()
    
    if task == 'Add a new Tool':
        tool_type = st.selectbox('Tool Type:', ['SQL Execution', 'Custom'])
        
        if tool_type == 'Custom':
            col1, col2 = st.columns(2)
            with col1:
                type_value = st.text_input('Tool Type:')
            with col2:
                name_value = st.text_input('Tool Name:')
        else:  # SQL Execution
            col1, col2 = st.columns(2)
            with col1:
                type_value = st.text_input('Tool Type:', value='cortex_analyst_sql_exec', disabled=True)
            with col2:
                name_value = st.text_input('Tool Name:')
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button('Add Tool', use_container_width=True):
                if not name_value or not type_value:
                    st.error("Tool name and type are required!")
                else:
                    new_tool = {'Active': True, 'Name': name_value, 'Type': type_value}
                    st.session_state['custom_tools'].loc[len(st.session_state['custom_tools'])] = new_tool
                    st.success(f"Added tool '{name_value}'")
                    st.rerun()
    
    if task == 'Manage existing Tools':
        if st.session_state['custom_tools'].empty:
            st.info('No custom tools have been added yet.', icon="ℹ️")
        else:
            tools_df = st.data_editor(
                st.session_state['custom_tools'], 
                use_container_width=True,
                column_config={
                    "Active": st.column_config.CheckboxColumn(
                        "Active",
                        help="Enable/disable this tool",
                        width="small",
                    ),
                }
            )
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button('Update Tools', use_container_width=True):
                    st.session_state['custom_tools'] = tools_df
                    st.rerun()

@st.dialog("Current Payload", width='large')
def display_payload():
    st.subheader("API Payload Configuration", anchor=False)
    st.markdown("Preview the current payload that will be sent to the API.")
    st.divider()
    
    prompt = st.text_input('Sample Question:', value='Tell me about our sales performance')
    
    payload = generate_payload(prompt)
    st.json(payload, expanded=True)

@st.dialog("API History", width='large')
def display_api_call_history():
    st.subheader("API Call History", anchor=False)
    st.markdown("View all API requests and responses from this session.")
    st.divider()
    
    if not st.session_state.api_history:
        st.info("No API calls have been made yet.", icon="ℹ️")
        return
        
    for i, message in enumerate(st.session_state.api_history):
        if 'Request' in message:
            st.subheader(f"Request #{(i//2)+1}", anchor=False)
            with st.expander("View request payload", expanded=False):
                st.json(message['Request'])
        
        if 'Response' in message:
            st.subheader(f"Response #{(i//2)+1}", anchor=False)
            with st.expander("View response data", expanded=False):
                st.json(message['Response'])
            
        if i < len(st.session_state.api_history) - 1:
            st.divider()

@st.dialog("Chat Messages", width='large')
def display_messages():
    st.subheader("Chat Message History", anchor=False)
    st.markdown("View the internal message objects used to display the chat.")
    st.divider()
    
    if not st.session_state.messages:
        st.info("No messages have been exchanged yet.", icon="ℹ️")
        return
        
    for i, message in enumerate(st.session_state.messages):
        if message['role'] == 'assistant':
            st.subheader(f"Assistant Message #{i+1}", anchor=False)
            with st.expander("View message object", expanded=False):
                st.json(message)
        
        elif message['role'] == 'user':
            st.subheader(f"User Message #{i+1}", anchor=False)
            with st.expander("View message object", expanded=False):
                st.json(message)
        
        elif message['role'] == '❗':
            st.subheader(f"Alert Message #{i+1}", anchor=False)
            with st.expander("View message object", expanded=False):
                st.write(message)
        
        if i < len(st.session_state.messages) - 1:
            st.divider()

@st.dialog("Conversation History", width='large')
def display_conversation_history():
    st.subheader("Conversation History for API", anchor=False)
    st.markdown("View the conversation history being sent to the API.")
    st.divider()
    
    if not st.session_state.conversation_history:
        st.info("No conversation history has been created yet.", icon="ℹ️")
        return
        
    for i, message in enumerate(st.session_state.conversation_history):
        if message['role'] == 'assistant':
            st.subheader(f"Assistant Message #{i+1}", anchor=False)
            with st.expander("View message object", expanded=False):
                st.json(message)
        
        elif message['role'] == 'user':
            st.subheader(f"User Message #{i+1}", anchor=False)
            with st.expander("View message object", expanded=False):
                st.json(message)
        
        if i < len(st.session_state.conversation_history) - 1:
            st.divider()

# Functions to process and format Cortex Agent responses
@st.cache_data
def bot_retrieve_sql_results(sql):
    try:
        return session.sql(sql).limit(MAX_DATAFRAME_ROWS).to_pandas()
    except Exception as e:
        st.error(f"Error executing SQL: {e}")
        return pd.DataFrame()

def bot_message_error(content):
    bot_message = 'Your query returned the following error:\n\n'
    bot_message += f"**Error Code:** {content['code']} \n\n"
    bot_message += f"**Error Message:** {content['message']} \n\n"
    bot_message_object = {
        'role': 'assistant',
        'text': bot_message,
        'type': 'error'
    }
    st.session_state.messages.append(bot_message_object)
    return bot_message_object

def format_message_tool_use(content):
    # Only proceed if content is a dictionary
    if not isinstance(content, dict):
        st.error(f"Invalid tool_use content format: {content}")
        return
    
    # Get the tool use information
    tool_use = content.get('tool_use', {})
    tool_name = tool_use.get('name', 'Unknown Tool')
    
    # Create a message for UI display
    bot_message = f"I used the following tool to serve your request: **{tool_name}**"
    bot_message_object = {
        'role': 'assistant',
        'text': bot_message,
        'type': 'tool_use'
    }
    st.session_state.messages.append(bot_message_object)

    # Add to conversation history in the expected format for the API
    st.session_state.conversation_history.append({
        "role": "assistant",
        "content": [
            {
                "type": "tool_use",
                "tool_use": tool_use
            }
        ]
    })

def format_message_tool_results(content):
    # Only proceed if content is a dictionary
    if not isinstance(content, dict):
        st.error(f"Invalid tool_results content format: {content}")
        return
    
    # Create message object for UI
    bot_message_object = {'role': 'assistant'}
    
    # Extract tool results based on the structure
    tool_results = {}
    if "tool_results" in content:
        tool_results_container = content["tool_results"]
        
        # Handle direct json content
        if isinstance(tool_results_container, dict) and "json" in tool_results_container:
            tool_results = tool_results_container["json"]
        # Handle nested content structure
        elif isinstance(tool_results_container, dict) and "content" in tool_results_container:
            if isinstance(tool_results_container["content"], list) and len(tool_results_container["content"]) > 0:
                first_content = tool_results_container["content"][0]
                if isinstance(first_content, dict) and "json" in first_content:
                    tool_results = first_content["json"]
    
    # Extract data for UI display
    bot_message_object['searchResults'] = tool_results.get("searchResults", [])
    bot_message_object['sql'] = tool_results.get("sql", "")
    bot_message_object['suggestions'] = tool_results.get("suggestions", [])
    
    # Extract the original user query for context
    user_query = ""
    if len(st.session_state.messages) > 0 and st.session_state.messages[-1]['role'] == 'user':
        user_query = st.session_state.messages[-1].get('text', '')
    
    # Handle SQL results
    if bot_message_object['sql'] and len(bot_message_object['sql']) > 1:
        # Remove the trailing semicolon if present for SQL execution
        sql_to_execute = bot_message_object['sql'][:-1] if bot_message_object['sql'].endswith(';') else bot_message_object['sql']
        
        try:
            # Execute SQL and get results
            bot_message_object['sql_df'] = bot_retrieve_sql_results(sql_to_execute)
            
            # Generate visualization if we have data
            if not bot_message_object['sql_df'].empty:
                bot_message_object['visualization'], bot_message_object['viz_type'] = generate_auto_visualization(bot_message_object['sql_df'], user_query)
            
            # Set default text if not provided
            if 'text' not in tool_results or not tool_results.get('text'):
                bot_message_object['text'] = "Here are the results of your query:"
            else:
                bot_message_object['text'] = tool_results.get('text')
            
            # Store message index for interactive chart features
            bot_message_object['message_index'] = len(st.session_state.messages)
            
            # Add SQL to conversation history for the API
            #st.session_state.conversation_history.append({
            #    "role": "assistant",
            #    "content": [{"type": "sql", "text": bot_message_object['sql']}]  
            #})
        
        except Exception as e:
            error_msg = f"Error executing SQL query: {str(e)}"
            st.error(error_msg)
            bot_message_object['text'] = error_msg
            bot_message_object['sql_df'] = pd.DataFrame()
    
    # Handle search results
    elif bot_message_object['searchResults'] and len(bot_message_object['searchResults']) > 0:
        bot_message_object['text'] = tool_results.get('text', 'I found the following relevant documents:')
    
    # Handle suggestions
    elif bot_message_object['suggestions'] and not bot_message_object['sql']:
        bot_message_object['text'] = tool_results.get('text', 'You might want to try these questions:')
    
    # Default text if nothing else is set
    if 'text' not in bot_message_object or not bot_message_object['text']:
        bot_message_object['text'] = tool_results.get('text', "Here's what I found:")
    
    # Add to UI messages
    st.session_state.messages.append(bot_message_object)

    # Add to conversation history for API in the correct format
    st.session_state.conversation_history.append({
        "role": "assistant", 
        "content": [{"type": "text", "text": bot_message_object['text']}], 
    })

    # Add tool results to conversation history if available
    if "tool_results" in content:
        st.session_state.conversation_history.append({
            "role": "assistant",
            "content": [
                {
                    "type": "tool_results",
                    "tool_results": content["tool_results"]
                }
            ]
        })
    

def format_bot_message(data):
    
    # Handle empty or invalid responses
    if not data:
        st.error("Empty response from API")
        st.session_state.messages.append({
            'role': 'assistant', 
            'text': "I'm sorry, I received an empty response from the API."
        })
        return
    
    bot_text_message = ''
    
    try:
        # Process the response based on its structure
        if isinstance(data, list):
            # Process streaming response
            for message in data:
                if not isinstance(message, dict):
                    continue
                    
                if message.get('event') == 'error':
                    bot_message_error(message.get('data', {}))
                
                elif message.get('event') == 'done':
                    break
                
                elif 'data' in message and 'delta' in message['data']:
                    delta = message['data']['delta']
                    
                    if 'content' in delta and isinstance(delta['content'], list):
                        for content in delta['content']:
                            if not isinstance(content, dict):
                                continue
                                
                            content_type = content.get('type')
                            
                            if content_type == 'tool_use':
                                format_message_tool_use(content)
                            
                            elif content_type == 'tool_results':
                                format_message_tool_results(content)
                            
                            elif content_type == 'text' and 'text' in content:
                                bot_text_message += content['text']
        
        elif isinstance(data, dict):
            # Process non-streaming response
            if 'content' in data:
                content = data['content']
                
                if isinstance(content, str):
                    # Simple text response
                    bot_text_message = content
                elif isinstance(content, list):
                    # Process structured content
                    for item in content:
                        if isinstance(item, dict):
                            if item.get('type') == 'text':
                                bot_text_message += item.get('text', '')
                            elif item.get('type') == 'tool_use':
                                format_message_tool_use(item)
                            elif item.get('type') == 'tool_results':
                                format_message_tool_results(item)
        
        # Add the text message if it's not empty
        if bot_text_message.strip():
            st.session_state.messages.append({'role': 'assistant', 'text': bot_text_message})
            
            # Add to conversation history for API context
            st.session_state.conversation_history.append({
                "role": "assistant", 
                "content": [{"type": "text", "text": bot_text_message}]
            })
    
    except Exception as e:
        st.error(f"Error formatting bot message: {str(e)}")
        st.error(f"Exception traceback: {traceback.format_exc()}")
        st.session_state.messages.append({
            'role': 'assistant', 
            'text': "I encountered an error processing the response."
        })

# Function to process user prompts
def process_prompt(prompt):
    try:
        # Add user message to UI messages first
        st.session_state.messages.append({"role": "user", "text": prompt})
        
        # Add user message to conversation history for API in the proper format
        st.session_state.conversation_history.append({
            "role": "user", 
            "content": [{"type": "text", "text": prompt}]  # Correct format expected by Cortex Agent API
        })
        
        # Generate payload with complete conversation history
        payload = {
            "response_instruction": st.session_state['response_instruction'],
            "model": st.session_state['agent_model'],
            "tools": get_tools(),
            "tool_resources": get_tool_resources(),
            "messages": st.session_state.conversation_history
        }
        
        # Log the request for debugging
        st.session_state.api_history.append({'Request': payload})
        

        # Make the API call
        resp = _snowflake.send_snow_api_request(
            "POST",
            API_ENDPOINT,
            {},  # headers
            {'stream': True},  # query params
            payload,
            None,  # form data
            API_TIMEOUT,  # timeout in milliseconds
        )
        
        # Check if response is None
        if resp is None:
            st.error("API returned None response")
            st.session_state.messages.append({
                'role': 'assistant', 
                'text': "I'm sorry, I couldn't process your request. The API returned a null response."
            })
            return None
        
        # Check if response content exists
        if not resp.get("content"):
            st.error("API response has no content")
            st.session_state.messages.append({
                'role': 'assistant', 
                'text': "I'm sorry, I couldn't process your request. The API response didn't contain any content."
            })
            return None
            
        # Try to parse the response
        try:
            response = json.loads(resp["content"])
            st.session_state.api_history.append({'Response': response})
            return response
        except json.JSONDecodeError as e:
            st.error(f"Failed to decode API response: {e}")
            st.error(f"Raw response: {resp['content']}")
            st.session_state.messages.append({
                'role': 'assistant', 
                'text': "I'm sorry, I couldn't process your request. There was an error parsing the API response."
            })
            return None
    
    except Exception as e:
        st.error(f"Error processing request: {str(e)}")
        st.session_state.messages.append({
            'role': 'assistant', 
            'text': f"I'm sorry, an error occurred: {str(e)}"
        })
        return None

# Main application
def main():
    # Initialize session state
    initialize_session_state()
    
    # Load CSS and get logo
    vLogo = load_css()
    
#################
# SIDEBAR UI
#################
    with st.sidebar:
        st.image(vLogo, width=200)

        st.markdown("---")
        model_options = ['claude-3-5-sonnet', 'mistral-large2', 'llama3.3-70b']
        
        st.session_state['agent_model'] = st.selectbox(
        "Model", 
        options=model_options,
        index=model_options.index(st.session_state['agent_model']) if st.session_state['agent_model'] in model_options else 0
    )
    
        # Actions section
        st.markdown("### Actions")
        
        if st.button('New Chat', use_container_width=True, icon='🔄'):
            st.session_state.api_history = []
            st.session_state.conversation_history = []
            st.session_state.messages = []
            st.rerun()
        
        # Collapsible sections with modern styling
        with stylable_container(
            "config_container",
            css_styles="""
                {
                    border-radius: 10px;
                    background-color: white;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                    padding: 10px;
                    margin-top: 20px;
                }
            """
        ):
            st.markdown("### Configuration")
            
            # Service controls with icons and tooltips
            col1, col2 = st.columns(2)
            with col1:
                search_count = sum(st.session_state['search_services']['Active'])
                search_button = st.button(
                    f'🔍 Search ({search_count})', 
                    use_container_width=True,
                    help="Manage Cortex Search Services"
                )
                if search_button:
                    manage_cortex_search_services()
            
            with col2:
                analyst_count = sum(st.session_state['analyst_services']['Active'])
                analyst_button = st.button(
                    f'📊 Analyst ({analyst_count})', 
                    use_container_width=True,
                    help="Manage Cortex Analyst Services"
                )
                if analyst_button:
                    manage_cortex_analyst_services()
            
            col1, col2 = st.columns(2)
            with col1:
                tools_count = sum(st.session_state['custom_tools']['Active'])
                tools_button = st.button(
                    f'🧰 Tools ({tools_count})', 
                    use_container_width=True,
                    help="Manage Custom Tools"
                )
                if tools_button:
                    manage_custom_tools()
            
            with col2:
                if st.button('📝 Instructions', use_container_width=True, help="Set Response Instructions"):
                    manage_custom_instruction()
        
        # Advanced section
        with st.expander("Advanced", expanded=False):
            if st.button('View Payload', use_container_width=True, icon='📦'):
                display_payload()
            if st.button('API History', use_container_width=True, icon='📚'):
                display_api_call_history()
            if st.button('Message Debug', use_container_width=True, icon='🔧'):
                display_messages()
            if st.button('Conversation History', use_container_width=True, icon='💬'):
                display_conversation_history()
        
        # Status indicators
        st.markdown("---")
        st.markdown("### Status")
        
        # Show active services with status indicators
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div class='badge' style='background-color: {'#29b5e8' if search_count else '#d3d3d3'};'>Search</div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='badge' style='background-color: {'#29b5e8' if analyst_count else '#d3d3d3'};'>Analyst</div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='badge' style='background-color: {'#29b5e8' if tools_count else '#d3d3d3'};'>Tools</div>", unsafe_allow_html=True)
        
        # Credits and version
        st.markdown("---")
        st.markdown("<div style='text-align: center; color: #888; font-size: 0.8em;'>Snowflake Cortex Agent v1.2</div>", unsafe_allow_html=True)

    
#################
# MAIN CHAT UI
#################
    with stylable_container(
    "main_container",
    css_styles="""
        {
            background-color: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }
    """
):
    # Display chat messages
        chat_container = st.container()
    
    with chat_container:
        if not st.session_state.messages:
            st.markdown(
                f"""
                <div style="display: flex; justify-content: center; align-items: center; height: 300px; flex-direction: column;">
                    <div style="font-size: 50px; margin-bottom: 20px;">👋</div>
                    <div style="font-size: 24px; color: #666; text-align: center;">{INITIAL_MESSAGE}</div>
                    <div style="font-size: 18px; color: #888; text-align: center; margin-top: 10px;">
                        Try asking about your data or using tools
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        # Display chat history
        for message in st.session_state.messages:
            # Use st.chat_message for all messages with appropriate avatars
            with st.chat_message(
                message["role"], 
                avatar=USER_AVATAR if message["role"] == "user" else BOT_AVATAR if message['role'] == 'assistant' else None
            ):
                if message["role"] in ("user", "assistant"):
                    # Always display the text content first
                    st.markdown(message["text"])
                    
                    # Handle search results - only if they exist in this message
                    if message.get('role') == 'assistant' and message.get('searchResults') and len(message.get('searchResults', [])) > 0:
                        #st.markdown(message.get('text', 'I found the following relevant documents:'))
                        with st.expander(f"📄 Search Results ({len(message['searchResults'])} documents)", expanded=False):
                            for i, doc in enumerate(message['searchResults']):
                                with stylable_container(
                                    f"search_result_{i}",
                                    css_styles=""" {
                                        border: 1px solid #e0e0e0;
                                        border-radius: 8px;
                                        padding: 10px;
                                        margin-bottom: 10px;
                                        background-color: #f9f9f9;
                                    }
                                    """
                                ):
                                    st.markdown(f"**{doc.get('source_id', doc.get('title', 'Document'))}**")
                                    st.markdown(doc.get('text', doc.get('content', 'No content available')))
                                    
                                    # Add score if available
                                    if 'score' in doc:
                                        st.markdown(f"*Score: {doc.get('score', 'N/A')}*")
                                    
                                    # If there are metadata fields, display them in a collapsible section
                                    if any(k for k in doc.keys() if k not in ['source_id', 'text', 'title', 'content', 'score']):
                                        metadata_items = {k: v for k, v in doc.items() 
                                                        if k not in ['source_id', 'text', 'title', 'content', 'score']}
                                        for key, value in metadata_items.items():
                                            st.markdown(f"**{key}**: {value}")
                    
                    # Handle SQL results with visualization - only if SQL and results exist in this message
                    if message.get('role') == 'assistant' and message.get('sql') and message.get('sql_df') is not None and not message.get('sql_df', pd.DataFrame()).empty:
                        # Create styled data card container
                        st.markdown("""
                            <div style="margin: 15px 0 10px 0; font-size: 1rem; color: #334155; font-weight: 600;">
                                Query Results
                            </div>
                        """, unsafe_allow_html=True)
                        
                        with st.container():
                            # Use tabs to separate the dataframe and visualization with customization
                            tabs = st.tabs(["📋 Data Table", "📊 Visualization", "🔍 SQL Query"])
                            
                            with tabs[0]:  # Data Table tab
                                # Add caption above the dataframe
                                row_count = len(message['sql_df'])
                                st.caption(f"Showing {row_count} {'row' if row_count == 1 else 'rows'} of data")
                                
                                # Display the dataframe with styling
                                st.dataframe(
                                    message['sql_df'], 
                                    use_container_width=True,
                                    hide_index=True
                                )
                            
                            with tabs[1]:  # Visualization tab
                                # IMPORTANT: Only show visualization UI when we have a visualization
                                if message.get('visualization') is not None:
                                    # Get message index for the interactive controls
                                    message_index = message.get('message_index', len(st.session_state.messages) - 1)
                                    
                                    # Display the chart in a styled container
                                    with st.container():
                                        # Display stats above the chart
                                        df = message['sql_df']
                                        if len(df) > 0:
                                            summary_cols = st.columns(3)
                                            with summary_cols[0]:
                                                st.markdown(f"**Rows**: {millify(len(df))}")
                                            with summary_cols[1]:
                                                st.markdown(f"**Columns**: {len(df.columns)}")
                                            with summary_cols[2]:
                                                numeric_cols = df.select_dtypes(include=['number']).columns
                                                if len(numeric_cols) > 0:
                                                    # Calculate sum of first numeric column
                                                    col_sum = df[numeric_cols[0]].sum()
                                                    st.markdown(f"**Sum of {numeric_cols[0]}**: {millify(col_sum, 1)}")
                                                    
                                    # Create container for chart visualization
                                    chart_container = st.container()
                                    
                                    # Display the chart
                                    with chart_container:
                                        # Use the original visualization first time, then update with customized chart
                                        if f"custom_chart_{message_index}" not in st.session_state:
                                            st.plotly_chart(message['visualization'], use_container_width=True)
                                        else:
                                            st.plotly_chart(st.session_state[f"custom_chart_{message_index}"], use_container_width=True)
                                    
                                    # Create an expander for customization options
                                    with st.expander("✨ Customize this visualization", expanded=False):
                                    
                                        st.markdown("""
                                            <div style="margin-bottom: 15px; font-size: 0.95rem; color: #334155;">
                                                Adjust the chart parameters to explore your data in different ways
                                            </div>
                                        """, unsafe_allow_html=True)
                                        
                                        # Chart controls in two columns with modern styling
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            chart_type = st.selectbox(
                                                "Chart Type",
                                                ["bar", "line", "scatter", "pie", "histogram", "box", "area"],
                                                index=["bar", "line", "scatter", "pie", "histogram", "box", "area"].index(
                                                    st.session_state.get(f"chart_type_{message_index}", 
                                                    message.get('viz_type', 'bar')) if st.session_state.get(f"chart_type_{message_index}", 
                                                    message.get('viz_type', 'bar')) in 
                                                    ["bar", "line", "scatter", "pie", "histogram", "box", "area"] 
                                                    else "bar"
                                                ),
                                                key=f"chart_type_{message_index}"
                                            )
                                            
                                            x_columns = df.columns.tolist()
                                            default_x = st.session_state.get(f"x_axis_{message_index}", x_columns[0] if x_columns else None)
                                            x_axis = st.selectbox(
                                                "X-Axis",
                                                x_columns,
                                                index=x_columns.index(default_x) if default_x in x_columns else 0,
                                                key=f"x_axis_{message_index}"
                                            )
                                            

                                        
                                        with col2:
                                            color_options = [None] + df.columns.tolist()
                                            default_color = st.session_state.get(f"color_{message_index}", None)
                                            color = st.selectbox(
                                                "Color By",
                                                color_options,
                                                index=color_options.index(default_color) if default_color in color_options else 0,
                                                key=f"color_{message_index}"
                                            )
                                            
                                            # Y-axis selector (conditional based on chart type)
                                            y_columns = [None] + df.columns.tolist()
                                            if chart_type not in ["histogram", "pie"]:
                                                selectbox_key = f"y_axis_{message_index}"
                                                
                                                # If the key doesn't exist in session state yet, initialize with a default
                                                if selectbox_key not in st.session_state:
                                                    default_y = y_columns[1] if len(y_columns) > 1 else None
                                                    st.session_state[selectbox_key] = default_y
                                                
                                                # Now use the selectbox with just the key, no index parameter
                                                y_axis = st.selectbox(
                                                    "Y-Axis",
                                                    options=y_columns,
                                                    key=selectbox_key
                                                )
                                            else:
                                                # For histogram and pie, no Y-axis selection needed
                                                y_axis = None if chart_type == "histogram" else df.columns[1] if len(df.columns) > 1 else df.columns[0]
                                            
                                                
                                        # Apply changes button
                                        if st.button("Apply Changes", use_container_width=True, key=f"apply_chart_{message_index}"):
                                            # Configure chart parameters based on selections
                                            chart_map = {
                                                "bar": px.bar,
                                                "line": px.line,
                                                "scatter": px.scatter,
                                                "pie": px.pie,
                                                "histogram": px.histogram,
                                                "box": px.box,
                                                "area": px.area
                                            }

                                            # Basic arguments for the chart
                                            args = {
                                                "data_frame": df,
                                                "template": "plotly_white",
                                            }

                                            # Add conditional parameters based on chart type
                                            if chart_type == "pie":
                                                args.update({
                                                    "names": x_axis,
                                                    "values": y_axis if chart_type != "histogram" else None,
                                                    "color": x_axis,
                                                    "color_discrete_sequence": px.colors.sequential.Viridis
                                                })
                                            elif chart_type == "histogram":
                                                args.update({
                                                    "x": x_axis,
                                                    "color": color,
                                                    "opacity": 0.8,
                                                    "nbins": 20
                                                })
                                            else:
                                                args.update({
                                                    "x": x_axis,
                                                    "y": y_axis,
                                                    "color": color,
                                                    "labels": {
                                                        x_axis: x_axis,
                                                        y_axis: y_axis if y_axis else ""
                                                    }
                                                })
                                            
                                            # Create the chart
                                            try:
                                                fig = chart_map[chart_type](**args)
                                                
                                                # Apply consistent styling
                                                fig.update_layout(
                                                    font_family="Inter, sans-serif",
                                                    title_font_family="Plus Jakarta Sans, sans-serif",
                                                    title_font_size=16,
                                                    plot_bgcolor="rgba(250, 250, 252, 0.9)",
                                                    paper_bgcolor="rgba(255, 255, 255, 0)",
                                                    title={
                                                        'x': 0.5,
                                                        'xanchor': 'center'
                                                    },
                                                    margin=dict(l=40, r=40, t=60, b=40),
                                                    legend=dict(
                                                        orientation="h",
                                                        yanchor="bottom",
                                                        y=1.02,
                                                        xanchor="right",
                                                        x=1
                                                    )
                                                )
                                                
                                                # Add grid lines for most chart types
                                                if chart_type not in ["pie"]:
                                                    fig.update_yaxes(
                                                        showgrid=True, 
                                                        gridwidth=1, 
                                                        gridcolor="rgba(226, 232, 240, 0.6)"
                                                    )
                                                    fig.update_xaxes(
                                                        showgrid=True, 
                                                        gridwidth=1, 
                                                        gridcolor="rgba(226, 232, 240, 0.6)"
                                                    )
                                                
                                                # Store the chart in session state
                                                st.session_state[f"custom_chart_{message_index}"] = fig
                                                # Force a rerun to update the visualization
                                                st.rerun()
                                                
                                            except Exception as e:
                                                st.error(f"Error generating chart: {e}")
                                    
                                    # Add context about the visualization type
                                    if 'viz_type' in message:
                                        viz_type = message['viz_type']
                                        viz_descriptions = {
                                            "time_series": "📈 Time Series visualization showing trends over time",
                                            "scatter": "📊 Scatter plot showing the relationship between variables",
                                            "bar": "📊 Bar chart showing key metrics from your query",
                                            "categorical_bar": "📊 Bar chart comparing values across categories",
                                            "histogram": "📊 Histogram showing the distribution of values",
                                            "count": "📊 Count plot showing frequency of categories",
                                            "pie": "🥧 Pie chart showing proportion of categories",
                                            "box": "📦 Box plot showing distribution statistics",
                                            "area": "📊 Area chart showing cumulative values over a dimension"
                                        }
                                        st.caption(viz_descriptions.get(viz_type, f"📊 {viz_type.title()} chart based on your data"))
                                else:
                                    st.info("No visualization available for this data.", icon="ℹ️")
        
                            with tabs[2]:  # SQL Query tab
                                st.caption("Generated SQL query")
                                st.code(message['sql'], language='sql')
                    
                    # Handle suggestions - only if suggestions exist in this message
                    if message.get('role') == 'assistant' and message.get('suggestions') and len(message.get('suggestions', [])) > 0:
                        with st.expander("❓ Suggested Questions"):
                            for suggestion in message['suggestions']:
                                st.markdown(f"• **{suggestion}**")
                
                elif message["role"] == "❗" and message.get('type') == 'hint':
                    st.warning(message['text'])  # hint messages
    
    # Chat input container
    with stylable_container(
        key='chat_input',
        css_styles="""{
            border-radius: 12px; 
            padding: 15px 20px; 
            background-color: white;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }"""
    ):
        c1, c2 = st.columns([1000,1]) # Use small dummy second column to avoid objects pushing off right edge of container
        
    with c1: 
            if prompt := st.chat_input("How can I help?"):
                # Add user message to history
                #st.session_state.messages.append({"role": "user", "text": prompt})
                
                # Check if any tools/services are active
                if len(get_tool_resources()) == 0:
                    st.session_state.messages.append({
                        "role": "❗", 
                        "type": "hint", 
                        "text": 'Note: You are using Cortex Agent without any active services or tools. Configure them in the sidebar.'
                    })
                
                # Process the prompt - this is the key part
                try:
                    with st.spinner('Thinking...'):
                        response = process_prompt(prompt)
                    
                    # Format and display the response
                    if response is not None:
                        format_bot_message(response)
                        st.rerun()
                except Exception as e:
                    st.error(f"Error processing request: {str(e)}")

# Footer with usage tips
    with st.expander("Usage Tips", expanded=False):
        st.markdown("""
        ### 💡 Tips for best results
        
        - **Be specific** in your questions for more accurate answers
        - Enable **Cortex Search** services to query documentation
        - Add **Semantic Models** to analyze your data with natural language
        - Try asking for **visualizations** of your data
        - Ask for **suggestions** if you're not sure what to ask
        """)

if __name__ == "__main__":
    main()