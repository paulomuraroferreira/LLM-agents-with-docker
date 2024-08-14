from src.workflow import WorkFlow

prompt = input('Agent input:\n')
workflow=WorkFlow(prompt=prompt)
workflow.running_agent()