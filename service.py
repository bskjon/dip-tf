from distutils.log import debug
from io import TextIOWrapper
from itertools import count
import random
from threading import Thread
import json
import os, sys, time, re

import errno
from unicodedata import name
import netifaces
from typing import List, Optional
from threading import Thread
from netaddr import IPAddress
from termcolor import colored as tcolor
import datetime

# import subprocess

#https://stackoverflow.com/questions/28813210/send-message-to-a-python-script

debug: bool=False

class Printy:
    @staticmethod
    def getTimeAndDate():
        now = datetime.datetime.now()
        return now.strftime("%d.%m.%Y %H:%M:%S")

    @staticmethod
    def info(values):
        sys.stdout.write("{}".format(values))
        sys.stdout.write("\n")
        
    @staticmethod
    def success(values):
        sys.stdout.write(tcolor("SUCCESS\t {}".format(values), "green"))
        sys.stdout.write("\n")

    @staticmethod
    def warn(values):
        sys.stdout.write(tcolor("WARN\t {}".format(values), "yellow"))
        sys.stdout.write("\n")
    
    @staticmethod
    def debug(values):
        if (debug == True):
            sys.stdout.write(tcolor("DEBUG\t {}".format(values), "blue"))
            sys.stdout.write("\n")

    @staticmethod
    def error(values):
        sys.stderr.write(tcolor("ERROR\t {}".format(values), "red"))
        sys.stdout.write("\n")
        
def flipper() -> str:
    faces: List[str] = [
        "(╯°□°）╯︵ ┻━┻",
        "(┛◉Д◉)┛彡┻━┻",
        "(ノಠ益ಠ)ノ彡┻━┻",
        
        "(ノ｀´)ノ ~┻━┻",
        "┻━┻ ︵ヽ(`Д´)ﾉ︵ ┻━┻"
    ]
    return random.choice(faces)

class networkAdapter:
    name: str = None # Network Adapter name
    ip: str = None
    subnet: str = None
    cidr: str = None
    gateway: str = None
    netmask: str = None # Gateway address but with 0 at the end

    def __init__(self, name) -> None:
        self.name = name
        self.gateway = self.getGateway()
        self.ip = self.getIpAddress()
        self.subnet = self.getSubnet()
        self.cidr = self.getCidr(self.subnet)
        self.netmask = self.getNetmask()

    def getGateway(self) -> Optional[str]:
        gws = netifaces.gateways()
        for gw in gws:
            try:
                gwstr: str = str(gw)
                if 'default' in gwstr:
                    continue
                entries = gws[gw]
                for entry in entries:
                    if self.name in entry[1]:
                        return entry[0]
            except:
                print("Exception")
                pass
        return None
    
    def getNetmask(self) -> Optional[str]:
        try:
            gw = self.getGateway()
            netmask = gw[:gw.rfind(".")+1]+"0"
            return netmask
        except:
            print("Exception")
            pass
        return None

    def getIpAddress(self) -> Optional[str]:
        try:
            iface = netifaces.ifaddresses(self.name)
            entry = iface[netifaces.AF_INET][0]
            return entry["addr"]
        except:
            pass
        return None

    def getSubnet(self) -> Optional[str]:
        try:
            iface = netifaces.ifaddresses(self.name)
            entry = iface[netifaces.AF_INET][0]
            return entry["netmask"]
        except:
            pass
        return None

    def getCidr(self, subnet: str) -> Optional[str]:
        try:
            return IPAddress(subnet).netmask_bits()
        except:
            pass
        return None

    def __str__(self):
        return "\n{}\n\t{}\n\t{}\t/{}\n\t{}".format(self.name, self.ip, self.subnet, self.cidr, self.gateway)


