from langchain_openai import ChatOpenAI
from src.docker_container import DockerPythonREPL
from langchain_core.tools import Tool
import os
from utils import PathInfo
from dotenv import load_dotenv
load_dotenv(dotenv_path=PathInfo.ENV_FILE_PATH) 

class ConfigHandler:
    def __init__(self):
        self.llm = ChatOpenAI(model=os.getenv("LLM_MODEL"))
        self.repl = DockerPythonREPL()
        self.repl_tool = Tool(
            name="python_repl",
            description="A Python shell. Use this to execute python commands. Input should be a valid python command. If you want to see the output of a value, you should print it out with `print(...)`.",
            func=self.repl.run,
        )

    def invoke_repl(self, code):
        with self.repl:  
            repl_result = self.repl_tool.invoke(code)
            return repl_result

