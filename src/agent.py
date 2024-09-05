from typing import Annotated, List, Sequence, TypedDict
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, StateGraph
import operator
from src.database_handler import DatabaseHandler
from src.config_handler import ConfigHandler
import pandas as pd
import io
import base64
import json
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from src.utils import PathInfo
from src.logger_setup import logger
from src.tools_schema import create_df_from_sql, python_shell

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

class Agent:

    def __init__(self, save_image=False):
        self.db = DatabaseHandler()
        self.config = ConfigHandler()
        self.config_handler = ConfigHandler()
        self.db = self.db.db
        self.llm = self.config.llm
        self.repl_tool = self.config.repl_tool
        self.repl = self.config.repl
        self.save_image = save_image

        self.system_prompt = f"""\
                            You are an expert at PostgreSQL and Python. You have access to a PostgreSQL database \
                            with the following tables

                            {self.db.table_info}

                            Given a user question related to the data in the database, \
                            first get the relevant data from the table as a DataFrame using the create_df_from_sql tool. Then use the \
                            python_shell to do any analysis required to answer the user question."""

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                ("placeholder", "{messages}"),
            ]
        )


    def call_model(self, state: AgentState) -> dict:
        """Call model with tools passed in."""
        messages = []

        chain = self.prompt | self.llm.bind_tools([create_df_from_sql, python_shell])
        messages.append(chain.invoke({"messages": state["messages"]}))

        return {"messages": messages}

    def execute_sql_query(self, state: AgentState) -> dict:
        """Execute the latest SQL queries."""
        messages = []

        for tool_call in state["messages"][-1].tool_calls:
            if tool_call["name"] != "create_df_from_sql":
                continue

            # Execute SQL query
            logger.info(f'Executing SQL query: {tool_call["args"]["select_query"]}')

            res = self.db.run(tool_call["args"]["select_query"], fetch="cursor").fetchall()
          
            # Convert result to Pandas DataFrame
            df_columns = tool_call["args"]["df_columns"]
            df = pd.DataFrame(res, columns=df_columns)
            df_name = tool_call["args"]["df_name"]

            df.to_csv(f'{PathInfo.CSV_PATH}/{df_name}.csv')

            # Add tool output message
            tool_output = {'df_name': df_name, 
                           'content': f"Generated dataframe {df_name} with columns {df_columns}",
                           'tool_call_id': tool_call["id"],
                           'tool_name': tool_call["name"]}

            messages.append(ToolMessage(
                content=f"Generated dataframe {df_name} with columns {df_columns}",
                artifact=tool_output,
                tool_call_id=tool_call["id"]
            ))

            logger.info(f"SQL query executed successfully: {tool_call['args']['select_query']}\n")

        return {"messages": messages}


    def _upload_dfs_to_repl(self, state: AgentState) -> str:
        """
        Upload generated dfs to code interpreter and return code for loading them.

        Note that code interpreter sessions are short-lived, so this needs to be done
        every agent cycle, even if the dfs were previously uploaded.
        """

        df_dicts = [
            msg.artifact['df_name']
            for msg in state["messages"]
            if isinstance(msg, ToolMessage) and msg.artifact['tool_name'] == "create_df_from_sql"
        ]

        df_code = "import pandas as pd\n" + "\n".join(
            f"{name} = pd.read_csv('/data/{name}.csv')" for name in df_dicts  
        )
        return df_code

    def _repl_result_to_msg_content(self, repl_result: dict) -> str:
        """
        Display images and include them in tool message content.
        """
        content = {}

        for k, v in repl_result.items():
            # Any image results are returned as a dict of the form:
            # {"type": "image", "base64_data": "..."}
            if isinstance(repl_result[k], dict) and repl_result[k]["type"] == "image":
                warnings.filterwarnings("ignore", category=UserWarning, message=".*Matplotlib.*GUI.*")
                base64_str = repl_result[k]["base64_data"]
                image_data = base64.b64decode(base64_str)
                image = mpimg.imread(io.BytesIO(image_data), format='png')
                plt.imshow(image)
                plt.axis('off')
                plt.show()

                if self.save_image:
                    #You can optionally save the image to a file:
                    with open(f"{PathInfo.DATA_FOLDER_PATH}/plot_from_docker.png", "wb") as f:
                        f.write(image_data)

            else:
                # Handle non-image output
                content[k] = repl_result[k]

        return json.dumps(content, indent=2)

    def execute_python(self, state: AgentState) -> dict:
        """
        Execute the latest generated Python code.
        """
        messages = []

        df_code = self._upload_dfs_to_repl(state)
        last_ai_msg = [msg for msg in state["messages"] if isinstance(msg, AIMessage)][-1]
        for tool_call in last_ai_msg.tool_calls:
            if tool_call["name"] != "python_shell":
                continue

            code_dict = {'code_to_load_csv': df_code,
                        'imports': tool_call["args"]["imports"],
                        'code_block_without_imports': tool_call["args"]["code"],}
            
            logger.info(f"Executing Python code: {code_dict}\n\n")
            
            repl_result = self.config_handler.invoke_repl(code_dict)

            content_ = self._repl_result_to_msg_content(repl_result).split('PLOT_BASE64:')[0].strip() + 'PLOT_BASE64: ...'

            messages.append(
                ToolMessage(
                    content = content_,
                    artifact= content_,
                    tool_call_id=tool_call["id"],
                )
            )

        return {"messages": messages}

    def should_continue(self, state: AgentState) -> str:
        """
        If any Tool messages were generated in the last cycle that means we need to call the model again to interpret the latest results.
        """
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            # Check if the last tool call was 'python_shell' and it returned a result
            last_tool_call = last_message.tool_calls[-1]
            if last_tool_call["name"] == "python_shell" and last_tool_call.get("output"):
                return END  # Stop the loop if python_shell returned a result
            else:
                return "execute_sql_query"
        else:
            return END