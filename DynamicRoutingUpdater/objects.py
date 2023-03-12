import netifaces
from netaddr import IPAddress
from typing import Optional
import sys, os, re, errno, json
from typing import List
import json
import subprocess
from datetime import datetime


class NetworkAdapter:
    name: str = None # Network Adapter name
    ip: str = None
    subnet: str = None
    cidr: str = None
    gateway: str = None
    netmask: str = None # Gateway address but with 0 at the end
    timeOfCreated: str = "Never set!"

    def __init__(self, name) -> None:
        self.name = name
        self.gateway = self.getGateway()
        self.ip = self.getIpAddress()
        self.subnet = self.getSubnet()
        self.cidr = self.getCidr(self.subnet)
        self.netmask = self.getNetmask()
        self.timeOfCreated = datetime.now().strftime("%H:%M:%S %d.%m.%Y")
        

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

    def isValid(self) -> bool:
        """Checks if fields are valid/assigned

        Returns:
            bool: Returns true if all is valid or/and assigned
        """
        if (
            self.ip == None or
            self.subnet == None or
            self.cidr == None or
            self.gateway == None or
            self.netmask == None # Gateway address but with 0 at the end
        ):
            sys.stderr.write("One or more values are invalid..\n")
            sys.stderr.write(f"\t{self}\n")
            return False
        else:
            return True

    def __str__(self):
        return "\n{}\n\t{}\n\t{}\t/{}\n\t{}\n\t{}".format(self.name, self.ip, self.subnet, self.cidr, self.gateway, self.timeOfCreated)


class AddressInfo:
    """_summary_
        ip -4 -j -o addr show internet
    """
    
    interface: str = None
    is_dynamic: bool = False
    valid_life_time_in_sec: int = 0
    ip_address: str = None
    ip_address_prefix: str = None
    
    initial__ip_address: str = None
    initial__valid_life_time_in_sec: int = 0
    initial__ip_address_prefix: str = None
    
    def __init__(self, interface: str) -> None:
        self.interface = interface
        self.reset()

    def __read(self):
        addrinfo = subprocess.getoutput(f"ip -4 -j -o addr show {self.interface}")
        jo = json.loads(addrinfo)
        if len(jo) == 1 and len(jo[0]["addr_info"]) == 1:
            details: dict = jo[0]["addr_info"][0]
            self.is_dynamic = details.get("dynamic")
            self.valid_life_time_in_sec = details.get("valid_life_time")
            self.ip_address = details.get("local")
            self.ip_address_prefix = details.get("prefixlen")
    
    def reset(self) -> None:
        self.__read()
        self.initial__ip_address = self.ip_address
        self.initial__ip_address_prefix = self.ip_address_prefix
        self.initial__valid_life_time_in_sec = self.valid_life_time_in_sec
    
    def ttl_now(self) -> int:
        self.__read()
        return self.valid_life_time_in_sec
    
    def __str__(self):
        return "\tIPv4 => {},\n\t Prefix => {},\n\t isDHCP => {},\n\t TTL => {}\n".format(self.ip_address, self.ip_address_prefix, self.is_dynamic, self.ttl_now())
    
class RouteEntry:
    dst: str = None
    gateway: str = None
    dev: str = None
    prefsrc: str = None
    scope: str = None
    
    def __init__(self, dst: str, gateway: str, dev: str, prefsrc: str, scope: str) -> None:
        self.dst = dst
        self.gateway = gateway
        self.dev = dev
        self.prefsrc = prefsrc
        self.scope = scope
    
    def __str__(self):
        return "\tdst => {},\n\t gateway => {},\n\t dev => {},\n\t prefsrc => {},\n\t scope => {}\n".format(self.dst, self.gateway, self.dev, self.prefsrc, self.scope)


class RouteInfo:
    """"""
    # ip -j route show table direct0
    adapterName: str = None
    tableName: str = None
    routes: List[RouteEntry] = []
    
    def __init__(self, name: str, tableName: str) -> None:
        self.tableName = tableName
        self.adapterName = name
        self.__read()
    
    def __read(self):
        self.routes.clear()
        dump = subprocess.getoutput(f"ip -j route show table {self.tableName}")
        jo = json.loads(dump)
        if len(jo) == 0:
            return
        for item in jo:
            route = RouteEntry(
                dst=getattr(item, "dst", None),
                gateway=getattr(item, "gateway", None),
                dev=getattr(item, "dev", None),
                prefsrc=getattr(item, "prefsrc", None),
                scope=getattr(item, "scope", None)
            )
            self.routes.append(route)
        
        
    def hasValidRoutes(self) -> bool:
        addri = AddressInfo(self.adapterName)
        if len(self.routes) < 2:
            sys.stderr.write("Routes are less than required")
            for route in self.routes:
                sys.stderr.write(route)
            sys.stderr.flush()
            return False
        elif all(x.prefsrc == addri.ip_address for x in self.routes) == False:
            sys.stderr.write("Some route IPs are wrong")

            sys.stderr.flush()
            return False
        
        return True
    
            
