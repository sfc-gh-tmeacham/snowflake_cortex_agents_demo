-- Set the current role to ACCOUNTADMIN
USE ROLE ACCOUNTADMIN;

-- Fetch the most recent files from the specified Github repository
ALTER GIT REPOSITORY GITHUB_REPO_CORTEX_AGENTS_DEMO FETCH;

-- Create a Streamlit app based on the status of Behavior Change Bundle 2025_01
BEGIN
  -- Check if 2025 Bundle is enabled (for multi-page Streamlit apps)
  LET status_2025_01 STRING := (SELECT SYSTEM$BEHAVIOR_CHANGE_BUNDLE_STATUS('2025_01'));
  
  -- Log the bundle status
  SYSTEM$LOG_INFO('Bundle 2025_01 is ' || :status_2025_01);
  
  -- Check if the bundle is ENABLED or RELEASED and execute appropriate commands
  IF (status_2025_01 = 'ENABLED' OR status_2025_01 = 'RELEASED') THEN
    -- If bundle 2025_01 is DISABLED, the compiler won't recognize the new CREATE STREAMLIT syntax
    -- To work around this, the statement is stored in a string variable
    let smt string := $$
      -- Create Streamlit app with multi-file editing support
      CREATE OR REPLACE STREAMLIT CORTEX_AGENT_CHAT_APP
        FROM @CORTEX_AGENTS_DEMO.PUBLIC.GITHUB_REPO_CORTEX_AGENTS_DEMO/branches/main/agent_app/
        MAIN_FILE = 'app.py'
        QUERY_WAREHOUSE = COMPUTE_WH
        TITLE = 'Cortex Agents Chat App'
        COMMENT = 'Demo Streamlit frontend for Cortex Agents'
    $$;

    -- Execute the CREATE STREAMLIT statement
    EXECUTE IMMEDIATE :smt;

    RETURN 'Bundle 2025_01 is ENABLED. Created Streamlit app with multi-file editing.';
    
  ELSE
    -- If the bundle is DISABLED, execute these commands for single-file editing
    -- Create a stage for the Streamlit App
    CREATE OR REPLACE STAGE STREAMLIT_APP
      DIRECTORY = (ENABLE = TRUE)
      ENCRYPTION = ( TYPE = 'SNOWFLAKE_FULL' );

    -- Copy Streamlit App files into the stage
    COPY FILES
      INTO @STREAMLIT_APP
      FROM @CORTEX_AGENTS_DEMO.PUBLIC.GITHUB_REPO_CORTEX_AGENTS_DEMO/branches/main/agent_app/;
    
    -- Refresh the stage to reflect the new files
    ALTER STAGE STREAMLIT_APP REFRESH;

    -- Create Streamlit App with single-file editing
    CREATE OR REPLACE STREAMLIT CORTEX_AGENT_CHAT_APP
        ROOT_LOCATION = '@CORTEX_AGENTS_DEMO.PUBLIC.STREAMLIT_APP'
        MAIN_FILE = '/app.py'
        QUERY_WAREHOUSE = 'COMPUTE_WH'
        TITLE = 'Cortex Agents Chat App'
        COMMENT = 'Demo Streamlit frontend for Cortex Agents';

    RETURN 'Bundle 2025_01 is DISABLED. Created Streamlit app with single file editing.';
  END IF;
END
