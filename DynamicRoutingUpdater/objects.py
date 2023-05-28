from datetime import datetime

class Rule:
    priority: int = 0
    source: str = None
    table: str = None
    
    def __init__(self, priority: int = 0, source: str = None, table: str = None) -> None:
        self.priority = priority
        self.source = source
        self.table = table
        
    def __str__(self) -> str:
        return "\tpriority => \t{},\n\tsource => \t{},\n\ttable => \t{}\n".format(self.priority, self.source, self.table)
    
class Route(object):
    """_summary_
    """
    destination: str = None
    gateway: str = None
    device: str = None
    preferredSource: str = None
    scope: str = None
    
    def __init__(self, destination: str = None, gateway: str = None, device: str = None, preferredSource: str = None, scope: str = None) -> None:
        self.destination = destination
        self.gateway = gateway
        self.device = device
        self.preferredSource = preferredSource
        self.scope = scope
    def __str__(self) -> str:
        return f"\n\tdestination =>\t\t{self.destination}\n\tgateway =>\t\t{self.gateway}\n\tdevice =>\t\t{self.device}\n\tpreferredSource =>\t{self.preferredSource}\n\tscope =>\t\t{self.scope}"
    
class IpData:
    name: str = None # Network Adapter name
    ip: str = None
    subnet: str = None
    cidr: str = None
    gateway: str = None
    netmask: str = None # Gateway address but with 0 at the end
    timeOfCreated: str = "Never set!"

    def __init__(self, name: str = None, gateway: str = None, ip: str = None, subnet: str = None, cidr: str = None, netmask: str = None) -> None:
        self.name = name
        self.gateway = gateway
        self.ip = ip
        self.subnet = subnet
        self.cidr = cidr
        self.netmask = netmask
        self.timeOfCreated = datetime.now().strftime("%H:%M:%S %d.%m.%Y")

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
            return False
        else:
            return True
        
    def __str__(self):
        return "\n{}\n\t{}\n\t{}\t/{}\n\t{}\n\t{}".format(self.name, self.ip, self.subnet, self.cidr, self.gateway, self.timeOfCreated)

class IpInfo:
    interface: str = None
    is_dynamic: bool = False
    valid_life_time_in_sec: int = 0
    ip_address: str = None
    ip_address_prefix: str = None
    
    def __init__(self, interface: str, dynamic: bool, ttl: int, ip: str, prefix: str) -> None:
        self.interface = interface
        self.is_dynamic = dynamic
        self.valid_life_time_in_sec = ttl
        self.ip_address = ip
        self.ip_address_prefix = prefix
    def __str__(self):
        return "\tIPv4 => {},\n\t Prefix => {},\n\t isDHCP => {},\n\t TTL => {}\n".format(self.ip_address, self.ip_address_prefix, self.is_dynamic, self.valid_life_time_in_sec())
    
    