from src.agent import AgentState, Agent
from langchain.globals import set_debug
from src.logger_setup import logger
from langgraph.checkpoint.memory import MemorySaver
import json
from langchain.globals import set_verbose
from langchain.globals import set_debug
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph

class WorkFlow:

    def __init__(self, prompt, plotting_graph_structure=False, 
                 is_in_debug_mode:str=False, is_verbose:bool=False,
                 sql_saver_checkpoint:bool=False) -> None:
        
        set_debug(is_in_debug_mode)
        set_verbose(is_verbose) 
        self.plotting_graph_structure = plotting_graph_structure
        self.prompt = prompt
        self.agent = Agent()
        if sql_saver_checkpoint:
            conn = sqlite3.connect("checkpoints.sqlite",  check_same_thread=False)
            self.memory = SqliteSaver(conn)
        else:
            self.memory = MemorySaver()
        self.thread = {"configurable": {"thread_id": "1"}}


    def setting_workflow(self):

        self.workflow = StateGraph(AgentState)
        self.workflow.add_node("call_model", self.agent.call_model)
        self.workflow.add_node("execute_sql_query", self.agent.execute_sql_query)
        self.workflow.add_node("execute_python", self.agent.execute_python)
        self.workflow.set_entry_point("call_model")
        self.workflow.add_edge("execute_sql_query", "execute_python")
        self.workflow.add_edge("execute_python", "call_model")
        self.workflow.add_conditional_edges("call_model", self.agent.should_continue)       
        self.app = self.workflow.compile(checkpointer=self.memory, interrupt_before=["execute_sql_query"], debug=False)

    def running_agent(self):

        self.setting_workflow()
        if self.plotting_graph_structure:
            self.app.get_graph().draw_mermaid_png(output_file_path="graph.png")

        inputs = {"messages": [("human", self.prompt)]}

        for event in self.app.stream(inputs, self.thread, stream_mode="values"):
            logger.info(event)

        #Getting the SQL query        
        arguments_str = event['messages'][1].additional_kwargs['tool_calls'][0]['function']['arguments']
        arguments_dict = json.loads(arguments_str)
        select_query = arguments_dict['select_query']
        logger.info(f'\n\n\nQUERY: {select_query}\n' )

        user_approval = input("Do you want to go execute the query? (yes/no): ")

        if user_approval.lower() == "yes":

            self.app.invoke(None, self.thread)
            snapshot = self.app.get_state(self.thread,)

            while snapshot.next:
                print("\n---\n")
                self.app.invoke(None, self.thread)
                snapshot = self.app.get_state(self.thread,)
      
        else:
            logger.info("Operation cancelled by user.")




if __name__ == "__main__":
    workflow=WorkFlow(prompt="graph the total sales values")
    workflow.running_agent()