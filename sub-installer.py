import netifaces
from typing import List
from whaaaaat import prompt, print_json

class ip:
    ip: str = None
    subnet: str = None
    
    def __init__(self, ip: str, subnet: str) -> None:
        self.ip = ip
        self.subnet = subnet
    
class networkAdapter:
    __name: str = None
    __ip: ip = None
    
    def __init__(self, name: str, ip: ip) -> None:
        self.__name = name
        self.__ip = ip
        
    def name(self) -> str:
        return self.__name
    def ip(self) -> ip:
        return self.__ip

class setup:
    interfaces: List[networkAdapter] = []
    
    def __init__(self) -> None:
        ifaces = netifaces.interfaces()
        for iface in ifaces:
            try:
                ifa = (netifaces.ifaddresses(iface)[netifaces.AF_INET])
                #print(ifa)
                ipObj = self.getIp(ifa[0])
                if ipObj is not None:
                    self.interfaces.append(networkAdapter(iface, ipObj))
            except:
                print("Failed to read IPv4 on", iface)
        print(self.interfaces)

    def getIp(self, ifaddr: list) -> ip:
        if "addr" in ifaddr and "netmask" in ifaddr:
            ipaddr: str = ifaddr["addr"]
            ipsubnet: str = ifaddr["netmask"]
            return ip(ipaddr, ipsubnet)
        else:
            return None

if (__name__ == "__main__"):
    service = setup()
    listOfNics: list = []
    for item in service.interfaces:
        entry = "{}`n`t{}`n`t`n".format(item.name(), item.ip().ip, item.ip().subnet)
        listOfNics.append(entry)
    
    questions = [
        {
            "type": "checkbox",
            "name": "Network interfaces",
            "message": "Select network interfaces to watch",
            "choices": listOfNics
        }
    ]
    answers = prompt(questions)
    print(answers)
                    
                
                    
                    
            