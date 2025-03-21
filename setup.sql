-- =============================================
-- SESSION SETUP
-- =============================================
-- Set session context for the current user
USE ROLE SYSADMIN;                -- Your Role
USE DATABASE SANDBOX_DB;          -- Target database for our work
USE SCHEMA PUBLIC;                -- Initial schema (will be changed later)
USE WAREHOUSE COMPUTE_WH;         -- Compute resources for our session

-- =============================================
-- TEAM CONFIGURATION
-- =============================================
-- Define team name variable (must be uppercase with no spaces)
SET team_name = 'SUPERSTARS';

-- Create a dedicated schema for the team if it doesn't already exist
CREATE SCHEMA IF NOT EXISTS IDENTIFIER($team_name);
USE SCHEMA IDENTIFIER($team_name);     -- Switch to the team's schema

-- Verify schema creation was successful
show terse schemas;                    -- Display available schemas

-- =============================================
-- GIT REPOSITORY SETUP
-- =============================================
-- Create a Git repository integration in Snowflake for the EMS Protocol Chatbot project
CREATE GIT REPOSITORY IF NOT EXISTS GITHUB_REPO_CORTEX_AGENTS_DEMO
	ORIGIN = 'https://github.com/sfc-gh-tmeacham/snowflake_cortex_agents_demo.git' 
	API_INTEGRATION = 'GITHUB_ALL'     -- Uses pre-configured GitHub integration
	COMMENT = 'Git Repo for Michigan EMS Protocol Chatbot HOL';

-- Display details about the Git repository configuration
DESCRIBE GIT REPOSITORY GITHUB_REPO_CORTEX_AGENTS_DEMO;

-- Synchronize with the remote repository to ensure we have the latest code
ALTER GIT REPOSITORY GITHUB_REPO_CORTEX_AGENTS_DEMO FETCH;

-- =============================================
-- GIT REPOSITORY EXPLORATION
-- =============================================
-- Example Git commands for repository exploration
-- For more information: https://docs.snowflake.com/en/developer-guide/git/git-operations

-- List all branches in the repository
SHOW GIT BRANCHES IN GITHUB_REPO_CORTEX_AGENTS_DEMO;

-- List files in the main branch
LS @GITHUB_REPO_CORTEX_AGENTS_DEMO/branches/hol;

-- =============================================
-- STREAMLIT APP CREATION
-- =============================================
-- Generate a unique notebook name based on team name
SET app_name = concat_ws('_',$team_name,'CORTEX_AGENT_CHAT_APP');

-- Preview the generated notebook name
SELECT $app_name as app_name;

-- Create Streamlit app with method based on status of Behavior Change Bundle 2025_01
BEGIN
  -- Check if 2025 Bundle is enabled (multi-page streamlit apps)
  LET status_2025_01 STRING := (SELECT SYSTEM$BEHAVIOR_CHANGE_BUNDLE_STATUS('2025_01'));
  -- Log result
  SYSTEM$LOG_INFO('Bundle 2025_01 is ' || :status_2025_01);
  
  -- Check if the bundle is ENABLED and execute appropriate commands
  IF (status_2025_01 = 'ENABLED' OR status_2025_01 = 'RELEASED') THEN

    -- Create Streamlit with multifile editing
    CREATE OR REPLACE STREAMLIT IDENTIFIER($app_name)
      FROM @GITHUB_REPO_CORTEX_AGENTS_DEMO/branches/hol/agent_app/
      MAIN_FILE = 'app.py'
      QUERY_WAREHOUSE = COMPUTE_WH
      TITLE = $app_name
      COMMENT = 'Demo Streamlit frontend for Cortex Agents';

    RETURN 'Bundle 2025_01 is ENABLED. Created Streamlit app with multi-file editing.';
  ELSE
    -- Check if the bundle is DISABLED and execute appropriate commands
      -- Create stage for the Streamlit App
      CREATE OR REPLACE STAGE STREAMLIT_APP
        DIRECTORY = (ENABLE = TRUE)
        ENCRYPTION = ( TYPE = 'SNOWFLAKE_FULL' );

      -- Copy Streamlit App into to stage
      COPY FILES
        INTO @STREAMLIT_APP
        FROM @GITHUB_REPO_CORTEX_AGENTS_DEMO/branches/hol/agent_app/;
      ALTER STAGE STREAMLIT_APP REFRESH;

      -- Create Streamlit App
      CREATE OR REPLACE STREAMLIT IDENTIFIER($app_name)
          ROOT_LOCATION = '@STREAMLIT_APP'
          MAIN_FILE = '/app.py'
          QUERY_WAREHOUSE = COMPUTE_WH
          TITLE = $app_name
          COMMENT = 'Demo Streamlit frontend for Cortex Agents';

      RETURN 'Bundle 2025_01 is DISABLED. Created Streamlit app with single file editing.';
  END IF;
END;

