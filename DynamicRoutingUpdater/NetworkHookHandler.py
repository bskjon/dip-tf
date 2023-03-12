from io import TextIOWrapper
import json
import random
from threading import Thread
import threading
from typing import List
from .objects import NetworkAdapter, RoutingManager
import os, sys, time, re, errno
import netifaces 


class NetworkHookHandler:
    """
    """
    __mainThread = threading.current_thread
    dipwaThread: Thread = None
    pipe_path = "/tmp/dipwa"
    
    stopFlag = threading.Event()
    
    nics: List[str] = []
    nics_rt = {}
        
    def __init__(self, nics: List[str], nics_rt: dict) -> None:
        try:
            if not os.path.exists(self.pipe_path):
                os.mkfifo(path=self.pipe_path)
                os.chmod(self.pipe_path, mode=0o666)
        except OSError as oe:
            if oe.errno != errno.EEXIST:
                raise
        self.nics.extend(nics)
        self.nics_rt = nics_rt
            
    def stdout(self, out:str):
        sys.stdout.write(f"{out}\n")
        sys.stdout.flush()
    def stderr(self, out:str):
        sys.stderr.write(f"{out}\n")
        sys.stderr.flush()
            
    def start(self) -> None:
        """Starts Thread that opens pipe and watches it for changes
        Returns:
            Thread: dipwaThread that has been started
        """
        self.dipwaThread = threading.Thread(target=self.__onThreadStart)
        self.dipwaThread.start()
        
    def dryrun(self) -> None:
        """Runs all operations on defined interfaces
        """
        self.stdout("DIPWA Dryrun started!\n")
        for nic in self.nics:
            self.__processMessage(nic)
        self.stdout("\nDIPWA Dryrun completed!\n")
        
    def stop(self) -> None:
        """
        """
        with open(self.pipe_path, 'w') as fifo:
            fifo.write('stop')
        self.stopFlag.set()
        self.dipwaThread.join()
        
    def __onThreadStart(self) -> None:
        """
        """
        if self.__mainThread == threading.current_thread():
            self.stderr("DIPWA has not been started in a separete thread!")
            raise Exception("DIPWA is started in main thread!")
        self.stdout("DIPWA Thread Started")
        self.__openPipe()
        
    def __openPipe(self) -> None:
        """_summary_
        """
        self.stdout(f"Opening pipe on {self.pipe_path}")
        while not self.stopFlag.is_set():
            with open(self.pipe_path, 'r') as fifo:
                message = fifo.read().strip("\n")
                if message and message in self.nics:
                    self.stdout(f"Received valid message: {message}")
                    self.__processMessage(message)
                elif message == "stop":
                    self.stdout(f"Received fifo stop: {message}")
                else:
                    self.stderr(f"Received invalid message: {message}")
            time.sleep(2.5)
        self.stdout(f"Pipe is closed!")
        
    
    def __processMessage(self, nic: str) -> None:
        if (nic not in netifaces.interfaces()):
            self.stdout(f"Message contains non nic value: {nic}")
            return
        self.stdout(f"Message indicates that there has been changes to nic: {nic}")
        adapter = NetworkAdapter(nic)
        if (adapter.isValid()):
            self.__routingTable_modify(adapter)
        else:
            self.stdout(f"Adding puller on {nic}")
            self.__puller_add(nic)
                
            
    def __routingTable_modify(self, adapter: NetworkAdapter) -> None:
        """_summary_
        """
        nic_rt_table = self.nics_rt[adapter.name]
        self.stdout(f"Modifying routing for {adapter.name} on table {nic_rt_table}")
        
        route_manager = RoutingManager()
        route_manager.flushTable(tableName=nic_rt_table)
        route_manager.deleteRoute(adapter=adapter)
        route_manager.deleteRoute(adapter=adapter, tableName=nic_rt_table)
        

        route_manager.addRoute(adapter=adapter, tableName=nic_rt_table)
        #route_manager.addRule(adapter=adapter, tableName=nic_rt_table)
        
            
    nicsPullerThreads: List[Thread] = []

    def __puller_add(self, nic: str) -> None:
        """Pulls on network adapter in seperate thread
        """
        waitTime: int = 60
        if len(list(filter(lambda x: x.name == nic, self.nicsPullerThreads))) != 0:
            self.stdout(f"Fount existing thread for {nic} skipping..")
            return
        thread = Thread(
            name=nic,
            target=self.__puller_thread,
            args=(nic,waitTime)
        )
        self.nicsPullerThreads.append(thread)
        thread.start()
        
    def __puller_remove(self, name: str) -> None:
        """Removes puller
        """
        targetThread = next(filter(lambda x: x.name == name, self.nicsPullerThreads))
        self.nicsPullerThreads.remove(targetThread)
        
    
    def __puller_thread(self, nic: str, waitTime: int = 60) -> None:
        """Thread for pulling on adapter
        """
        self.stdout(f"Starting pulling on {nic}")
        
        isInInvalidState: bool = True
        while isInInvalidState:
            time.sleep(waitTime)
            adapter = NetworkAdapter(nic)
            isInInvalidState != adapter.isValid()
            if (isInInvalidState == False):
                self.__puller_remove(nic)
                self.__routingTable_modify(adapter)
            else:
                self.stdout(f"Pulling on {nic} in {waitTime}s")
        self.stdout(f"Pulling on {nic} has ended")
        
