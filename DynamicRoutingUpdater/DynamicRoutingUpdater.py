from io import TextIOWrapper
import json
import random
import signal
from threading import Thread
import threading
from typing import List

from .RoutingTable import RoutingTable
from .Routing import Routing

from .NetworkHookHandler import NetworkHookHandler
from .NetworkInfoWatcher import NetworkInfoWatcher
import os, sys, time, re, errno
import netifaces
       

class DynamicRoutingUpdater:
    """DynamicRoutingUpdater, modify routing table
    """
    dipwa: NetworkHookHandler = None
    niw: NetworkInfoWatcher = None
    
    configuredTables: dict = {}
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
    
    def setup(self) -> None:
        """_summary_
        """
        availableNetworkAdapters = netifaces.interfaces()
        sys.stdout.write("[INFO]: Running pre-check")
        if set(self.nics).issubset(set(availableNetworkAdapters)):
            sys.stdout.write("[OK]: Configured interfaces are present!")
        else:
            sys.stderr.write("[ERROR]: Configured interfaces are not present!")
            missingNetworkAdapters = [verdi for verdi in self.nics if verdi not in availableNetworkAdapters]
            for missing in missingNetworkAdapters:
                sys.stderr.write(f"\t{missing}")
            sys.stdout.write("[SUGGESTION]: Verify that your configuration corresponds to your available network adapters")
            exit(1)
        
        
        rt = RoutingTable(self.tableName, self.nics)
        rt.deleteMyEntries()
        self.configuredTables = rt.addMyEntries()
        
        for device, table in self.configuredTables.items():
            Routing.addRoute_Default(device=device, table=table)
        sys.stdout.write("Setup completed")
                
    def start(self) -> None:
        """
        """
        sys.stdout.write("Updating and preparing Routing Table entries\n")
        self.setup()
        
        if len(self.nics) == 0 or len(self.configuredTables) == 0:
            sys.stderr.write("Configuration is missing network adapters or configured tables..\n")
            return
        
        for nic_table in self.configuredTables.items():
            Routing.flushRoutes(nic_table)
        
        sys.stdout.write("Starting DRUHook\n")
        self.dipwa = NetworkHookHandler(self.nics, self.configuredTables)
        self.dipwa.start()
        self.niw = NetworkInfoWatcher(self.configuredTables)
        try:
            for nic in self.nics:
                with open("/tmp/dru-hook", 'w') as fifo:
                    fifo.write(nic)
                time.sleep(10)
        except:
            sys.stderr("[ERROR]: Failed to adjust routes..")
        
        self.niw.start()
        
        
    def dryrun(self) -> None:
        """
        """
        
        sys.stdout.write("Starting DRU dryrun\n")
        sys.stdout.write("Updating and preparing Routing Table entries\n")
        self.setup()
    
        
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
        RoutingTable(self.tableName, self.nics).deleteMyEntries()
        sys.stdout.write("Stopped DRUHook and removed created Routing Table entries\n")