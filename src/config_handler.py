from langchain_openai import ChatOpenAI
from docker_container import DockerPythonREPL
#from langfuse.callback import CallbackHandler
from langchain_core.tools import Tool
import os
from dotenv import load_dotenv
load_dotenv() 

class ConfigHandler:

    def __init__(self):

        self.llm = ChatOpenAI(model="gpt-4-turbo")

        self.repl = DockerPythonREPL()

        # self.langfuse_handler = CallbackHandler(
        #     public_key=os.getenv("LF_PUBLIC_KEY"),
        #     secret_key=os.getenv("LF_SECRET_KEY"),
        #     host=os.getenv("LF_HOST")
        # )

        self.repl_tool = Tool(
            name="python_repl",
            description="A Python shell. Use this to execute python commands. Input should be a valid python command. If you want to see the output of a value, you should print it out with `print(...)`.",
            func=self.repl.run,
        )
