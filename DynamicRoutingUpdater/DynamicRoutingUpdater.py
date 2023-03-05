from io import TextIOWrapper
import json
import random
from threading import Thread
import threading
from typing import List
from .objects import NetworkAdapter
import os, sys, time, re, errno
import netifaces 
       

class __DynamicIpWatcherAction:
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
            
    def start(self) -> Thread:
        """Starts Thread that opens pipe and watches it for changes
        Returns:
            Thread: dipwaThread that has been started
        """
        self.dipwaThread = threading.Thread(target=self.__onThreadStart())
        self.dipwaThread.start()
        
    def stop(self) -> None:
        """
        """
        self.stopFlag.set()
        self.dipwaThread.join()
        
    def __onThreadStart(self) -> None:
        """
        """
        if self.__mainThread == threading.current_thread():
            sys.stderr.write("DIPWA has not been started in a separete thread!\n")
            raise Exception("DIPWA is started in main thread!")
        sys.stdout.write("DIPWA Thread Started\n")
        self.__openPipe()
        
    def __openPipe(self) -> None:
        """_summary_
        """
        sys.stdout.write(f"Opening pipe on {self.pipe_path}")
        while not self.stopFlag.is_set():
            with open(self.pipe_path, 'r') as fifo:
                message = fifo.read().strip("\n")
                if message and message in self.nics:
                    sys.stdout.write(f"Recieved valid message: {message}\n")
                    self.__processMessage(message)
                else:
                    sys.stderr.write(f"Recieved invalid message: {message}\n")
            time.sleep(2.5)
    
    def __processMessage(self, nic: str) -> None:
        if (nic not in netifaces.interfaces()):
            sys.stdout.write(f"Message contains non nic value: {nic}\n")
            return
        sys.stdout.write(f"Message indicates that there has been changes to nic: {nic}\n")
        adapter = NetworkAdapter(nic)
        if (adapter.isValid()):
            self.__routingTable_modify(adapter)
        else:
            sys.stdout.write(f"Adding puller on {nic}")
            self.__puller_add(nic)
                
            
    def __routingTable_modify(self, adapter: NetworkAdapter) -> None:
        """_summary_
        """
        nic_rt_table = self.nics_rt[adapter.name]
        sys.stdout.write(f"Modifying routing for {adapter.name} on table {nic_rt_table}")
        
        self.__routingTable_deleteRoute(adapter=adapter)
        self.__routingTable_deleteRoute(adapter=adapter, tableName=nic_rt_table)
        self.__routingTable_addRoute(adapter=adapter, tableName=nic_rt_table)
        self.__routingTable_addRule(adapter=adapter, tableName=nic_rt_table)
        
        
    def __routingTable_addRoute(self, adapter: NetworkAdapter, tableName: str) -> None:
        """_summary_
        """
        sys.stdout.write(f"Adding routes to routing table {tableName}")
        if not tableName:
            raise Exception("Routing table name is not preset")
        operations: List[str] = [
            "ip route add {}/{} dev {} src {} table {}".format(adapter.netmask, adapter.cidr, adapter.name, adapter.ip, tableName),
            "ip route add default via {} dev {} src {} table {}".format(adapter.gateway, adapter.name, adapter.ip, tableName),
            "ip route add {} dev {} src {} table {}".format(adapter.gateway, adapter.name, adapter.ip, tableName)
        ]
        for operation in operations:
            #proc = subprocess.run([operation], shell=True, check=True, stdout=subprocess.PIPE)
            result = os.system(operation)
            if result != 0:
                sys.stderr.write(f"Failed: {operation}\n")
            else:
                sys.stderr.write(f"OK: {operation}\n")
        
    def __routingTable_addRule(self, adapter: NetworkAdapter, tableName: str) -> None:
        """
        """
        sys.stdout.write(f"Adding rules to routing table {tableName}")
        if not tableName:
            raise Exception("Routing table name is not preset")
        operations: List[str] = [
            "ip rule add from {} table {}".format(adapter.ip, tableName),
        ]
        for operation in operations:
            #proc = subprocess.run([operation], shell=True, check=True, stdout=subprocess.PIPE)
            result = os.system(operation)
            if result != 0:
                sys.stderr.write(f"Failed: {operation}\n")
            else:
                sys.stderr.write(f"OK: {operation}\n")
    
    def __routingTable_deleteRoute(self, adapter: NetworkAdapter, tableName: str = "main") -> None:
        """Deletes routes on routing table
            If there is a different ruting table than main, you will need to pass it here
            For removing routes on the default table keep "main" or replace it with the correct one
        """
        sys.stdout.write(f"Deleting rules on routing table {tableName}")
        if not tableName:
            raise Exception("Routing table name is not preset")
        operations: List[str] = [
            "ip route del {}/{} dev {} src {} table {}".format(adapter.netmask, adapter.cidr, adapter.name, adapter.ip, tableName),
            "ip route del default via {} dev {} src {} table {}".format(adapter.gateway, adapter.name, adapter.ip, tableName),
            "ip route del {} dev {} src {} table {}".format(adapter.gateway, adapter.name, adapter.ip, tableName),
            "ip route flush table {}".format(tableName)
        ]
        for operation in operations:
            #proc = subprocess.run([operation], shell=True, check=True, stdout=subprocess.PIPE)
            result = os.system(operation)
            if result != 0:
                sys.stderr.write(f"Failed: {operation}\n")
            else:
                sys.stderr.write(f"OK: {operation}\n")
    
    nicsPullerThreads: List[Thread] = []

    def __puller_add(self, nic: str) -> None:
        """Pulls on network adapter in seperate thread
        """
        waitTime: int = 60
        if len(list(filter(lambda x: x.name == nic, self.nicsPullerThreads))) != 0:
            print(f"Fount existing thread for {nic} skipping..\n")
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
        sys.stdout.write(f"Starting pulling on {nic}\n")
        
        isInInvalidState: bool = True
        while isInInvalidState:
            time.sleep(waitTime)
            adapter = NetworkAdapter(nic)
            isInInvalidState != adapter.isValid()
            if (isInInvalidState == False):
                self.__puller_remove(nic)
                self.__routingTable_modify(adapter)
            else:
                sys.stdout.write(f"Pulling on {nic} in {waitTime}s")
        sys.stdout.write(f"Pulling on {nic} has ended")
        

