from abc import ABC, abstractmethod
import logging
import threading
from threading import Thread
import time

from .NetworkAdapter import NetworkAdapter

from .AddressInfo import AddressInfo
from .Routing import Routing, Route
from .Rules import Rules

logging.basicConfig(level=logging.INFO)

class RouteAndRuleObserverManager():
    """"""
    adapter__rt: dict = {}
    watchers: list[Thread] = []

    def __init__(self, adapter__rt: dict) -> None:
        """"""
        self.adapter__rt = adapter__rt
        for name, table in adapter__rt.items():
            routeObserver = RouteObserver(nic_name=name, rt_name=table)
            ruleObserver = RuleObserver(nic_name=name, rt_name=table)

            self.watchers.append(Thread(target=routeObserver.start))
            self.watchers.append(Thread(target=ruleObserver.start))

    def execute(self) -> None:
        """Starts all observers in their own thread
        """
        for thread in self.watchers:
            thread.start()


class __Shared(ABC):
    """"""
    addrInfo: AddressInfo = None
    stopFlag = threading.Event()

    nic_name: str = None
    rt_name: str = None

    def __init__(self, nic_name: str, rt_name: str) -> None:
        self.nic_name = nic_name
        self.rt_name = rt_name
        self.addrInfo = AddressInfo(nic_name)

    def start(self) -> None:
        """Starts the observer
        If adress is not available yet, ready check should postpone operations
        """
        while (not self.isReady()):
            logging.info("RouteObserver is waiting for address to be valid..", self.nic_name, self.rt_name)
            time.sleep(60)
        
        # Waits 30 sec just to prevent conflict if both hook and this runs at the same time
        time.sleep(30)
        self.monitor()

    @abstractmethod
    def monitor(self) -> None:
        pass

    def stop(self) -> None:
        """
        """
        self.stopFlag.set()

    def isReady(self):
        """"""
        info = self.addrInfo.read()
        if (info.valid_life_time_in_sec == None):
            return False
        else:
            return True


class RouteObserver(__Shared):
    """Goes over the routing table, designated and main
    Validates that the routes are correct to expected setup.
    If there is any deviation, it should detect it and perform corrective actions.
    """
    
    def __init__(self, nic_name: str, rt_name: str) -> None:
        super().__init__(nic_name, rt_name)

    def start(self) -> None:
        logging.info("Starting RouteObserver on {table} for {nic}".format(table=self.rt_name, nic=self.nic_name))
        return super().start()

    def monitor(self) -> None:
        """
        """
        while not self.stopFlag.is_set():
            if (self.__routeValidation(table=self.rt_name) == False):
                try:
                    with open("/tmp/dru-hook", 'w') as fifo:
                        fifo.write(self.nic_name)
                except:
                    logging.error("Failed to adjust routes..", self.nic_name, self.rt_name)
            elif (self.__lostPriorities()):
                logging.info("{table} lost routing priority to main".format(table=self.rt_name))
                adapterInfo = NetworkAdapter(self.nic_name)
                ip = adapterInfo.getIpData()
                rt_manager = Routing("main")
                logging.info("{table} attempting to clear routes in conflict with main".format(table=self.rt_name))
                rt_manager.deleteRoutes(ip)
    
            time.sleep(30)

    def __routeValidation(self, table: str) -> bool:
        """"""
        addri = self.addrInfo.read()
        routes = Routing.getRoutes(table=table)
        if (len(routes) < 2):
            return False
        if all(x.preferredSource == addri.ip_address for x in routes) == False:
            return False
        return True
    
    def __lostPriorities(self) -> bool:
        """Checks wether the table has lost priority to main, and route is present in both
        """
        active = Routing.getRoutes(table=self.rt_name)
        main = Routing.getRoutes(table="main")

        hasLostPriotiry: bool = False
        # Check if any route in active has common values in main
        for active_route in active:
            found_route = next((main_route for main_route in main if
                                main_route.destination == active_route.destination and
                                main_route.gateway == active_route.gateway and
                                main_route.device == active_route.device and
                                main_route.preferredSource == active_route.preferredSource), None)
            if found_route:
                hasLostPriotiry = True
                logging.info(f"Route {active_route} exists in both active and main. Found route in main: {found_route}")
        return hasLostPriotiry


class RuleObserver(__Shared):
    """"""
    def __init__(self, nic_name: str, rt_name: str) -> None:
        super().__init__(nic_name, rt_name)

    def start(self) -> None:
        logging.info("Starting RuleObserver on {table} for {nic}".format(table=self.rt_name, nic=self.nic_name))
        return super().start()

    def monitor(self) -> None:
        while not self.stopFlag.is_set():
            if (self.__ruleValidation(table=self.rt_name) == False):
                addri = self.addrInfo.read()
                Rules().addRule(addri.ip_address, table=self.rt_name)

            time.sleep(30)

    def __ruleValidation(self, table: str) -> bool:
        """"""
        addri = self.addrInfo.read()
        rules = Rules.getRules(table=table)
        if (len(rules) == 0):
            return False
        if any(x.source == addri.ip_address for x in rules) == False:
            return False
        return True

