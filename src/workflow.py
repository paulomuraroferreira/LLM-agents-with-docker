from src.agent import AgentState, StateGraph, Agent
from langchain.globals import set_debug
from src.logger_setup import logger
from langgraph.checkpoint.memory import MemorySaver
import json

class WorkFlow:

    def __init__(self, prompt, plotting_graph_structure=False, debug=False) -> None:
        
        set_debug(debug)    
        self.plotting_graph_structure = plotting_graph_structure
        self.prompt = prompt
        self.agent = Agent()
        self.memory = MemorySaver()
        self.thread = {"configurable": {"thread_id": "2"}}

    def setting_workflow(self):

        self.workflow = StateGraph(AgentState)

        self.workflow.add_node("call_model", self.agent.call_model)
        self.workflow.add_node("execute_sql_query", self.agent.execute_sql_query)
        self.workflow.add_node("execute_python", self.agent.execute_python)

        self.workflow.set_entry_point("call_model")
        self.workflow.add_edge("execute_sql_query", "execute_python")
        self.workflow.add_edge("execute_python", "call_model")
        self.workflow.add_conditional_edges("call_model", self.agent.should_continue)

        self.app = self.workflow.compile(checkpointer=self.memory, interrupt_before=["execute_sql_query"])

    def running_agent(self):

        self.setting_workflow()
        if self.plotting_graph_structure:
            self.app.get_graph().draw_mermaid_png(output_file_path="graph.png")

        #yeoutput = self.app.invoke({"messages": [("human", self.prompt)]})
        for event in self.app.stream({"messages": [("human", self.prompt)]}, self.thread, stream_mode="values"):
            logger.info(event["messages"])

        #Getting the SQL query        
        arguments_str = event['messages'][1].additional_kwargs['tool_calls'][0]['function']['arguments']
        arguments_dict = json.loads(arguments_str)
        select_query = arguments_dict['select_query']
        logger.info(f'\n\n\nQUERY: {select_query}\n' )

        user_approval = input("Do you want to go execute the query? (yes/no): ")
        from pprint import pprint
        if user_approval.lower() == "yes":
            # If approved, continue the graph execution
            #self.app.invoke(None, self.thread)
            for event in self.app.stream(None, self.thread, stream_mode="values"):
                print('\n'*5)
                pprint(event)

        else:
            logger.info("Operation cancelled by user.")




if __name__ == "__main__":
    workflow=WorkFlow(prompt="graph the total sales values")
    workflow.running_agent()