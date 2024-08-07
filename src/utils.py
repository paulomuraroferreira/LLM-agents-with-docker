from dataclasses import dataclass
from pathlib import Path

current_file_dir = Path(__file__).parent

@dataclass
class PathInfo:
    CSV_PATH:str = str(current_file_dir.parent / "data" )