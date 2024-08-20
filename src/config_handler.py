from langchain_openai import ChatOpenAI
from src.docker_container import DockerPythonREPL
from langchain_core.tools import Tool
import os
from langfuse.callback import CallbackHandler
from utils import PathInfo
from langchain_core.tools import StructuredTool
from dotenv import load_dotenv
load_dotenv(dotenv_path=PathInfo.ENV_FILE_PATH) 
from tools_schema import python_shell, python_code

class ConfigHandler:
    def __init__(self):
        self.llm = ChatOpenAI(model=os.getenv("LLM_MODEL")) 
        self.repl = DockerPythonREPL()
        self.repl_tool = StructuredTool(
            name="python_repl",
            description="A Python shell. Use this to execute python commands. Input should be a valid python command. If you want to see the output of a value, you should print it out with `print(...)`.",
            func=self.repl.run,
            args_schema=python_code,
        )
        self.langfuse_handler = CallbackHandler()

    def invoke_repl(self, code: dict):

        with self.repl:  
            repl_result = self.repl_tool.invoke(code)
            return repl_result

