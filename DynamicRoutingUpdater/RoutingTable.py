import sys, os, re

def stdout(out:str):
    sys.stdout.write(f"{out}\n")
    sys.stdout.flush()
def stderr(out:str):
    sys.stderr.write(f"{out}\n")
    sys.stderr.flush() 

def operationOut(command: str = None) -> None:
    result = os.system(command)
    if result != 0:
        stderr(f"[FAILED]: {command}\n\tResult: {result}")
    else:
        stdout(f"[SUCCESS]: {command}")

class RoutingTable:
    """"""
    rt_table_file = "/etc/iproute2/rt_tables"
    
    tableBaseName: str = None
    adapterNames: list[str] = []
    
    def __init__(self, tableBaseName: str = None, adapterNames: list[str] = []) -> None:
        if (tableBaseName is None):
            raise ValueError(f"tableBaseName is {tableBaseName}, None is not supported!")
        self.tableBaseName = tableBaseName
        if (len(adapterNames) == 0):
            raise ValueError(f"adapterNames is {adapterNames}, Empty is not supported!")
        self.adapterNames = adapterNames
        
    
    
    @staticmethod
    def getRoutingTables() -> list[str]:
        """Read routing table to list
        """
        rt_entries: list[str] = []
        
        with open(RoutingTable.rt_table_file, "r") as rt_tables:
            for line in rt_tables:
                if len(line.strip("\t\r\n")) > 0:
                    rt_entries.append(line.strip("\n"))
                else:
                    sys.stdout.write("Skipping empty line in rt_tables!\n")
        return rt_entries
    
    def deleteMyEntries(self) -> None:
        """Removes DRU created routing table entries
        """    
        escapedTableName = re.escape(self.tableBaseName)
        directTable = re.compile(r"[0-9]+\t{}[0-9]+(?!\w)".format(escapedTableName), re.IGNORECASE)
                
        sys.stdout.write("Removing old tables..\n")
        updatedTables: list[str] = []
        for line in RoutingTable.getRoutingTables():
            if directTable.search(line) == None:
                updatedTables.append(line)
        
        rewrite = open(self.rt_table_file, "w")
        for entry in updatedTables:
            rewrite.write("{}\n".format(entry))
        rewrite.close()
        
    def addMyEntries(self) -> dict:
        """
        """
        configuredTables: dict = {}
        self.deleteMyEntries()
        acceptableTableIds = list(range(0, 255))
        activeTablesCheck = re.compile(r"^(?!#)[0-9]+")
        for line in RoutingTable.getRoutingTables():
            activeIds = activeTablesCheck.findall(line)
            if len(activeIds) > 0:
                activeId = int(activeIds[0])
                if (activeId in acceptableTableIds):
                    acceptableTableIds.remove(activeId)
        
        appendableTables: list[str] = []
        for i, adapter in enumerate(self.adapterNames):
            tableId = acceptableTableIds.pop(0)
            ntableName: str = "{}{}".format(self.tableBaseName, i)
            tableEntry: str = "{}\t{}".format(tableId, ntableName)
            appendableTables.append(tableEntry)
            configuredTables[adapter] = ntableName
        sys.stdout.write("Creating new tables\n")
        with open(self.rt_table_file, "a") as file:
            for table in appendableTables:
                file.write("{}\n".format(table))
                sys.stdout.write(f"{table}\n")
        return configuredTables
        