from io import TextIOWrapper
import json
import random
import signal
from threading import Thread
import threading
from typing import List
from .objects import NetworkAdapter, RoutingManager
from .NetworkHookHandler import NetworkHookHandler
from .NetworkInfoWatcher import NetworkInfoWatcher
import os, sys, time, re, errno
import netifaces 
       

class DynamicRoutingUpdater:
    """DynamicRoutingUpdater, modify routing table
    """
    dipwa: NetworkHookHandler = None
    niw: NetworkInfoWatcher = None
    
    configuredTables = {}
    tableName = "direct"
    
    nics: List[str] = []
    
    threads: List[Thread] = []
    
    
    def flipper(self) -> str:
        faces: List[str] = [
            "(╯°□°）╯︵ ┻━┻",
            "(┛◉Д◉)┛彡┻━┻",
            "(ノಠ益ಠ)ノ彡┻━┻",
            
            "(ノ｀´)ノ ~┻━┻",
            "┻━┻ ︵ヽ(`Д´)ﾉ︵ ┻━┻"
        ]
        return random.choice(faces)
    
    def __init__(self, reference: str = "reference.json") -> None:
        """
        """
        sys.stdout.write(f"{self.flipper()}\n")
        sys.stdout.write("Loading up Dynamic Routing Updater\n")
        sys.stdout.write("Reading configuration\n")
        reference = json.load(open(reference))
        self.nics.extend(reference["adapter"])
        desiredTableName: str = reference["tableName"]
        if desiredTableName != "":
            sys.stdout.write(f"Using desired table name {desiredTableName}\n")
            self.tableName = desiredTableName
        else:
            sys.stdout.write(f"Using DEFAULT table name {self.tableName}\n")
            
        sys.stdout.write("Dynamic Routing Updater will watch the following:\n")
        for toWatch in self.nics:
            sys.stdout.write(f"\t{toWatch}\n")    
        
        signal.signal(signal.SIGINT, self.__stop)
    
    def getRoutingTable(self) -> List[str]:
        """Read routing table to list
        """
        rt_entries: List[str] = []
        
        with open("/etc/iproute2/rt_tables", "r") as rt_tables:
            for line in rt_tables:
                if len(line.strip("\t\r\n")) > 0:
                    rt_entries.append(line.strip("\n"))
                else:
                    sys.stdout.write("Skipping empty line in rt_tables!\n")
        return rt_entries
    
    def removeDruTableEntries(self) -> None:
        """Removes DRU created routing table entries
        """    
        escapedTableName = re.escape(self.tableName)
        directTable = re.compile(r"[0-9]+\t{}[0-9]+(?!\w)".format(escapedTableName), re.IGNORECASE)
                
        sys.stdout.write("Removing old tables..\n")
        updatedTables: List[str] = []
        for line in self.getRoutingTable():
            if directTable.search(line) == None:
                updatedTables.append(line)
        
        rewrite = open("/etc/iproute2/rt_tables", "w")
        for entry in updatedTables:
            rewrite.write("{}\n".format(entry))
        rewrite.close()
        manager = RoutingManager()
        for net, table in self.configuredTables.items():
            manager.removeInOutRule(net, table)
        
               
    def addDruTableEntries(self) -> None:
        """
        """
        self.removeDruTableEntries()
        acceptableTableIds = list(range(0, 255))
        activeTablesCheck = re.compile(r"^(?!#)[0-9]+")
        for line in self.getRoutingTable():
            activeIds = activeTablesCheck.findall(line)
            if len(activeIds) > 0:
                activeId = int(activeIds[0])
                if (activeId in acceptableTableIds):
                    acceptableTableIds.remove(activeId)
        
        appendableTables: List[str] = []
        for i, adapter in enumerate(self.nics):
            tableId = acceptableTableIds.pop(0)
            ntableName: str = "{}{}".format(self.tableName, i)
            tableEntry: str = "{}\t{}".format(tableId, ntableName)
            appendableTables.append(tableEntry)
            self.configuredTables[adapter] = ntableName
        sys.stdout.write("Creating new tables\n")
        with open("/etc/iproute2/rt_tables", "a") as file:
            for table in appendableTables:
                file.write("{}\n".format(table))
                sys.stdout.write(f"{table}\n")
    
    def setRoutingRules(self) -> None:
        """
        """
        manager = RoutingManager()
        for net, table in self.configuredTables.items():
            manager.setIncomingRule(net, table)
            manager.setOutgoingRule(net, table)
                    
                
    def start(self) -> None:
        """
        """
        sys.stdout.write("Updating and preparing Routing Table entries\n")
        self.addDruTableEntries()
        self.setRoutingRules()
        
        if len(self.nics) == 0 or len(self.configuredTables) == 0:
            sys.stderr.write("Configuration is missing network adapters or configured tables..\n")
            return
        
        sys.stdout.write("Starting DRUHook\n")
        self.dipwa = NetworkHookHandler(self.nics, self.configuredTables)
        self.dipwa.start()
        self.niw = NetworkInfoWatcher(self.configuredTables)
        self.niw.start()
        
    def dryrun(self) -> None:
        """
        """
        
        sys.stdout.write("Starting DRU dryrun\n")
        sys.stdout.write("Updating and preparing Routing Table entries\n")
        self.addDruTableEntries()
        self.setRoutingRules()
    
        
        if len(self.nics) == 0 or len(self.configuredTables) == 0:
            sys.stderr.write("Configuration is missing network adapters or configured tables..\n")
            return
        
        sys.stdout.write("Starting DRUHook\n")
        self.dipwa = NetworkHookHandler(self.nics, self.configuredTables)
        self.dipwa.dryrun()
        sys.stdout.write("\nDRU dryrun ended\n")
        
    def __stop(self, sig, _):
        sys.stdout.write(f"Signal {sig} received. Cleaning up and exiting gracefully...\n")
        self.stop()
        
    def stop(self) -> None:
        self.dipwa.stop()
        self.removeDruTableEntries()
        sys.stdout.write("Stopped DRUHook and removed created Routing Table entries\n")