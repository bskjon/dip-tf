import netifaces
from netaddr import IPAddress
from typing import Optional
import sys


class NetworkAdapter:
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
        return "\n{}\n\t{}\n\t{}\t/{}\n\t{}".format(self.name, self.ip, self.subnet, self.cidr, self.gateway)
