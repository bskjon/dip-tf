import threading
import time, sys
from threading import Thread
from typing import List

from .objects import AddressInfo, NetworkAdapter, RouteInfo, RoutingManager


class NetworkInfoWatcher:
    """
    """
    
    def stdout(self, out:str):
        sys.stdout.write(f"{out}\n")
        sys.stdout.flush()
    def stderr(self, out:str):
        sys.stderr.write(f"{out}\n")
        sys.stderr.flush()
    
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
            sleep_time = 0
            if ai.valid_life_time_in_sec == None:
                sleep_time = 60
            else:
                sleep_time = ai.valid_life_time_in_sec
            
            try:
                # Waits 30 sec just to prevent conflict if both hook and this runs at the same time
                time.sleep(30)
            except:
                return
            
            # Run check on the routes    
            routeInfo = RouteInfo(name, table)
            if (routeInfo.hasValidRoutes() == False):
                try:
                    with open("/tmp/dipwa", 'w') as fifo:
                        fifo.write(name)
                except:
                    self.stderr("Failed to adjust routes..")
            
            try:
                time.sleep(sleep_time)
            except:
                return
            