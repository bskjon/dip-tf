import unittest
import os
from DynamicRoutingUpdater.RoutingTable import RoutingTable

class RoutingTableTestCase(unittest.TestCase):
    test_rt_tables = "./test_rt_tables"
    test_rt_tables_with_my_entries = "./test_rt_tables_custom"
    test_adapter_list = ["testEth0", "testEth1"]
    test_table_basename = "test"
    
    def setUp(self):
        # Opprett den midlertidige testfilen
        with open(self.test_rt_tables, "w") as file:
            # Skriv inn noen eksisterende rader i den midlertidige testfilen
            file.write("0\tdefault\n")
            file.write("1\tmain\n")
            
        with open(self.test_rt_tables_with_my_entries, "w") as file:
            file.write("0\tdefault\n")
            file.write("1\tmain\n")
            file.write("2\ttest0\n")
            file.write("3\ttest1\n")
        
    def tearDown(self):
        # Fjern den midlertidige testfilen
        os.remove(self.test_rt_tables)
        os.remove(self.test_rt_tables_with_my_entries)
        
    def test_getRoutingTables(self):
        # Opprett en instans av RoutingTable med den midlertidige testfilbanen
        RoutingTable.rt_table_file = self.test_rt_tables
        routing_table = RoutingTable(tableBaseName=self.test_table_basename, adapterNames=self.test_adapter_list)
        
        # Kall metoden getRoutingTables og sjekk resultatet
        result = routing_table.getRoutingTables()
        
        # Utfør assertjekk på resultatet
        expected_result = ["0\tdefault", "1\tmain"]
        self.assertEqual(result, expected_result)
        
    def test_deleteMyEntries(self):
        # Opprett en instans av RoutingTable med den midlertidige testfilbanen
        RoutingTable.rt_table_file = self.test_rt_tables_with_my_entries
        routing_table = RoutingTable(tableBaseName=self.test_table_basename, adapterNames=self.test_adapter_list)
        
        # Kall metoden deleteMyEntries for å fjerne rader
        routing_table.deleteMyEntries()
        
        # Les den midlertidige testfilen og sjekk om radene er fjernet
        with open(self.test_rt_tables, "r") as file:
            result = file.readlines()
        
        # Utfør assertjekk på resultatet
        expected_result = ["0\tdefault", "1\tmain"]
        self.assertListEqual(
            [r.strip() for r in result],
            [r.strip() for r in expected_result]
        )
        
    def test_addMyEntries(self):
        # Opprett en instans av RoutingTable med den midlertidige testfilbanen
        RoutingTable.rt_table_file = self.test_rt_tables
        routing_table = RoutingTable(tableBaseName=self.test_table_basename, adapterNames=self.test_adapter_list)
        
        # Kall metoden addMyEntries for å legge til rader
        routing_table.addMyEntries()
        
        # Les den midlertidige testfilen og sjekk om radene er lagt til
        with open(self.test_rt_tables, "r") as file:
            result = file.readlines()
        
        # Utfør assertjekk på resultatet
        expected_result = ["0\tdefault", "1\tmain", "2\ttest0", "3\ttest1"]  # Forventer at de nye radene er lagt til
        #self.assertEqual(result, expected_result)
        self.assertListEqual(
            [r.strip() for r in result],
            [r.strip() for r in expected_result]
        )