class DynamicRoutingUpdater:
    """DynamicRoutingUpdater, modify routing table
    """
    dipwa: __DynamicIpWatcherAction = None
    
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
    
    def __init__(self) -> None:
        """
        """
        sys.stdout.write(f"{self.flipper()}\n")
        sys.stdout.write("Loading up Dynamic Routing Updater\n")
        sys.stdout.write("Reading configuration\n")
        reference = json.load(open("reference.json"))
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
    
    def getRoutingTable(self) -> List[str]:
        """Read routing table to list
        """
        rt_entries: List[str] = []
        rt: TextIOWrapper = open("/etc/iproute2/rt_tables", "r")
        for i, line in enumerate(rt):
            rt_entries.append(line)
        rt.close()
        return rt_entries
    
    def removeDruTableEntries(self) -> None:
        """Removes DRU created routing table entries
        """    
        escapedTableName = re.escape(self.tableName)
        directTable = re.compile(r"(?<!\d)\s+{}[0-9]+(?!\w)".format(escapedTableName), re.IGNORECASE)
                
        sys.stdout.write("Removing old tables..\n")
        updatedTables: List[str] = []
        for line in self.getRoutingTable():
            if directTable.search(line) == None:
                updatedTables.append(line)
        
        rewrite = open("/etc/iproute2/rt_tables", "w")
        for entry in updatedTables:
            rewrite.write("{}\n".format(entry))
        rewrite.close()
               
    def addDruTableEntries(self) -> None:
        """
        """
        self.removeDruTableEntries()
        acceptableTableIds = list(range(0, 255))
        activeTablesCheck = re.compile(r"^(?!#)[0-9]+")
        for i, line in self.getRoutingTable():
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
                
    def start(self) -> None:
        """
        """
        if len(self.nics) == 0 or len(self.configuredTables) == 0:
            sys.stderr.write("Configuration is missing network adapters or configured tables..\n")
            return
        
        sys.stdout.write("Updating and preparing Routing Table entries\n")
        self.addDruTableEntries()
        
        sys.stdout.write("Starting DIPWA\n")
        self.dipwa = __DynamicIpWatcherAction(self.nics, self.configuredTables)
        self.dipwa.start()
        
    def stop(self) -> None:
        self.dipwa.stop()
        self.removeDruTableEntries()
        sys.stdout.write("Stopped DIPWA and removed created Routing Table entries\n")