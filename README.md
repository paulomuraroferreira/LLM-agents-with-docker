# README

This repository is based on the code from LangChain's Azure Container Apps Dynamic Sessions Data Analyst Notebook, where an agent reads data from a PostgreSQL database, saves it in a CSV file, and executes code based on the CSV file, such as plotting a graph.

The main feature of the code was that it executed code in a container using Azure Container Apps dynamic sessions.

This project replaces the Azure Container Apps dynamic sessions with docker. So when the agent executes the code, it will create a docker container, execute the code, and then remove the container. This ensures that the host machine is safe from arbitrary code from the agent.

The agent architecture is as follows:

![image.png](README_files/image.png)

After the execute_sql_query node is executed, the data is saved as a CSV on the host machine. The Docker container then has read-only permission to access this CSV. If it plots anything, the image is passed back to the host machine via a Base64 string.


## Setup Instructions

1. Clone the repository:


```python
git clone <repository-url>
cd <repository-directory>
```

2. Install Dependencies:

Ensure you have Docker installed and running.
Install required Python packages:


```python
pip install -r requirements.txt
```

3. Environment Configuration:

Create a .env file and configure the following environment variables:


```python
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=your_postgres_url
```

4. Run the Application:

Start the Docker container for the Python REPL.
Execute the main script to initialize the workflow and handle user queries:


```python
python main.py
```
