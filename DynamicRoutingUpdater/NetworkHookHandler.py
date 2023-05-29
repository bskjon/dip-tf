from io import TextIOWrapper
import json, random
from threading import Thread
import threading
import traceback
import queue, select
from typing import List
import os, sys, time, re, errno
import netifaces 
from .objects import IpData
from .Routing import Routing
from .Rules import Rules
from .NetworkAdapter import NetworkAdapter


class NetworkHookHandler:
    """
    """
    __mainThread = threading.current_thread
    
    # Create a queue to hold messages received from the pipe
    message_queue = queue.Queue()

    # Create a mutex to coordinate access to the queue
    message_mutex = threading.Lock()
    
    # Create a condition variable to notify waiting threads of new messages
    message_cond = threading.Condition(message_mutex)
    
    
    hookThreads: List[Thread] = []
    pipe_path = "/tmp/dru-hook"
    
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
            
            
    def __openPipe(self) -> None:
        """_summary_
        """
        self.stdout(f"Opening pipe on {self.pipe_path}")
        
        epoll = select.epoll()
        pipe_fd = os.open(self.pipe_path, os.O_RDONLY | os.O_NONBLOCK)
        epoll.register(pipe_fd, select.EPOLLIN)
        
        try:
            while not self.stopFlag.is_set():
                events = epoll.poll()
                for fileno, event in events:
                    if fileno == pipe_fd and event & select.EPOLLIN:
                        try:
                            message = os.read(pipe_fd, 1024).strip().decode()
                            if message in self.nics:
                                self.stdout(f"DRUHook Received message from hook: {message}")
                                with self.message_mutex:
                                    self.message_queue.put(message)
                                    self.message_cond.notify_all()
                            elif message == "stop":
                                self.stdout(f"DRUHook Received stop: {message}")
                                self.stopFlag.set()
                            else:
                                if len(message) > 0:
                                    self.stderr(f"DRUHook is ignoring: {message} as it expects one of your predefined values or stop")
                            pass
                        except OSError as e:
                            if e.errno == errno.EAGAIN or e.errno == errno.EWOULDBLOCK:
                                # Ingen data tilgjengelig på røret for øyeblikket
                                pass
                            else:
                                # Annet OSError
                                self.stderr(f"Error reading from pipe: {e}")
                                self.stopFlag.set()
            pass
        finally:
            epoll.unregister(self.pipe_fd)
            epoll.close()
        self.stdout(f"Pipe is closed!")
        
            
    def start(self) -> None:
        """Starts Thread that opens pipe and watches it for changes
        Returns:
            Thread: DruHookThread that has been started
        """
        _pthread = threading.Thread(target=self.__openPipe)
        self.hookThreads.append(_pthread)
        _pthread.start()
        for nic in self.nics:
            _hthread = threading.Thread(target=self.__onThreadStart, kwargs={'targetName': nic})
            self.hookThreads.append(_hthread)
            _hthread.start()
    
        
    def dryrun(self) -> None:
        """Runs all operations on defined interfaces
        """
        self.stdout("DRUHook Dryrun started!\n")
        for nic in self.nics:
            self.__processMessage(nic)
        self.stdout("\DRUHook Dryrun completed!\n")
        
    def stop(self) -> None:
        """
        """
        with open(self.pipe_path, 'w') as fifo:
            fifo.write('stop')
        self.stopFlag.set()
        for thread in self.hookThreads:
            thread.join()
        
    def __onThreadStart(self, targetName: str) -> None:
        """
        """
        if self.__mainThread == threading.current_thread():
            self.stderr("DRUHook has not been started in a separete thread!")
            raise Exception("DRUHook is started in main thread!")
        self.stdout(f"DRUHook Thread Started for {targetName}")
        
        while not self.stopFlag.is_set():
            with self.message_mutex:
                if self.message_queue.empty():
                    timeout = random.uniform(1, 5)
                    self.message_cond.wait(timeout)
                    continue                   
                    
                message = self.message_queue.get()
                if message == targetName:
                    self.stdout(f"DRUHook Thread for {targetName} has received event")
                    self.__processMessage(message)
                else:
                    self.message_queue.put(message)
                
                 
    
    def __processMessage(self, nic: str) -> None:
        adapter = NetworkAdapter(nic)
        if (adapter.getIpData().isValid()):
            self.__routingTable_modify(adapter)
        else:
            self.stdout(f"Adding puller on {nic}")
            self.__puller_add(nic)
                
            
    def __routingTable_modify(self, adapter: NetworkAdapter) -> None:
        """_summary_
        """
        nic_rt_table = self.nics_rt[adapter.name]
        self.stdout(f"Modifying routing for {adapter.name} on table {nic_rt_table}")
        
        Routing.flushRoutes(table=nic_rt_table) 
        Rules().flushRules(table=nic_rt_table)
        
        try:
            ipData = adapter.getIpData()
            Routing("main").deleteRoutes(ipData=ipData)
            
            
            rt = Routing(nic_rt_table)
            rt.deleteRoutes(ipData=ipData)
            rt.addRoutes(ipData=ipData)
            
            Rules().addRule(table=nic_rt_table, source=ipData.ip)
        except Exception as e:
            traceback.print_exc()
        
            
    nicsPullerThreads: List[Thread] = []

    def __puller_add(self, nic: str) -> None:
        """Pulls on network adapter in seperate thread
        """
        waitTime: int = 60
        if len(list(filter(lambda x: x.name == nic, self.nicsPullerThreads))) != 0:
            self.stdout(f"Found existing thread for {nic} skipping..")
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
            adapter = NetworkAdapter(nic).getIpData()
            isInInvalidState = not adapter.isValid()
            print(adapter)
            if (isInInvalidState == False):
                self.__puller_remove(nic)
                self.__routingTable_modify(adapter)
            else:
                self.stdout(f"Pulling on {nic} in {waitTime}s")
        self.stdout(f"Pulling on {nic} has ended")
        
