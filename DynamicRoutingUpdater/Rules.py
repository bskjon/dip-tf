import logging
import subprocess
import json
import sys, os
from .objects import Rule
from typing import List

logging.basicConfig(level=logging.INFO)
    
def operationOut(command: str = None) -> None:
    result = os.system(command)
    if result != 0:
        logging.error(f"{command}\n\tResult: {result}")
    else:
        logging.info(f"{command}")


class Rules:
    """_summary_
    """
    
    def __init__(self):
        """
        """
        
    @staticmethod
    def getRules(table: str = None) -> List[Rule]:
        """_summary_

        Args:
            table (str, optional): _description_. Defaults to None.

        Returns:
            list[Rule]: _description_
        """
        result: List[Rule] = []
        try:
            query = f"ip -j rule show table {table}" if table is not None and len(table) > 0 else "ip -j rule show"
            data: List[dict[str, any]] = json.loads(subprocess.getoutput(query))        
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
            logging.error(f"No result for {query}")
            pass
        return result
    
    @staticmethod
    def flushRules(table: str = None, device: str = None) -> None:
        commands = [
            f"ip rule del table {table} oif {device}",
            f"ip rule del table {table} iif {device}",
            f"ip rule del table {table}"
        ]
        for command in commands:
            operationOut(command)
    
    def addRule(self, source: str = None, table: str = None) -> None:
        if (source is None or table is None):
            raise ValueError(f"source is {source} and table is {table}, None is not supported!")
        command = f"ip rule add from {source} table {table}"
        operationOut(command)
        
    def deleteRule(self, table: str) -> None:
        command = f"ip rule del table {table}"
        operationOut(command)
    