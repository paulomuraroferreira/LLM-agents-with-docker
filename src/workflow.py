from agent import AgentState, StateGraph, Agent

class WorkFlow:

    def __init__(self) -> None:
        from langchain.globals import set_debug
        set_debug(False)

        self.agent = Agent()

    def setting_workflow(self):

        self.workflow = StateGraph(AgentState)

        self.workflow.add_node("call_model", self.agent.call_model)
        self.workflow.add_node("execute_sql_query", self.agent.execute_sql_query)
        self.workflow.add_node("execute_python", self.agent.execute_python)

        self.workflow.set_entry_point("call_model")
        self.workflow.add_edge("execute_sql_query", "execute_python")
        self.workflow.add_edge("execute_python", "call_model")
        self.workflow.add_conditional_edges("call_model", self.agent.should_continue)

        self.app = self.workflow.compile()

    def running_agent(self):

        self.setting_workflow()
        print(self.app.get_graph().draw_mermaid_png(output_file_path="graph.png"))
        output = self.app.invoke({"messages": [("human", "graph the total sales values")]})#,config={"callbacks": [langfuse_handler]})
        print(output["messages"][-1].content)

if __name__ == "__main__":
    workflow=WorkFlow()
    workflow.running_agent()