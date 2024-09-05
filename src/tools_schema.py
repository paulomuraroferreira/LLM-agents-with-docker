from langchain_core.pydantic_v1 import BaseModel, Field
from typing import Annotated, List, Sequence, TypedDict

class create_df_from_sql(BaseModel):
    """Execute a PostgreSQL SELECT statement and use the results to create a DataFrame with the given column names."""

    select_query: str = Field(..., description="A PostgreSQL SELECT statement.")
    # We're going to convert the results to a Pandas DataFrame that we pass
    # to the code intepreter, so we also have the model generate useful column and
    # variable names for this DataFrame that the model will refer to when writing
    # python code.
    df_columns: List[str] = Field(
        ..., description="Ordered names to give the DataFrame columns."
    )
    df_name: str = Field(
        ..., description="The name to give the DataFrame variable in downstream code."
    )

# Tool schema for writing Python code
class python_shell(BaseModel):
    """Execute Python code that analyzes the DataFrames that have been generated. Make sure to print any important results."""

    imports: str = Field(description="Code block import statements")
    code: str = Field(description="Code block not including import statements. Make sure to print any important results.")


# Tool schema for writing Python code
class python_code(BaseModel):
    """Execute Python code that analyzes the DataFrames that have been generated. Make sure to print any important results."""

    code_to_load_csv: str  = Field(description="Code block to load csv file")
    imports: str = Field(description="Code block import statements")
    code_block_without_imports: str = Field(description="Code block not including import statements. Make sure to print any important results.")