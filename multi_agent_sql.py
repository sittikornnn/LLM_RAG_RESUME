import os
from dotenv import load_dotenv
import pyodbc
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.tools import AgentTool, FunctionTool
import asyncio
import logging
import re

# Setup logging
logging.basicConfig(filename='myapp.log', level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Setup Google API Key
try:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"
    print("✅ Gemini API key setup complete.")
except Exception as e:
    print(f"🔑 Authentication Error: Please make sure you have added 'GOOGLE_API_KEY' to your secrets. Details: {e}")

# Database Configuration Helper
def get_db_connection():
    server = os.getenv("DB_SERVER", "LAPTOP-MJRT53TF")
    database = os.getenv("DB_NAME", "ComputerVision")
    username = os.getenv("DB_USER", "sittikorn")
    password = os.getenv("DB_PASSWORD", "12345")
    # Ensure the driver is correct for the user's environment
    connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
    return pyodbc.connect(connection_string)

# --- Tools ---

def basic_calculator(expression: str) -> str:
    """คำนวณนิพจน์ทางคณิตศาสตร์"""
    logging.info(f"Tool:basic_calculator invoked with expression: {expression}")
    try:
        if not isinstance(expression, str) or not expression.strip():
            return "Error: Empty or invalid expression."
        expr = expression
        expr = re.sub(r'\bof\b', '*', expr, flags=re.IGNORECASE)
        expr = re.sub(r'(\d+(?:\.\d+)?)\%', r'(\1/100)', expr)
        safe_expression = re.sub(r'[^0-9\+\-\*\/\.\(\)\s]', '', expr)
        if not safe_expression.strip():
            return "Error: Empty or unsafe expression after sanitization."
        result_val = eval(safe_expression)
        if isinstance(result_val, float) and result_val.is_integer():
            result_val = int(result_val)
        logging.info(f"Tool:basic_calculator result: {result_val}")
        return str(result_val)
    except Exception as e:
        logging.info(f"Tool:basic_calculator error: {e}")
        return f"Calculation Error: {e}"

def get_db_schema() -> str:
    """Retrieves the database schema (tables and columns).

    Returns:
        A string representation of the database schema.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query to get tables and columns
        query = """
        SELECT TABLE_NAME, COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = 'dbo'
        ORDER BY TABLE_NAME, ORDINAL_POSITION
        """
        cursor.execute(query)
        
        schema_data = {}
        for row in cursor.fetchall():
            table_name = row.TABLE_NAME
            column_name = row.COLUMN_NAME
            if table_name not in schema_data:
                schema_data[table_name] = []
            schema_data[table_name].append(column_name)
            
        conn.close()
        
        schema_str = "Database Schema:\n"
        for table, columns in schema_data.items():
            schema_str += f"- Table: {table}\n  Columns: {', '.join(columns)}\n"
            
        return schema_str
    except Exception as e:
        return f"Error retrieving schema: {str(e)}"

def run_sql_query(query: str) -> str:
    """Executes a SQL query against the database.

    Args:
        query: The SQL query string to execute.

    Returns:
        JSON string containing the query results or error message.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        
        if cursor.description:
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            conn.close()
            return str(results)
        else:
            conn.commit()
            conn.close()
            return "Query executed successfully."
            
    except Exception as e:
        return f"Error executing query: {str(e)}"

# --- Agents ---

sql_agent = Agent(
    name="sql_expert_agent",
    model="gemini-2.5-flash-lite",
    description="An agent that can query a SQL Server database.",
    instruction="""
    You are a SQL expert. Your goal is to answer questions about the database content.
    
    CRITICAL INSTRUCTION:
    1. For ANY new request involving the database, you MUST FIRST call `get_db_schema` to see the actual table names and columns.
    2. DO NOT GUESS table names. If you think a table might exist (e.g., 'cameras'), CHECK THE SCHEMA FIRST.
    3. Once you have the schema, construct a valid SQL query using `run_sql_query`.
    4. If the query fails, analyze the error and try to fix it.
    5. Return the raw data or a summary of the findings.
    """,
    tools=[get_db_schema, run_sql_query],
    output_key="sql_result",
)

root_agent = Agent(
    name="root_agent",
    model="gemini-2.5-flash-lite",
    description="The main coordinator agent.",
    instruction="""
    คุณคือผู้ช่วยอัจฉริยะที่มีความสามารถในการตอบคำถามจากฐานข้อมูลและคำนวณเลข
    - หากผู้ใช้ถามเกี่ยวกับข้อมูลใน Database ให้ใช้ `sql_expert_agent` ในการดึงข้อมูล
    - หากมีการคำนวณ ให้ใช้ `basic_calculator`
    - ตอบคำถามเป็นภาษาไทย ให้กระชับ และเข้าใจง่าย
    - สรุปข้อมูลที่ได้จาก Database ให้เป็นประโยชน์ต่อผู้ใช้
    """,
    tools=[
        AgentTool(sql_agent),
        FunctionTool(basic_calculator),
    ],
)

# --- Runner ---

runner = InMemoryRunner(agent=root_agent)

async def main():
    print("ChatBot Ready! (Type 'exit' to quit)")
    while True:
        user_input = input("User >> ")
        if user_input.lower() in ["exit", "quit"]:
            break
        try:
            # Using run_debug as it supports input and returns execution trace
            response = await runner.run_debug(user_input)
            
            # # Extract the final response from the trace
            # if response and isinstance(response, list) and len(response) > 0:
            #     # The last item usually contains the final answer
            #     last_step = response[-1]
            #     if hasattr(last_step, 'content'):
            #         print(f"ChatBot >> {last_step.content}")
            #     else:
            #         print(f"ChatBot >> {last_step}")
            # else:
            #     print(f"ChatBot >> {response}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())