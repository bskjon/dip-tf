import netifaces
from netaddr import IPAddress
from typing import Optional
from datetime import datetime
from .objects import IpData

def stdout(out:str):
    sys.stdout.write(f"{out}\n")
    sys.stdout.flush()
    
def stderr(out:str):
    sys.stderr.write(f"{out}\n")
    sys.stderr.flush() 


class NetworkAdapter:
    name: str = None # Network Adapter name

    def __init__(self, name) -> None:
        self.name = name
    
    def getIpData(self) -> IpData:
        gateway = self.getGateway()
        ipAddress = self.getIpAddress()
        subnet = self.getSubnet()
        cidr = self.getCidr(subnet)
        netmask = self.getNetmask()
        return IpData(
            name=self.name,
            gateway=gateway,
            ip=ipAddress,
            subnet=subnet,
            cidr=cidr,
            netmask=netmask
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
                stderr(f"[ERROR]: getGateway => {gw}")
                pass
        return None
    
    def getNetmask(self) -> Optional[str]:
        gw = self.getGateway()
        try:
            netmask = gw[:gw.rfind(".")+1]+"0"
            return netmask
        except:
            stderr(f"[ERROR]: getNetmask => {gw}")
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

   