#  [{"addr_info":[{"index":4,"dev":"internet","family":"inet","local":"193.69.230.53","prefixlen":21,"metric":100,"broadcast":"193.69.231.255","scope":"global","dynamic":true,"label":"internet","valid_life_time":436,"preferred_life_time":436}]}]

# ip -j route show table direct0
class RoutingManager:
    """
    """
    
    def stdout(self, out:str):
        sys.stdout.write(f"{out}\n")
        sys.stdout.flush()
    def stderr(self, out:str):
        sys.stderr.write(f"{out}\n")
        sys.stderr.flush() 
    
    def setIncomingRule(self, adapterName: str, tableName: str) -> None:
        operations: List[str] = [
            "ip rule add iif {} table {}".format(adapterName, tableName)
        ]
        for operation in operations:
            #proc = subprocess.run([operation], shell=True, check=True, stdout=subprocess.PIPE)
            result = os.system(operation)
            if result != 0:
                self.stderr(f"Failed: {operation}")
            else:
                self.stderr(f"OK: {operation}")
        
    def setOutgoingRule(self, adapterName: str, tableName: str) -> None:
        operations: List[str] = [
            "ip rule add oif {} table {}".format(adapterName, tableName)
        ]
        for operation in operations:
            #proc = subprocess.run([operation], shell=True, check=True, stdout=subprocess.PIPE)
            result = os.system(operation)
            if result != 0:
                self.stderr(f"Failed: {operation}")
            else:
                self.stderr(f"OK: {operation}")
    
    def removeInOutRule(self, adapterName: str, tableName: str) -> None:
        operations: List[str] = [
            "ip rule del iif {} table {}".format(adapterName, tableName),
            "ip rule del oif {} table {}".format(adapterName, tableName)
        ]
        for operation in operations:
            #proc = subprocess.run([operation], shell=True, check=True, stdout=subprocess.PIPE)
            result = os.system(operation)
            if result != 0:
                self.stderr(f"Failed: {operation}")
            else:
                self.stderr(f"OK: {operation}")
    
    
    def addRoute(self, adapter: NetworkAdapter, tableName: str) -> None:
        """_summary_
        """
        self.stdout(f"Adding routes to routing table {tableName}")
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
                self.stderr(f"Failed: {operation}")
            else:
                self.stderr(f"OK: {operation}")
        
    def addRule(self, adapter: NetworkAdapter, tableName: str) -> None:
        """Not needed if you use the iif oif
        """
        self.stdout(f"Adding rules to routing table {tableName}")
        if not tableName:
            raise Exception("Routing table name is not preset")
        operations: List[str] = [
            "ip rule add from {} table {}".format(adapter.ip, tableName),
        ]
        for operation in operations:
            #proc = subprocess.run([operation], shell=True, check=True, stdout=subprocess.PIPE)
            result = os.system(operation)
            if result != 0:
                self.stderr(f"Failed: {operation}")
            else:
                self.stderr(f"OK: {operation}")
    
    def deleteRoute(self, adapter: NetworkAdapter, tableName: str = "main") -> None:
        """Deletes routes on routing table
            If there is a different ruting table than main, you will need to pass it here
            For removing routes on the default table keep "main" or replace it with the correct one
        """
        self.stdout(f"Deleting rules on routing table {tableName}")
        if not tableName:
            raise Exception("Routing table name is not preset")
        operations: List[str] = [
            "ip route del {}/{} dev {} src {} table {}".format(adapter.netmask, adapter.cidr, adapter.name, adapter.ip, tableName),
            "ip route del default via {} dev {} src {} table {}".format(adapter.gateway, adapter.name, adapter.ip, tableName),
            "ip route del {} dev {} src {} table {}".format(adapter.gateway, adapter.name, adapter.ip, tableName)
        ]
        if tableName != "main":
            operations.append("ip route flush table {}".format(tableName))
        
        for operation in operations:
            #proc = subprocess.run([operation], shell=True, check=True, stdout=subprocess.PIPE)
            result = os.system(operation)
            if result != 0:
                self.stderr(f"Failed: {operation}")
            else:
                self.stderr(f"OK: {operation}")
                
    def flushTable(self, tableName: str) -> None:
        """Deletes routes on routing table
            If there is a different ruting table than main, you will need to pass it here
            For removing routes on the default table keep "main" or replace it with the correct one
        """
        self.stdout(f"Flushing routing table {tableName}")
        if not tableName:
            raise Exception("Routing table name is not preset")
        operations: List[str] = [
            "ip route flush table {}".format(tableName)
        ]
        
        for operation in operations:
            #proc = subprocess.run([operation], shell=True, check=True, stdout=subprocess.PIPE)
            result = os.system(operation)
            if result != 0:
                self.stderr(f"Failed: {operation}")
            else:
                self.stderr(f"OK: {operation}")         
