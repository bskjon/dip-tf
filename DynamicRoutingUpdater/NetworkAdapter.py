import netifaces
from netaddr import IPAddress
from typing import Optional
from datetime import datetime
from .objects import IpData

class NetworkAdapter:
    name: str = None # Network Adapter name

    def __init__(self, name) -> None:
        self.name = name
    
    def getIpData(self) -> IpData:
        return IpData(
            self.name,
            self.getGateway(),
            self.getIpAddress(),
            self.getSubnet(),
            self.getCidr(self.subnet),
            self.getNetmask()
        )
        

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

   