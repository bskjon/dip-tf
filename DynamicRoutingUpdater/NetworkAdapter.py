import logging
import re
import netifaces
from netaddr import IPAddress
from typing import Optional
from .objects import IpData, Netstated
import subprocess

logging.basicConfig(level=logging.INFO)

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
                logging.error(f"getGateway => {gw}")
                pass
        # If this is hit, then it could not find the gateway using traditional means
        netst = self.parseNetstat(nic_name=self.name)
        routable = [line for line in netst if line.flags.lower() == "G".lower()]
        use_route: Netstated = next(iter(routable), None)
        if (use_route is not None):
            return use_route.gateway
        return None
    
    def getNetmask(self) -> Optional[str]:
        gw = self.getGateway()
        try:
            netmask = gw[:gw.rfind(".")+1]+"0"
            return netmask
        except:
            logging.error(f"getNetmask => {gw}")
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



    def parseNetstat(self, nic_name: str) -> list[Netstated]:
        result = subprocess.getoutput(f"netstat -r -n -e -4 | grep {nic_name}").split("\n")
        if (len(result) == 0):
            return []
        else:
            entries: list[Netstated] = []
            for line in result:
                try:
                    columns = re.split(r'\s+', line)
                    entries.append(
                        Netstated(
                            destination=columns[0],
                            gateway=columns[1],
                            genmask=columns[2],
                            flags=columns[3],
                            metric=columns[4],
                            ref=columns[5],
                            use=columns[6],
                            iface=columns[7]
                        )
                    )
                except:
                    logging.exception("Failed to parse netstat")
            return entries

    