class service:
    configuredTables = {}
    __defaultTableName = "direct"


    pipe_path = "/tmp/dipwa"
    watchable: List[str] = []

    threads: List[Thread] = []
    
    def __init__(self) -> None:
        print("Loading...")
        reference = json.load(open('reference.json'))
        self.watchable.extend(reference["adapter"])
        self.__defaultTableName = reference["tableName"]
        print("Watching",self.watchable)

        try:
            if not os.path.exists(self.pipe_path):
                os.mkfifo(path=self.pipe_path)
                os.chmod(self.pipe_path, mode=0o666)
        except OSError as oe:
            if oe.errno != errno.EEXIST:
                raise
        self.setup(self.watchable)
        self.run()
    
    def setup(self, adapters) -> None:

        tableIds = list(range(0, 255))
        writableTables: List[str] = []


        print("Setting up..")
        activeTables = re.compile(r"^(?!#)[0-9]+")
        directTable = re.compile(r"(?!<=[0-9]+)\s+direct[0-9]+", re.IGNORECASE)
        current_tables: TextIOWrapper = open("/etc/iproute2/rt_tables", "r")
        for i, line in enumerate(current_tables):
            if directTable.search(line) == None:
                writableTables.append(line.strip("\n"))
                getActiveId = activeTables.findall(line)
                if len(getActiveId) > 0:
                    activeId = int(getActiveId[0])
                    if activeId in tableIds:
                        tableIds.remove(activeId)
                        
        current_tables.close()

        for i, adapter in enumerate(adapters):
            tableId = tableIds.pop(0)
            ntableName: str = "{}{}".format(self.__defaultTableName, i)
            tableEntry: str = "{}\t{}".format(tableId, ntableName)
            writableTables.append(tableEntry)
            self.configuredTables[adapter] = ntableName
        
        print(writableTables)
        

        rewrite = open("/etc/iproute2/rt_tables", "w")
        for entry in writableTables:
            rewrite.write("{}\n".format(entry))
        rewrite.close()

        print("Updated ip route table")
        current_tables = open("/etc/iproute2/rt_tables", "r")
        for line in current_tables:
            print(line)
        current_tables.close()
        


            


    def run(self) -> None:
        
        # Run before waiting
        for adapter in self.watchable:
            self.analyzer(adapter)

        while True:
            with open(self.pipe_path, 'r') as fifo:
                message = fifo.read().strip("\n")
                
                if message and message in self.watchable:
                    Printy.info("Valid {}".format(message))
                    self.analyzer(message)
                else:
                    Printy.info("Not valid..")
            time.sleep(1)
                # spawn a new thread with message

    def analyzer(self, interface: str) -> None:
        Printy.info("Looking into {}".format(interface))
        adapters = netifaces.interfaces()
        if (interface in adapters):
            Printy.info("Changes to {} detected!".format(interface))
            adapter = networkAdapter(interface)
            if (self.hasValidEntries(adapter=adapter)):
                self.modify(adapter=adapter)
            else:
                print(interface, "invalid or incomplete values found, starting pulling for interface")
                self.addUnavailablePuller(interface=interface)
        else:
            Printy.info("\033[93m Unrecognized data passed: {}".format(interface))
            return

    def hasValidEntries(self, adapter: networkAdapter) -> bool:
        if (
            adapter.ip == None or
            adapter.subnet == None or
            adapter.cidr == None or
            adapter.gateway == None or
            adapter.netmask == None # Gateway address but with 0 at the end
        ):
            print("One or more values are invalid..")
            print(adapter)
            return False
        else:
            return True


    pullingThread: List[Thread] = []
    def addUnavailablePuller(self, interface: str) -> None:
        if len(list(filter(lambda x: x.name == interface, self.pullingThread))) != 0:
            return
        thread = Thread(
            name=interface,
            target=self.availabilityPuller,
            args=(interface)
        )
        self.pullingThread.append(thread)
        thread.start
            
    def availabilityPuller(self, interface: str):
        delayTime: int = 60
        Printy.info("Pulling availability on {}".format(interface))
        time.sleep(delayTime)
        interfaceAdapter = networkAdapter(interface)
        while(self.hasValidEntries(interfaceAdapter) == False):
            Printy.info("{} still has invalid values. Waiting another {}seconds".format(interface, delayTime))
            time.sleep(delayTime)
        Printy.info("{} has valid values, returning to normal flow".format(interface))
        thisThread = filter(lambda x: x.name == interface, self.pullingThread)
        if thisThread in self.pullingThread:
            self.pullingThread.remove(thisThread)
        self.analyzer(interface=interface)
            


    def modify(self, adapter: networkAdapter) -> None:
        print("Modifing routing for", adapter.name)

        deviceTable = self.configuredTables[adapter.name]
        if deviceTable == None:
            print("Failed to obtain route table for device {}".format(adapter.name))

        print(flipper())
        
        self.deleteRoute(adapter=adapter, table=deviceTable)
        self.addRoute(adapter=adapter, table=deviceTable)
        self.addRule(adapter=adapter, table=deviceTable)

    def addRoute(self, adapter:networkAdapter, table: str = None) -> None:
        Printy.info("Adding Routes")
        if table == None:
            return
        operations: List[str] = [
            "ip route add {}/{} dev {} src {} table {}".format(adapter.netmask, adapter.cidr, adapter.name, adapter.ip, table),
            "ip route add default via {} dev {} src {} table {}".format(adapter.gateway, adapter.name, adapter.ip, table),
            "ip route add {} dev {} src {} table {}".format(adapter.gateway, adapter.name, adapter.ip, table)
        ]

        for operation in operations:
            #proc = subprocess.run([operation], shell=True, check=True, stdout=subprocess.PIPE)
            result = os.system(operation)
            if result != 0:
                Printy.info("{} [Failed]\t{}".format("\033[91m", operation))
            else:
                Printy.info("{} [Success]\t{}".format("\033[92m", operation))

    def addRule(self, adapter: networkAdapter, table: str = None) -> None:
        Printy.info("Adding Rule")
        if table == None:
            return
        operations: List[str] = [
            "ip rule add from {} table {}".format(adapter.ip, table),
        ]
        for operation in operations:
            #proc = subprocess.run([operation], shell=True, check=True, stdout=subprocess.PIPE)
            result = os.system(operation)
            if result != 0:
                Printy.info("{} [Failed]\t{}".format("\033[91m", operation))
            else:
                Printy.info("{} [Success]\t{}".format("\033[92m", operation))

    def deleteRoute(self, adapter: networkAdapter, table: str = None) -> None:
        Printy.info("Removing Routes")
        if table == None:
            return
        defaultTable = 'main'
        operations: List[str] = [
            "ip route del {}/{} dev {} src {} table {}".format(adapter.netmask, adapter.cidr, adapter.name, adapter.ip, defaultTable),
            "ip route del default via {} dev {} src {} table {}".format(adapter.gateway, adapter.name, adapter.ip, defaultTable),
            "ip route del {} dev {} src {} table {}".format(adapter.gateway, adapter.name, adapter.ip, defaultTable),
            "ip route flush table {}".format(table)
        ]
        
        for operation in operations:
            #proc = subprocess.run([operation], shell=True, check=True, stdout=subprocess.PIPE)
            result = os.system(operation)
            if result != 0:
                Printy.info("{} [Failed]\t{}".format("\033[91m", operation))
            else:
                Printy.info("{} [Success]\t{}".format("\033[92m", operation))

if (__name__ == "__main__"):
    #networkAdapter("internet").print()
    #networkAdapter("enp6s0").print()
    srv = service()