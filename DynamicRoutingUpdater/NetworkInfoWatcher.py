import logging
import threading
import time, sys
from threading import Thread
from typing import List
from .AddressInfo import AddressInfo
from .Routing import Routing
from .Rules import Rules

class NetworkInfoWatcher:
    """
    """
    
    adapter__rt: dict = {}
    watchers: List[Thread] = []
    
    stopFlag = threading.Event()
    
    
    def __init__(self, adapter__rt: dict) -> None:
        """"""
        self.adapter__rt = adapter__rt
        for name, table in adapter__rt.items():
            self.watchers.append(Thread(target=self.__monitor, kwargs={'name': name, 'table': table}))
        
    def start(self) -> None:
        for thread in self.watchers:
            thread.start()
        
    def stop(self) -> None:
        """
        """
        self.stopFlag.set()
#        for thread in self.watchers:
#            thread.join()
        
    def __monitor(self, name, table) -> None:
        """"""
        ai = AddressInfo(name)
        while not self.stopFlag.is_set():
            sleep_time = 1
            ipInfo = ai.read()
            if ipInfo.valid_life_time_in_sec == None:
                sleep_time = 60
            else:
                sleep_time = ipInfo.valid_life_time_in_sec
            
            try:
                # Waits 30 sec just to prevent conflict if both hook and this runs at the same time
                time.sleep(30)
            except:
                return
            
            # Run check on the routes    
            if (self.__routeValidation(table=table, device=name) == False):
                try:
                    with open("/tmp/dru-hook", 'w') as fifo:
                        fifo.write(name)
                except:
                    logging.error("Failed to adjust routes..")
            
            if (self.__ruleValidation(device=name, table=table) == False):
                Rules().addRule(ipInfo.ip_address, table=table)
            
            try:
                time.sleep(sleep_time)
            except:
                return
    
    def __routeValidation(self, device: str, table: str) -> bool:
        """"""
        addri = AddressInfo(device).read()
        routes = Routing.getRoutes(table=table)
        if (len(routes) < 2):
            return False
        if all(x.preferredSource == addri.ip_address for x in routes) == False:
            return False
        return True
    
    def __ruleValidation(self, device: str, table: str) -> bool:
        """"""
        rules = Rules.getRules(table=table)
        addri = AddressInfo(device).read()
        if (len(rules) == 0):
            return False
        if any(x.source == addri.ip_address for x in rules) == False:
            return False
        return True
        