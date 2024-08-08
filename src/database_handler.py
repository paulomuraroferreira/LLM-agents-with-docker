
from langchain_community.utilities import SQLDatabase
import os
from dotenv import load_dotenv
load_dotenv()

class DatabaseHandler:
    def __init__(self):
        self.db_url=os.getenv("DATABASE_URL")
        self.db = SQLDatabase.from_uri(self.db_url)