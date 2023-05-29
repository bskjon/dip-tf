import subprocess
import json
import sys, os
from .objects import Rule

def stdout(out:str):
    sys.stdout.write(f"{out}\n")
    sys.stdout.flush()
    
def stderr(out:str):
    sys.stderr.write(f"[ERROR]: {out}\n")
    sys.stderr.flush() 
    
def operationOut(command: str = None) -> None:
    result = os.system(command)
    if result != 0:
        stderr(f"[FAILED]: {command}\n\tResult: {result}")
    else:
        stdout(f"[SUCCESS]: {command}")



class Rules:
    """_summary_
    """
    
    def __init__(self):
        """
        """
        
    @staticmethod
    def getRules(table: str = None) -> list[Rule]:
        """_summary_

        Args:
            table (str, optional): _description_. Defaults to None.

        Returns:
            list[Rule]: _description_
        """
        result: list[Rule] = []
        try:
            query = f"ip -j rule show table {table}" if table is not None and len(table) > 0 else "ip -j rule show"
            data: list[dict[str, any]] = json.loads(subprocess.getoutput(query))        
            if len(data) == 0:
                return result
            for item in data:
                mapped = Rule(
                    priority=item.get("priority"),
                    source=item.get("src"),
                    table=item.get("table")
                )
                result.append(mapped)
        except json.JSONDecodeError:
            stderr(f"No result for {query}")
            pass
        return result
    
    def addRule(self, source: str = None, table: str = None) -> None:
        if (source is None or table is None):
            raise ValueError(f"source is {source} and table is {table}, None is not supported!")
        command = f"ip rule add from {source} table {table}"
        operationOut(command)
    def deleteRule(self, table: str) -> None:
        command = f"ip rule del table {table}"
        operationOut(command)
    