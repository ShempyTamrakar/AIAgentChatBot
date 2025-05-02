"""
Question processor for the Data Center Chatbot application.
Maps natural language questions to appropriate database queries.
"""

import re
import logging
from query_handler import QueryHandler

logger = logging.getLogger(__name__)

class QuestionProcessor:
    """
    Processes natural language questions and maps them to specific query functions.
    """
    
    def __init__(self):
        """Initialize the question processor with pattern matchers."""
        # Location & Data Center patterns
        self.city_data_center_pattern = re.compile(r'which cities|what cities|cities.+data centers|which city')
        self.country_data_center_pattern = re.compile(r'how many data centers.+each country|data centers.+by country|country.+data centers')
        self.list_data_centers_pattern = re.compile(r'list all data centers|show all data centers|all data centers.+city|all data centers.+country')
        
        # Rack & Server patterns
        self.racks_per_data_center_pattern = re.compile(r'how many racks|racks in each|racks.+data center')
        self.servers_with_racks_pattern = re.compile(r'list all servers|servers with.+rack|servers.+data center')
        self.servers_with_os_pattern = re.compile(r'servers.+ubuntu|servers running|which os|running ubuntu|ubuntu os')
        self.empty_racks_pattern = re.compile(r'empty rack|racks.+no servers|racks.+without servers|racks do not have')
        
        # Network Device patterns
        self.list_network_devices_pattern = re.compile(r'list.+network|show.+network|network devices.+data center')
        self.network_devices_count_pattern = re.compile(r'how many network|count.+network|network.+count')
        self.network_devices_location_pattern = re.compile(r'ip.+network.+london|network.+in london|london.+network|ip.+address.+london')
        
        # Maintenance Log patterns
        self.maintenance_by_technician_pattern = re.compile(r'maintenance.+john|john doe|performed by|jane smith')
        self.maintenance_count_pattern = re.compile(r'maintenance tasks.+server.+network|how many maintenance|maintenance count')
        self.server_maintenance_year_pattern = re.compile(r'server.+maintenance.+2023|maintenance.+2023|2023.+maintenance')
        self.maintenance_with_entity_pattern = re.compile(r'maintenance logs.+corresponding|list.+maintenance')
        
        # Analytical patterns
        self.servers_by_country_pattern = re.compile(r'server.+each country|servers.+country|total.+servers.+country')
        self.data_centers_both_pattern = re.compile(r'data centers.+both|both servers.+network|servers and network')
        self.recent_maintenance_pattern = re.compile(r'most recent|latest maintenance|recent.+maintenance')
        self.no_maintenance_pattern = re.compile(r'never had maintenance|without maintenance|no maintenance')
    
    def process_question(self, question):
        """
        Process a natural language question and return the appropriate answer.
        
        Args:
            question (str): The natural language question
            
        Returns:
            str: Formatted answer to the question
        """
        question = question.lower().strip()
        logger.info(f"Processing question: {question}")
        
        # Location & Data Center Questions
        if self.city_data_center_pattern.search(question):
            logger.info("Matched: Cities with data centers")
            return self._format_cities_with_data_centers()
            
        if self.country_data_center_pattern.search(question):
            logger.info("Matched: Data centers by country")
            return self._format_data_centers_by_country()
            
        if self.list_data_centers_pattern.search(question):
            logger.info("Matched: List data centers with locations")
            return self._format_data_centers_with_locations()
        
        # Rack & Server Questions
        if self.racks_per_data_center_pattern.search(question):
            logger.info("Matched: Racks per data center")
            return self._format_racks_by_data_center()
            
        if self.servers_with_racks_pattern.search(question):
            logger.info("Matched: Servers with racks and data centers")
            return self._format_servers_with_racks_and_data_centers()
            
        if self.servers_with_os_pattern.search(question):
            logger.info("Matched: Servers with Ubuntu OS")
            return self._format_servers_with_os('ubuntu')
            
        if self.empty_racks_pattern.search(question):
            logger.info("Matched: Empty racks")
            return self._format_empty_racks()
        
        # Network Device Questions
        if self.list_network_devices_pattern.search(question):
            logger.info("Matched: List network devices")
            return self._format_network_devices_with_data_centers()
            
        if self.network_devices_count_pattern.search(question):
            logger.info("Matched: Network devices by data center")
            return self._format_network_devices_by_data_center()
            
        if self.network_devices_location_pattern.search(question):
            logger.info("Matched: Network devices in London")
            return self._format_network_devices_by_location('London')
        
        # Maintenance Log Questions
        if self.maintenance_by_technician_pattern.search(question):
            logger.info("Matched: Maintenance by John Doe")
            if 'john' in question or 'doe' in question:
                return self._format_maintenance_by_technician('John Doe')
            elif 'jane' in question or 'smith' in question:
                return self._format_maintenance_by_technician('Jane Smith')
            else:
                # Extract technician name if possible
                technician = self._extract_technician(question)
                return self._format_maintenance_by_technician(technician or 'John Doe')
            
        if self.maintenance_count_pattern.search(question):
            logger.info("Matched: Maintenance count by entity type")
            return self._format_maintenance_count_by_entity_type()
            
        if self.server_maintenance_year_pattern.search(question):
            logger.info("Matched: Server maintenance in 2023")
            return self._format_server_maintenance_by_year(2023)
            
        if self.maintenance_with_entity_pattern.search(question):
            logger.info("Matched: Maintenance logs with entity names")
            return self._format_maintenance_logs_with_entity_names()
        
        # Analytical Questions
        if self.servers_by_country_pattern.search(question):
            logger.info("Matched: Server count by country")
            return self._format_server_count_by_country()
            
        if self.data_centers_both_pattern.search(question):
            logger.info("Matched: Data centers with both servers and network devices")
            return self._format_data_centers_with_both()
            
        if self.recent_maintenance_pattern.search(question):
            logger.info("Matched: Most recent server maintenance")
            return self._format_most_recent_server_maintenance()
            
        if self.no_maintenance_pattern.search(question):
            logger.info("Matched: Entities without maintenance")
            return self._format_entities_without_maintenance()
        
        # Default response
        return "I'm not sure how to answer that question. Could you please rephrase it or ask something about our data centers, servers, racks, network devices, or maintenance logs?"
    
    def _extract_technician(self, question):
        """Extract technician name from question if possible."""
        # Simple pattern: "by {name}"
        match = re.search(r'by\s+([A-Z][a-z]+\s+[A-Z][a-z]+)', question, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    
    # Format responses for each query type
    
    def _format_cities_with_data_centers(self):
        result = QueryHandler.get_cities_with_data_centers()
        if result["success"]:
            cities = result["cities"]
            if cities:
                if len(cities) == 1:
                    return f"We have data centers in {cities[0]}."
                elif len(cities) == 2:
                    return f"We have data centers in {cities[0]} and {cities[1]}."
                else:
                    city_list = ", ".join(cities[:-1]) + f", and {cities[-1]}"
                    return f"We have data centers in {city_list}."
            else:
                return "We don't have data centers in any cities yet."
        else:
            return f"Sorry, I couldn't retrieve the list of cities: {result.get('error', 'Unknown error')}"
    
    def _format_data_centers_by_country(self):
        result = QueryHandler.get_data_centers_by_country()
        if result["success"]:
            countries = result["countries"]
            if countries:
                response = "Here's the number of data centers in each country:\n\n"
                for country in countries:
                    response += f"• {country['country']}: {country['data_center_count']} data center"
                    if country['data_center_count'] > 1:
                        response += "s"
                    response += "\n"
                return response
            else:
                return "We don't have any data centers yet."
        else:
            return f"Sorry, I couldn't retrieve the data center counts: {result.get('error', 'Unknown error')}"
    
    def _format_data_centers_with_locations(self):
        result = QueryHandler.list_data_centers_with_locations()
        if result["success"]:
            data_centers = result["data_centers"]
            if data_centers:
                response = "Here are all our data centers with their locations:\n\n"
                for i, dc in enumerate(data_centers, 1):
                    state_info = f", {dc['state']}" if dc['state'] else ""
                    response += f"{i}. {dc['name']} in {dc['city']}{state_info}, {dc['country']}\n"
                return response
            else:
                return "We don't have any data centers yet."
        else:
            return f"Sorry, I couldn't retrieve the data centers: {result.get('error', 'Unknown error')}"
    
    def _format_racks_by_data_center(self):
        result = QueryHandler.get_racks_by_data_center()
        if result["success"]:
            rack_counts = result["rack_counts"]
            if rack_counts:
                response = "Here's the number of racks in each data center:\n\n"
                for rack in rack_counts:
                    response += f"• {rack['data_center_name']}: {rack['rack_count']} rack"
                    if rack['rack_count'] != 1:
                        response += "s"
                    response += "\n"
                return response
            else:
                return "We don't have any racks in our data centers yet."
        else:
            return f"Sorry, I couldn't retrieve the rack counts: {result.get('error', 'Unknown error')}"
    
    def _format_servers_with_racks_and_data_centers(self):
        result = QueryHandler.list_servers_with_racks_and_data_centers()
        if result["success"]:
            servers = result["servers"]
            if servers:
                response = "Here are all our servers with their rack and data center information:\n\n"
                for i, server in enumerate(servers, 1):
                    response += f"{i}. {server['hostname']} (IP: {server['ip_address']})\n"
                    response += f"   Rack: {server['rack_label']}\n"
                    response += f"   Data Center: {server['data_center_name']}\n"
                    response += f"   OS: {server['os']}\n\n"
                return response
            else:
                return "We don't have any servers in our data centers yet."
        else:
            return f"Sorry, I couldn't retrieve the server information: {result.get('error', 'Unknown error')}"
    
    def _format_servers_with_os(self, os_filter):
        result = QueryHandler.get_servers_with_os(os_filter)
        if result["success"]:
            servers = result["servers"]
            if servers:
                response = f"Here are the servers running {os_filter.title()}:\n\n"
                for i, server in enumerate(servers, 1):
                    response += f"{i}. {server['hostname']} (OS: {server['os']})\n"
                    response += f"   Rack: {server['rack_label']}\n"
                    response += f"   Data Center: {server['data_center_name']}\n\n"
                return response
            else:
                return f"We don't have any servers running {os_filter.title()} yet."
        else:
            return f"Sorry, I couldn't retrieve the server information: {result.get('error', 'Unknown error')}"
    
    def _format_empty_racks(self):
        result = QueryHandler.get_empty_racks()
        if result["success"]:
            racks = result["empty_racks"]
            if racks:
                response = "Here are the racks that don't have any servers:\n\n"
                for i, rack in enumerate(racks, 1):
                    response += f"{i}. {rack['rack_label']} in {rack['data_center_name']} Data Center\n"
                return response
            else:
                return "All racks currently have servers installed."
        else:
            return f"Sorry, I couldn't check for empty racks: {result.get('error', 'Unknown error')}"
    
    def _format_network_devices_with_data_centers(self):
        result = QueryHandler.list_network_devices_with_data_centers()
        if result["success"]:
            devices = result["network_devices"]
            if devices:
                response = "Here are all our network devices with their data center locations:\n\n"
                for i, device in enumerate(devices, 1):
                    response += f"{i}. {device['device_name']} ({device['device_type']})\n"
                    response += f"   IP: {device['ip_address']}\n"
                    response += f"   Data Center: {device['data_center_name']}\n\n"
                return response
            else:
                return "We don't have any network devices in our data centers yet."
        else:
            return f"Sorry, I couldn't retrieve the network device information: {result.get('error', 'Unknown error')}"
    
    def _format_network_devices_by_data_center(self):
        result = QueryHandler.get_network_devices_by_data_center()
        if result["success"]:
            counts = result["device_counts"]
            if counts:
                response = "Here's the number of network devices in each data center:\n\n"
                for count in counts:
                    response += f"• {count['data_center_name']}: {count['device_count']} device"
                    if count['device_count'] != 1:
                        response += "s"
                    response += "\n"
                return response
            else:
                return "We don't have any network devices in our data centers yet."
        else:
            return f"Sorry, I couldn't retrieve the network device counts: {result.get('error', 'Unknown error')}"
    
    def _format_network_devices_by_location(self, location):
        result = QueryHandler.find_network_devices_by_location(location)
        if result["success"]:
            devices = result["network_devices"]
            if devices:
                response = f"Here are the network devices in {location}:\n\n"
                for i, device in enumerate(devices, 1):
                    response += f"{i}. {device['device_name']} ({device['device_type']})\n"
                    response += f"   IP: {device['ip_address']}\n"
                    response += f"   Data Center: {device['data_center_name']}\n\n"
                return response
            else:
                return f"We don't have any network devices in {location} yet."
        else:
            return f"Sorry, I couldn't retrieve the network device information: {result.get('error', 'Unknown error')}"
    
    def _format_maintenance_by_technician(self, technician):
        result = QueryHandler.get_maintenance_by_technician(technician)
        if result["success"]:
            logs = result["maintenance_logs"]
            if logs:
                response = f"Here are the maintenance tasks performed by {technician}:\n\n"
                for i, log in enumerate(logs, 1):
                    entity_type = log['entity_type'].replace('_', ' ').title()
                    response += f"{i}. {entity_type}: {log['entity_name']}\n"
                    response += f"   Date: {log['maintenance_date']}\n"
                    response += f"   Notes: {log['notes']}\n\n"
                return response
            else:
                return f"No maintenance has been performed by {technician} yet."
        else:
            return f"Sorry, I couldn't retrieve the maintenance information: {result.get('error', 'Unknown error')}"
    
    def _format_maintenance_count_by_entity_type(self):
        result = QueryHandler.get_maintenance_count_by_entity_type()
        if result["success"]:
            counts = result["maintenance_counts"]
            if counts:
                response = "Here's the breakdown of maintenance tasks by entity type:\n\n"
                for count in counts:
                    entity_type = count['entity_type'].replace('_', ' ').title()
                    response += f"• {entity_type}s: {count['maintenance_count']} task"
                    if count['maintenance_count'] != 1:
                        response += "s"
                    response += "\n"
                return response
            else:
                return "No maintenance tasks have been recorded yet."
        else:
            return f"Sorry, I couldn't retrieve the maintenance counts: {result.get('error', 'Unknown error')}"
    
    def _format_server_maintenance_by_year(self, year):
        result = QueryHandler.get_server_maintenance_by_year(year)
        if result["success"]:
            logs = result["server_maintenance"]
            if logs:
                response = f"Here are the servers that had maintenance in {year}:\n\n"
                for i, log in enumerate(logs, 1):
                    response += f"{i}. {log['hostname']} (IP: {log['ip_address']})\n"
                    response += f"   Date: {log['maintenance_date']}\n"
                    response += f"   Technician: {log['performed_by']}\n"
                    response += f"   Notes: {log['notes']}\n\n"
                return response
            else:
                return f"No server maintenance was performed in {year}."
        else:
            return f"Sorry, I couldn't retrieve the maintenance information: {result.get('error', 'Unknown error')}"
    
    def _format_maintenance_logs_with_entity_names(self):
        result = QueryHandler.list_maintenance_logs_with_entity_names()
        if result["success"]:
            logs = result["maintenance_logs"]
            if logs:
                response = "Here are all maintenance logs with their corresponding entity names:\n\n"
                for i, log in enumerate(logs, 1):
                    entity_type = log['entity_type'].replace('_', ' ').title()
                    response += f"{i}. {entity_type}: {log['entity_name']}\n"
                    response += f"   Date: {log['maintenance_date']}\n"
                    response += f"   Technician: {log['performed_by']}\n"
                    response += f"   Notes: {log['notes']}\n\n"
                return response
            else:
                return "No maintenance logs have been recorded yet."
        else:
            return f"Sorry, I couldn't retrieve the maintenance logs: {result.get('error', 'Unknown error')}"
    
    def _format_server_count_by_country(self):
        result = QueryHandler.get_server_count_by_country()
        if result["success"]:
            counts = result["country_servers"]
            if counts:
                response = "Here's the total number of servers in each country:\n\n"
                for count in counts:
                    response += f"• {count['country']}: {count['server_count']} server"
                    if count['server_count'] != 1:
                        response += "s"
                    response += "\n"
                return response
            else:
                return "We don't have any servers deployed yet."
        else:
            return f"Sorry, I couldn't retrieve the server counts: {result.get('error', 'Unknown error')}"
    
    def _format_data_centers_with_both(self):
        result = QueryHandler.get_data_centers_with_both_servers_and_network_devices()
        if result["success"]:
            centers = result["data_centers"]
            if centers:
                response = "Here are the data centers that have both servers and network devices:\n\n"
                for i, center in enumerate(centers, 1):
                    response += f"{i}. {center['name']}\n"
                    response += f"   Servers: {center['server_count']}\n"
                    response += f"   Network devices: {center['network_device_count']}\n\n"
                return response
            else:
                return "None of our data centers currently have both servers and network devices."
        else:
            return f"Sorry, I couldn't retrieve the data center information: {result.get('error', 'Unknown error')}"
    
    def _format_most_recent_server_maintenance(self):
        result = QueryHandler.get_most_recent_server_maintenance()
        if result["success"]:
            server = result["server"]
            response = f"The most recent server maintenance was performed on {server['hostname']}:\n\n"
            response += f"• Date: {server['maintenance_date']}\n"
            response += f"• Performed by: {server['performed_by']}\n"
            response += f"• Data Center: {server['data_center_name']}\n"
            response += f"• Rack: {server['rack_label']}\n"
            response += f"• Notes: {server['notes']}\n"
            return response
        else:
            return f"Sorry, I couldn't retrieve the maintenance information: {result.get('error', 'Unknown error')}"
    
    def _format_entities_without_maintenance(self):
        result = QueryHandler.get_entities_without_maintenance()
        if result["success"]:
            entities = result["entities"]
            if entities:
                response = "Here are the entities that have never had maintenance performed:\n\n"
                
                # Group by entity type for better readability
                servers = [e for e in entities if e['entity_type'] == 'server']
                network_devices = [e for e in entities if e['entity_type'] == 'network_device']
                
                if servers:
                    response += "Servers:\n"
                    for i, server in enumerate(servers, 1):
                        response += f"{i}. {server['entity_name']} (IP: {server['ip_address']})\n"
                        response += f"   Rack: {server['rack_label']}\n"
                        response += f"   Data Center: {server['data_center_name']}\n\n"
                
                if network_devices:
                    response += "Network Devices:\n"
                    for i, device in enumerate(network_devices, 1):
                        response += f"{i}. {device['entity_name']} (IP: {device['ip_address']})\n"
                        response += f"   Data Center: {device['data_center_name']}\n\n"
                        
                return response
            else:
                return "All entities (servers and network devices) have had maintenance performed."
        else:
            return f"Sorry, I couldn't retrieve the entity information: {result.get('error', 'Unknown error')}"