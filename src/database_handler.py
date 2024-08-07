
from langchain_community.utilities import SQLDatabase

class DatabaseHandler:
    def __init__(self):
        self.db_url="postgresql://postgres:adminadmin@localhost:5432/postgres"
        self.db = SQLDatabase.from_uri(self.db_url)