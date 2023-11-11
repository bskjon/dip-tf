import logging
from io import TextIOWrapper
import json
import random
import signal
from threading import Thread
from .version import __version__

from typing import List

from .RoutingTable import RoutingTable
from .Routing import Routing
from .Rules import Rules

from .NetworkHookHandler import NetworkHookHandler
from .NetworkInfoWatcher import NetworkInfoWatcher
from .RouteAndRuleObserver import RouteAndRuleObserverManager
import os, sys, time, re, errno
import netifaces

logging.basicConfig(level=logging.INFO)
       

class DynamicRoutingUpdater:
    """DynamicRoutingUpdater, modify routing table
    """
    dipwa: NetworkHookHandler = None
    niw: NetworkInfoWatcher = None
    rrm_observer: RouteAndRuleObserverManager = None
    
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
        logging.info(f"Version: {__version__}")
        logging.info("Loading up Dynamic Routing Updater")
        logging.info("Reading configuration")
        reference = json.load(open(reference))
        self.nics.extend(reference["adapter"])
        desiredTableName: str = reference["tableName"]
        if desiredTableName != "":
            logging.info(f"Using desired table name {desiredTableName}")
            self.tableName = desiredTableName
        else:
            logging.info(f"Using DEFAULT table name {self.tableName}")
            
        logging.info("Dynamic Routing Updater will watch the following:")
        for toWatch in self.nics:
            logging.info(f"\t{toWatch}")    
        
        signal.signal(signal.SIGINT, self.__stop)
    
    def setup(self) -> None:
        """_summary_
        """
        availableNetworkAdapters = netifaces.interfaces()
        logging.info("Running pre-check")
        if set(self.nics).issubset(set(availableNetworkAdapters)):
            logging.info("Configured interfaces are present!")
        else:
            logging.error("Configured interfaces are not present!")
            missingNetworkAdapters = [verdi for verdi in self.nics if verdi not in availableNetworkAdapters]
            for missing in missingNetworkAdapters:
                logging.error(f"\t{missing}")
            logging.warn("Verify that your configuration corresponds to your available network adapters")
            exit(1)
        
        
        rt = RoutingTable(self.tableName, self.nics)
#        rt.deleteMyEntries()
        self.configuredTables = rt.addMyEntries()
        
        for device, table in self.configuredTables.items():
            Routing.addRoute_Default(device=device, table=table)
        logging.info("Setup completed")
                
    def start(self) -> None:
        """
        """
        logging.info("Updating and preparing Routing Table entries")
        self.setup()
        
        if len(self.nics) == 0 or len(self.configuredTables) == 0:
            logging.error("Configuration is missing network adapters or configured tables..")
            return
        
        for device, table in self.configuredTables.items():
            Routing.flushRoutes(table)
        
        logging.info("Starting DRUHook")
        self.dipwa = NetworkHookHandler(self.nics, self.configuredTables)
        self.dipwa.start()
        self.niw = NetworkInfoWatcher(self.configuredTables)
        self.rrm_observer = RouteAndRuleObserverManager(self.configuredTables)
        try:
            for nic in self.nics:
                with open("/tmp/dru-hook", 'w') as fifo:
                    fifo.write(nic)
                time.sleep(10)
        except:
            logging.error("Failed to adjust routes..")
        
        #self.niw.start()
        self.rrm_observer.execute()
        
        
    def dryrun(self) -> None:
        """
        """
        
        logging.info("Starting DRU dryrun")
        logging.info("Updating and preparing Routing Table entries")
        self.setup()
    
        
        if len(self.nics) == 0 or len(self.configuredTables) == 0:
            logging.error("Configuration is missing network adapters or configured tables..")
            return
        
        logging.info("Starting DRUHook\n")
        self.dipwa = NetworkHookHandler(self.nics, self.configuredTables)
        self.dipwa.dryrun()
        logging.info("\nDRU dryrun ended\n")
        
    def __stop(self, sig, _):
        logging.info(f"Signal {sig} received. Cleaning up and exiting gracefully...")
        self.stop()
        
    def stop(self) -> None:
        self.dipwa.stop()
        RoutingTable(self.tableName, self.nics).deleteMyEntries()
        for device, table in self.configuredTables.items():
            Routing.flushRoutes(table=table)
            Rules.flushRules(device=device, table=table)
        logging.info("Stopped DRUHook and removed created Routing Table entries")
