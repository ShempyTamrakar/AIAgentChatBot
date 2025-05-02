"""
Flask web application for the Data Center Chatbot.
"""

import os
import logging
from flask import Flask, render_template, request, jsonify, session, send_from_directory
import pandas as pd
import numpy as np
import requests

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Mock RAG functionality until we can integrate the full system
from database import DatabaseManager

class DataCenterChatbot:
    """An enhanced chatbot for interacting with the data center database."""
    
    def __init__(self):
        """Initialize the chatbot with a database connection."""
        self.db_manager = DatabaseManager()
        self.schema_info = self.db_manager.get_schema_info()
        logger.info("Data Center Chatbot initialized with database connection")
    
    def get_schema_info(self):
        """Get database schema information."""
        return self.schema_info
    
    def execute_query(self, query, params=()):
        """Execute a SQL query against the database.
        
        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query
        
        Returns:
            list: List of dictionaries with query results
        """
        try:
            return self.db_manager.execute_query(query, params)
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return [{"error": str(e)}]
    
    def process_input(self, user_input):
        """Process user input and generate a response based on database information."""
        user_input = user_input.lower().strip()
        
        # Handle greetings and farewells - but only if they're the primary content
        greetings = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']
        farewells = ['bye', 'goodbye', 'see you', 'talk to you later', 'thanks']
        
        # Only respond to greetings if they're the main content (i.e., the message is very short)
        if len(user_input.split()) <= 3 and any(user_input == greeting for greeting in greetings):
            return "Hello! I'm your data center assistant. I can provide information about our data centers, servers, and infrastructure. How can I help you today?"
        
        if len(user_input.split()) <= 3 and any(user_input == farewell for farewell in farewells):
            return "Goodbye! Feel free to chat again when you need information about our data centers."
        
        # Handle questions about data centers
        try:
            # =================== Location & Data Center Questions ===================
            
            # Which cities have data centers?
            if any(phrase in user_input for phrase in ["which cities have data centers", "cities with data centers", "data center cities"]):
                results = self.execute_query("""
                    SELECT DISTINCT l.city, l.country
                    FROM locations l
                    JOIN data_centers dc ON l.location_id = dc.location_id
                    ORDER BY l.country, l.city
                """)
                if not results:
                    return "I couldn't find any cities with data centers in our system."
                
                response = "Here are the cities that have data centers:\n\n"
                for i, loc in enumerate(results, 1):
                    response += f"{i}. {loc['city']}, {loc['country']}\n"
                return response
            
            # How many data centers are in each country?
            if ("data centers" in user_input and "country" in user_input) or ("data center" in user_input and "country" in user_input):
                results = self.execute_query("""
                    SELECT l.country, COUNT(dc.data_center_id) as dc_count
                    FROM locations l
                    JOIN data_centers dc ON l.location_id = dc.location_id
                    GROUP BY l.country
                    ORDER BY dc_count DESC
                """)
                if not results:
                    return "I couldn't find any data centers grouped by country in our system."
                
                # Format as a table for better display
                response = "Here is the count of data centers in each country:\n\n"
                response += "| Country | Number of Data Centers |\n"
                response += "|---------|------------------------|\n"
                for res in results:
                    response += f"| {res['country']} | {res['dc_count']} |\n"
                return response
            
            # List all data centers along with their corresponding city and country
            if ("list" in user_input and "data centers" in user_input and ("city" in user_input or "country" in user_input)) or "data centers with locations" in user_input:
                results = self.execute_query("""
                    SELECT dc.name, l.city, l.state, l.country
                    FROM data_centers dc
                    JOIN locations l ON dc.location_id = l.location_id
                    ORDER BY l.country, l.city, dc.name
                """)
                if not results:
                    return "I couldn't find any data centers in our system."
                
                response = "Here are all our data centers with their locations:\n\n"
                for i, dc in enumerate(results, 1):
                    state_info = f", {dc['state']}" if dc['state'] else ""
                    response += f"{i}. {dc['name']} - {dc['city']}{state_info}, {dc['country']}\n"
                return response
            
            # =================== Rack & Server Questions ===================
            
            # How many racks are in each data center?
            if ("racks" in user_input and "data center" in user_input) or "racks per data center" in user_input:
                results = self.execute_query("""
                    SELECT dc.name as data_center, COUNT(r.rack_id) as rack_count
                    FROM data_centers dc
                    LEFT JOIN racks r ON dc.data_center_id = r.data_center_id
                    GROUP BY dc.data_center_id
                    ORDER BY rack_count DESC
                """)
                if not results:
                    return "I couldn't find information about rack counts in our data centers."
                
                # Format as a table for better display
                response = "Here is the number of racks in each data center:\n\n"
                response += "| Data Center | Number of Racks |\n"
                response += "|-------------|----------------|\n"
                for res in results:
                    response += f"| {res['data_center']} | {res['rack_count']} |\n"
                return response
            
            # List all servers along with their rack label and data center name
            if any(phrase in user_input for phrase in ["list all servers with rack and data center", "servers with rack label and data center", "all servers with their rack and data center"]):
                results = self.execute_query("""
                    SELECT s.hostname, s.ip_address, r.rack_label, dc.name as data_center
                    FROM servers s
                    JOIN racks r ON s.rack_id = r.rack_id
                    JOIN data_centers dc ON r.data_center_id = dc.data_center_id
                    ORDER BY dc.name, r.rack_label, s.hostname
                """)
                if not results:
                    return "I couldn't find any servers with their rack and data center information."
                
                response = "Here are all servers with their rack and data center information:\n\n"
                for i, res in enumerate(results, 1):
                    response += f"{i}. Server: {res['hostname']} ({res['ip_address']})\n"
                    response += f"   Rack: {res['rack_label']}, Data Center: {res['data_center']}\n\n"
                return response
            
            # Which servers are running Ubuntu OS?
            if any(phrase in user_input for phrase in ["which servers are running ubuntu", "ubuntu servers", "servers with ubuntu os"]):
                results = self.execute_query("""
                    SELECT s.hostname, s.ip_address, s.os, dc.name as data_center
                    FROM servers s
                    JOIN racks r ON s.rack_id = r.rack_id
                    JOIN data_centers dc ON r.data_center_id = dc.data_center_id
                    WHERE s.os LIKE '%Ubuntu%'
                    ORDER BY dc.name, s.hostname
                """)
                if not results:
                    return "I couldn't find any servers running Ubuntu OS."
                
                response = "Here are the servers running Ubuntu OS:\n\n"
                for i, res in enumerate(results, 1):
                    response += f"{i}. {res['hostname']} ({res['ip_address']})\n"
                    response += f"   OS: {res['os']}, Data Center: {res['data_center']}\n\n"
                return response
            
            # Which racks do not have any servers?
            if any(phrase in user_input for phrase in ["which racks do not have any servers", "empty racks", "racks without servers"]):
                results = self.execute_query("""
                    SELECT r.rack_label, dc.name as data_center
                    FROM racks r
                    JOIN data_centers dc ON r.data_center_id = dc.data_center_id
                    LEFT JOIN servers s ON r.rack_id = s.rack_id
                    WHERE s.server_id IS NULL
                    ORDER BY dc.name, r.rack_label
                """)
                if not results:
                    return "All racks have at least one server assigned."
                
                response = "Here are the racks that do not have any servers:\n\n"
                for i, res in enumerate(results, 1):
                    response += f"{i}. Rack {res['rack_label']} in {res['data_center']} Data Center\n"
                return response
            
            # =================== Network Device Questions ===================
            
            # List all network devices along with their type and the data center they are located in
            if any(phrase in user_input for phrase in ["list all network devices", "network devices with type and data center", "all network devices and their data center"]):
                results = self.execute_query("""
                    SELECT nd.device_name, nd.device_type, nd.ip_address, dc.name as data_center
                    FROM network_devices nd
                    JOIN data_centers dc ON nd.data_center_id = dc.data_center_id
                    ORDER BY dc.name, nd.device_type, nd.device_name
                """)
                if not results:
                    return "I couldn't find any network devices in our system."
                
                response = "Here are all network devices with their type and data center:\n\n"
                for i, res in enumerate(results, 1):
                    response += f"{i}. {res['device_name']} ({res['ip_address']})\n"
                    response += f"   Type: {res['device_type']}, Data Center: {res['data_center']}\n\n"
                return response
            
            # How many network devices are in each data center?
            if any(phrase in user_input for phrase in ["how many network devices in each data center", "network devices per data center", "count of network devices by data center"]):
                results = self.execute_query("""
                    SELECT dc.name as data_center, COUNT(nd.device_id) as device_count
                    FROM data_centers dc
                    LEFT JOIN network_devices nd ON dc.data_center_id = nd.data_center_id
                    GROUP BY dc.data_center_id
                    ORDER BY device_count DESC
                """)
                if not results:
                    return "I couldn't find information about network device counts in our data centers."
                
                response = "Here is the number of network devices in each data center:\n\n"
                for i, res in enumerate(results, 1):
                    response += f"{i}. {res['data_center']}: {res['device_count']} device(s)\n"
                return response
            
            # Find all IP addresses of network devices in 'London'
            if any(phrase in user_input for phrase in ["ip addresses of network devices in london", "london network device ips", "network devices in london"]):
                results = self.execute_query("""
                    SELECT nd.device_name, nd.device_type, nd.ip_address
                    FROM network_devices nd
                    JOIN data_centers dc ON nd.data_center_id = dc.data_center_id
                    JOIN locations l ON dc.location_id = l.location_id
                    WHERE LOWER(l.city) = 'london'
                    ORDER BY nd.device_type, nd.device_name
                """)
                if not results:
                    return "I couldn't find any network devices in London."
                
                response = "Here are the IP addresses of network devices in London:\n\n"
                for i, res in enumerate(results, 1):
                    response += f"{i}. {res['device_name']} ({res['device_type']}): {res['ip_address']}\n"
                return response
            
            # =================== Maintenance Log Questions ===================
            
            # Which entities had maintenance performed by 'John Doe'?
            if any(phrase in user_input for phrase in ["entities maintained by john doe", "john doe maintenance", "maintenance by john doe"]):
                results = self.execute_query("""
                    SELECT ml.entity_type, ml.entity_id, ml.maintenance_date, ml.notes,
                           CASE 
                               WHEN ml.entity_type = 'server' THEN (SELECT s.hostname FROM servers s WHERE s.server_id = ml.entity_id)
                               WHEN ml.entity_type = 'network_device' THEN (SELECT nd.device_name FROM network_devices nd WHERE nd.device_id = ml.entity_id)
                               ELSE 'Unknown'
                           END as entity_name
                    FROM maintenance_logs ml
                    WHERE LOWER(ml.performed_by) = 'john doe'
                    ORDER BY ml.maintenance_date DESC
                """)
                if not results:
                    return "I couldn't find any maintenance performed by John Doe."
                
                response = "Here are the entities that had maintenance performed by John Doe:\n\n"
                for i, res in enumerate(results, 1):
                    entity_type = "Server" if res['entity_type'] == 'server' else "Network Device"
                    response += f"{i}. {entity_type}: {res['entity_name']}\n"
                    response += f"   Date: {res['maintenance_date']}, Notes: {res['notes']}\n\n"
                return response
            
            # How many maintenance tasks were performed on servers vs. network devices?
            if any(phrase in user_input.lower() for phrase in ["maintenance tasks", "maintenance count"]) or ("maintenance" in user_input.lower() and "vs" in user_input.lower()) or ("maintenance" in user_input.lower() and "compare" in user_input.lower()) or ("maintenance" in user_input.lower() and "entity type" in user_input.lower()):
                results = self.execute_query("""
                    SELECT entity_type, COUNT(*) as maintenance_count
                    FROM maintenance_logs
                    GROUP BY entity_type
                    ORDER BY maintenance_count DESC
                """)
                if not results:
                    return "I couldn't find any maintenance tasks in our system."
                
                response = "Here is the count of maintenance tasks by entity type:\n\n"
                for res in results:
                    entity_type = "Servers" if res['entity_type'] == 'server' else "Network Devices"
                    response += f"{entity_type}: {res['maintenance_count']} task(s)\n"
                return response
            
            # Which servers had maintenance in 2023?
            if "2023" in user_input and ("maintenance" in user_input.lower() or "maintained" in user_input.lower()) and "server" in user_input.lower():
                results = self.execute_query("""
                    SELECT s.hostname, s.ip_address, ml.maintenance_date, ml.performed_by, ml.notes
                    FROM maintenance_logs ml
                    JOIN servers s ON ml.entity_id = s.server_id
                    WHERE ml.entity_type = 'server' AND ml.maintenance_date LIKE '2023-%'
                    ORDER BY ml.maintenance_date DESC
                """)
                if not results:
                    return "I couldn't find any servers that had maintenance in 2023."
                
                # Format as a nice table
                response = "Here are the servers that had maintenance in 2023:\n\n"
                response += "| Server | IP Address | Maintenance Date | Performed By | Notes |\n"
                response += "|--------|-----------|-----------------|--------------|-------|\n"
                for res in results:
                    response += f"| {res['hostname']} | {res['ip_address']} | {res['maintenance_date']} | {res['performed_by']} | {res['notes']} |\n"
                return response
            
            # List all maintenance logs with the corresponding server or device name
            if any(phrase in user_input for phrase in ["all maintenance logs", "list maintenance logs", "maintenance history"]):
                results = self.execute_query("""
                    SELECT ml.maintenance_date, ml.performed_by, ml.notes, ml.entity_type,
                           CASE 
                               WHEN ml.entity_type = 'server' THEN (SELECT s.hostname FROM servers s WHERE s.server_id = ml.entity_id)
                               WHEN ml.entity_type = 'network_device' THEN (SELECT nd.device_name FROM network_devices nd WHERE nd.device_id = ml.entity_id)
                               ELSE 'Unknown'
                           END as entity_name
                    FROM maintenance_logs ml
                    ORDER BY ml.maintenance_date DESC
                """)
                if not results:
                    return "I couldn't find any maintenance logs in our system."
                
                response = "Here are all maintenance logs with their corresponding entity names:\n\n"
                for i, res in enumerate(results, 1):
                    entity_type = "Server" if res['entity_type'] == 'server' else "Network Device"
                    response += f"{i}. {entity_type}: {res['entity_name']}\n"
                    response += f"   Date: {res['maintenance_date']}, Performed by: {res['performed_by']}\n"
                    response += f"   Notes: {res['notes']}\n\n"
                return response
            
            # =================== Join-Based Analytical Questions ===================
            
            # Find the total number of servers in each country
            if ("servers" in user_input and "country" in user_input and "data center" not in user_input) or "server count by country" in user_input or "how many servers per country" in user_input:
                results = self.execute_query("""
                    SELECT l.country, COUNT(s.server_id) as server_count
                    FROM locations l
                    JOIN data_centers dc ON l.location_id = dc.location_id
                    JOIN racks r ON dc.data_center_id = r.data_center_id
                    JOIN servers s ON r.rack_id = s.rack_id
                    GROUP BY l.country
                    ORDER BY server_count DESC
                """)
                if not results:
                    return "I couldn't find information about server counts by country."
                
                # Format as a nice table
                response = "Here is the total number of servers in each country:\n\n"
                response += "| Country | Number of Servers |\n"
                response += "|---------|------------------|\n"
                for res in results:
                    response += f"| {res['country']} | {res['server_count']} |\n"
                return response
            
            # Which data centers have both servers and network devices?
            if any(phrase in user_input for phrase in ["data centers with both servers and network devices", "data centers with servers and network devices", "which data centers have both"]):
                results = self.execute_query("""
                    SELECT dc.name as data_center, l.city, l.country,
                           COUNT(DISTINCT s.server_id) as server_count,
                           COUNT(DISTINCT nd.device_id) as network_device_count
                    FROM data_centers dc
                    JOIN locations l ON dc.location_id = l.location_id
                    JOIN racks r ON dc.data_center_id = r.data_center_id
                    JOIN servers s ON r.rack_id = s.rack_id
                    JOIN network_devices nd ON dc.data_center_id = nd.data_center_id
                    GROUP BY dc.data_center_id
                    HAVING server_count > 0 AND network_device_count > 0
                    ORDER BY server_count + network_device_count DESC
                """)
                if not results:
                    return "I couldn't find any data centers that have both servers and network devices."
                
                # Format as a nice table
                response = "Here are the data centers that have both servers and network devices:\n\n"
                response += "| Data Center | Location | Servers | Network Devices |\n"
                response += "|-------------|----------|---------|----------------|\n"
                for res in results:
                    location = f"{res['city']}, {res['country']}"
                    response += f"| {res['data_center']} | {location} | {res['server_count']} | {res['network_device_count']} |\n"
                return response
            
            # Which server had the most recent maintenance performed?
            if ("recent" in user_input.lower() and "maintenance" in user_input.lower() and "server" in user_input.lower()) or ("latest" in user_input.lower() and "maintenance" in user_input.lower() and "server" in user_input.lower()):
                results = self.execute_query("""
                    SELECT s.hostname, s.ip_address, ml.maintenance_date, ml.performed_by, ml.notes
                    FROM maintenance_logs ml
                    JOIN servers s ON ml.entity_id = s.server_id
                    WHERE ml.entity_type = 'server'
                    ORDER BY ml.maintenance_date DESC
                    LIMIT 1
                """)
                if not results:
                    return "I couldn't find any maintenance records for servers."
                
                res = results[0]
                response = f"The server with the most recent maintenance is {res['hostname']} ({res['ip_address']}).\n\n"
                response += f"Maintenance details:\n"
                response += f"Date: {res['maintenance_date']}\n"
                response += f"Performed by: {res['performed_by']}\n"
                response += f"Notes: {res['notes']}\n"
                return response
            
            # Show all entities (servers or network devices) that have never had maintenance
            if (("without maintenance" in user_input.lower()) or ("never had maintenance" in user_input.lower()) or ("no maintenance" in user_input.lower())):
                # Servers without maintenance
                server_results = self.execute_query("""
                    SELECT s.hostname, s.ip_address, 'server' as entity_type
                    FROM servers s
                    LEFT JOIN maintenance_logs ml ON ml.entity_id = s.server_id AND ml.entity_type = 'server'
                    WHERE ml.log_id IS NULL
                """)
                
                # Network devices without maintenance
                device_results = self.execute_query("""
                    SELECT nd.device_name, nd.ip_address, 'network_device' as entity_type
                    FROM network_devices nd
                    LEFT JOIN maintenance_logs ml ON ml.entity_id = nd.device_id AND ml.entity_type = 'network_device'
                    WHERE ml.log_id IS NULL
                """)
                
                if not server_results and not device_results:
                    return "All entities have had maintenance performed at least once."
                
                response = "Here are the entities that have never had maintenance:\n\n"
                
                if server_results:
                    response += "Servers without maintenance:\n"
                    for i, res in enumerate(server_results, 1):
                        response += f"{i}. {res['hostname']} ({res['ip_address']})\n"
                    response += "\n"
                
                if device_results:
                    response += "Network devices without maintenance:\n"
                    for i, res in enumerate(device_results, 1):
                        response += f"{i}. {res['device_name']} ({res['ip_address']})\n"
                
                return response
            
            # Count of data centers
            if any(phrase in user_input for phrase in ["how many data centers", "number of data centers", "count of data centers"]):
                results = self.execute_query("SELECT COUNT(*) as count FROM data_centers")
                count = results[0]['count']
                return f"We currently have {count} data centers in our system."
            
            # List all data centers
            if any(phrase in user_input for phrase in ["list all data centers", "show all data centers", "what data centers", "which data centers"]):
                try:
                    # Check if we need to include location details
                    if any(word in user_input for word in ["city", "country", "location", "along with", "corresponding"]):
                        results = self.execute_query("""
                            SELECT dc.name, l.city, l.state, l.country
                            FROM data_centers dc
                            JOIN locations l ON dc.location_id = l.location_id
                            ORDER BY dc.name
                        """)
                        if not results:
                            return "I couldn't find any data centers in our system."
                        
                        response = "Here are all our data centers with their locations:\n\n"
                        for i, dc in enumerate(results, 1):
                            state_info = f", {dc['state']}" if dc['state'] else ""
                            response += f"{i}. {dc['name']} in {dc['city']}{state_info}, {dc['country']}\n"
                        return response
                    else:
                        # Standard data center list
                        results = self.execute_query("SELECT name FROM data_centers ORDER BY name")
                        if not results:
                            return "I couldn't find any data centers in our system."
                        
                        response = "Here are all our data centers:\n\n"
                        for i, dc in enumerate(results, 1):
                            response += f"{i}. {dc['name']}\n"
                        return response
                except Exception as e:
                    logger.error(f"Error listing data centers: {e}")
                    return f"I encountered an error processing your request: {str(e)}. Please try asking in a different way."
            
            # Information about a specific data center by location
            cities = ["new york", "san francisco", "london"]
            for city in cities:
                if city in user_input.lower():
                    # Get data centers in this city
                    results = self.execute_query("""
                        SELECT dc.data_center_id, dc.name, l.city, l.state, l.country
                        FROM data_centers dc
                        JOIN locations l ON dc.location_id = l.location_id
                        WHERE LOWER(l.city) LIKE ?
                    """, (f"%{city}%",))
                    
                    if results:
                        response = f"Data centers in {city.title()}:\n\n"
                        for i, dc in enumerate(results, 1):
                            state_info = f", {dc['state']}" if dc['state'] else ""
                            response += f"{i}. {dc['name']} Data Center in {dc['city']}{state_info}, {dc['country']}\n"
                        
                        # If only one result, add rack counts
                        if len(results) == 1:
                            dc_id = results[0]['data_center_id']
                            rack_results = self.execute_query("""
                                SELECT COUNT(*) as rack_count 
                                FROM racks
                                WHERE data_center_id = ?
                            """, (dc_id,))
                            
                            server_results = self.execute_query("""
                                SELECT COUNT(*) as server_count
                                FROM servers s
                                JOIN racks r ON s.rack_id = r.rack_id
                                WHERE r.data_center_id = ?
                            """, (dc_id,))
                            
                            if rack_results and server_results:
                                rack_count = rack_results[0]['rack_count']
                                server_count = server_results[0]['server_count']
                                
                                response += f"\nDetails:\n"
                                response += f"• Racks: {rack_count}\n"
                                response += f"• Servers: {server_count}\n"
                        
                        return response
                    return f"I don't have information about any data centers in {city.title()}."
            
            # Data center with most racks/servers (as capacity is not in our schema)
            if any(phrase in user_input for phrase in ["largest data center", "biggest data center"]):
                try:
                    results = self.execute_query("""
                        SELECT dc.name, l.city, l.country, COUNT(r.rack_id) as rack_count
                        FROM data_centers dc
                        JOIN locations l ON dc.location_id = l.location_id
                        JOIN racks r ON dc.data_center_id = r.data_center_id
                        GROUP BY dc.data_center_id
                        ORDER BY rack_count DESC
                        LIMIT 1
                    """)
                    
                    if results:
                        dc = results[0]
                        return f"The largest data center is {dc['name']} in {dc['city']}, {dc['country']} with {dc['rack_count']} racks."
                    else:
                        return "I couldn't determine which data center is the largest based on rack count."
                except Exception as e:
                    logger.error(f"Error determining largest data center: {e}")
                    return f"I encountered an error processing your request: {str(e)}. Please try asking in a different way."
            
            # Data center with fewest racks
            if any(phrase in user_input for phrase in ["smallest data center"]):
                try:
                    results = self.execute_query("""
                        SELECT dc.name, l.city, l.country, COUNT(r.rack_id) as rack_count
                        FROM data_centers dc
                        JOIN locations l ON dc.location_id = l.location_id
                        JOIN racks r ON dc.data_center_id = r.data_center_id
                        GROUP BY dc.data_center_id
                        ORDER BY rack_count ASC
                        LIMIT 1
                    """)
                    
                    if results:
                        dc = results[0]
                        return f"The smallest data center is {dc['name']} in {dc['city']}, {dc['country']} with only {dc['rack_count']} racks."
                    else:
                        return "I couldn't determine which data center is the smallest based on rack count."
                except Exception as e:
                    logger.error(f"Error determining smallest data center: {e}")
                    return f"I encountered an error processing your request: {str(e)}. Please try asking in a different way."
            
            # Advanced SQL query handling
            if user_input.startswith("sql:"):
                query = user_input[4:].strip()
                
                # Add support for params in advanced queries
                params = ()
                
                # Special handling for complex queries
                if "complex:" in query:
                    # Extract the complex query type
                    complex_query = query.split("complex:")[1].strip()
                    
                    if "server_usage_by_datacenter" in complex_query:
                        # A complex query to show server usage metrics by data center
                        query = """
                        SELECT 
                            dc.name as datacenter_name,
                            l.city, 
                            l.country,
                            COUNT(s.server_id) as server_count
                        FROM 
                            data_centers dc
                        JOIN
                            locations l ON dc.location_id = l.location_id
                        LEFT JOIN 
                            racks r ON dc.data_center_id = r.data_center_id
                        LEFT JOIN
                            servers s ON r.rack_id = s.rack_id
                        GROUP BY 
                            dc.data_center_id
                        ORDER BY 
                            server_count DESC
                        """
                    elif "server_model_analysis" in complex_query:
                        # A complex query to analyze server models across data centers
                        query = """
                        SELECT 
                            s.os as operating_system,
                            COUNT(s.server_id) as server_count,
                            GROUP_CONCAT(DISTINCT dc.name) as used_in_datacenters
                        FROM 
                            servers s
                        JOIN 
                            racks r ON s.rack_id = r.rack_id
                        JOIN
                            data_centers dc ON r.data_center_id = dc.data_center_id
                        GROUP BY 
                            s.os
                        ORDER BY 
                            server_count DESC
                        """
                    elif "search:" in complex_query:
                        # Extract search term
                        search_term = complex_query.split("search:")[1].strip()
                        query = """
                        SELECT 
                            'server' as type, 
                            s.hostname as name, 
                            s.os as detail, 
                            dc.name as datacenter
                        FROM 
                            servers s
                        JOIN 
                            racks r ON s.rack_id = r.rack_id
                        JOIN
                            data_centers dc ON r.data_center_id = dc.data_center_id
                        WHERE 
                            s.hostname LIKE ? OR s.os LIKE ? OR s.ip_address LIKE ?
                        UNION
                        SELECT 
                            'datacenter' as type, 
                            dc.name as name, 
                            l.city as detail, 
                            l.country as datacenter
                        FROM 
                            data_centers dc
                        JOIN
                            locations l ON dc.location_id = l.location_id
                        WHERE 
                            dc.name LIKE ? OR l.city LIKE ?
                        """
                        
                        search_pattern = f"%{search_term}%"
                        params = (search_pattern, search_pattern, search_pattern, search_pattern, search_pattern)
                
                # Execute the query
                results = self.execute_query(query, params)
                if isinstance(results, list) and len(results) > 0:
                    if 'error' in results[0]:
                        return f"Error executing your SQL query: {results[0]['error']}"
                    
                    # Format the response as a table for better readability
                    response = f"Query results ({len(results)} rows):\n\n"
                    
                    # Get headers from the first row
                    headers = list(results[0].keys())
                    
                    # Calculate column widths
                    col_widths = {header: len(header) for header in headers}
                    for row in results[:15]:  # Look at first 15 rows to determine column width
                        for header in headers:
                            width = len(str(row[header])) if row[header] is not None else 4  # 'None' width
                            col_widths[header] = max(col_widths[header], width)
                    
                    # Create header row
                    header_row = " | ".join(f"{header:{col_widths[header]}}" for header in headers)
                    separator = "-+-".join("-" * col_widths[header] for header in headers)
                    
                    response += header_row + "\n"
                    response += separator + "\n"
                    
                    # Create data rows
                    for i, row in enumerate(results[:15], 1):  # Limit to first 15 rows
                        data_row = " | ".join(f"{str(row[header]):{col_widths[header]}}" if row[header] is not None else "None" for header in headers)
                        response += data_row + "\n"
                    
                    if len(results) > 15:
                        response += f"\n...and {len(results) - 15} more rows."
                    
                    return response
                return "Your query returned no results."
            
            # Which cities have data centers?
            if any(phrase in user_input for phrase in ["which cities", "what cities", "cities with", "list cities"]) and "data center" in user_input:
                try:
                    results = self.execute_query("""
                        SELECT DISTINCT l.city, l.state, l.country, COUNT(dc.data_center_id) as dc_count
                        FROM locations l
                        JOIN data_centers dc ON l.location_id = dc.location_id
                        GROUP BY l.city, l.state, l.country
                        ORDER BY dc_count DESC
                    """)
                    
                    if not results:
                        return "I couldn't find any cities with data centers in our database."
                    
                    response = "Here are the cities that have data centers:\n\n"
                    for i, row in enumerate(results, 1):
                        state_info = f", {row['state']}" if row['state'] else ""
                        response += f"{i}. {row['city']}{state_info}, {row['country']} ({row['dc_count']} data center"
                        response += "s" if row['dc_count'] > 1 else ""
                        response += ")\n"
                    
                    return response
                except Exception as e:
                    logger.error(f"Error listing cities with data centers: {e}")
                    return f"I encountered an error processing your request: {str(e)}. Please try asking in a different way."
            
            # How many racks are in each data center?
            if "racks" in user_input and any(phrase in user_input for phrase in ["how many", "count", "number of"]) and "data center" in user_input:
                try:
                    results = self.execute_query("""
                        SELECT dc.name as data_center_name, COUNT(r.rack_id) as rack_count
                        FROM data_centers dc
                        LEFT JOIN racks r ON dc.data_center_id = r.data_center_id
                        GROUP BY dc.data_center_id
                        ORDER BY rack_count DESC
                    """)
                    
                    if not results:
                        return "I couldn't find any data on racks per data center."
                    
                    response = "Here's the number of racks in each data center:\n\n"
                    for i, row in enumerate(results, 1):
                        response += f"{i}. {row['data_center_name']}: {row['rack_count']} rack"
                        response += "s" if row['rack_count'] != 1 else ""
                        response += "\n"
                    
                    return response
                except Exception as e:
                    logger.error(f"Error counting racks by data center: {e}")
                    return f"I encountered an error processing your request: {str(e)}. Please try asking in a different way."
            
            # List servers with rack and data center info
            if "servers" in user_input and any(word in user_input for word in ["list", "show", "display"]) and any(phrase in user_input for phrase in ["rack", "data center"]):
                try:
                    results = self.execute_query("""
                        SELECT s.hostname, s.ip_address, s.os, r.rack_label, dc.name as data_center_name
                        FROM servers s
                        JOIN racks r ON s.rack_id = r.rack_id
                        JOIN data_centers dc ON r.data_center_id = dc.data_center_id
                        ORDER BY dc.name, r.rack_label, s.hostname
                    """)
                    
                    if not results:
                        return "I couldn't find any servers with rack and data center information."
                    
                    response = "Here are all servers with their rack and data center information:\n\n"
                    current_dc = None
                    current_rack = None
                    
                    for server in results:
                        # If we're starting a new data center section
                        if current_dc != server['data_center_name']:
                            current_dc = server['data_center_name']
                            response += f"\n📍 {current_dc} Data Center:\n"
                            current_rack = None
                        
                        # If we're starting a new rack section
                        if current_rack != server['rack_label']:
                            current_rack = server['rack_label']
                            response += f"  📦 Rack {current_rack}:\n"
                        
                        # Add server info
                        response += f"    • {server['hostname']} ({server['ip_address']}) - {server['os']}\n"
                    
                    return response
                except Exception as e:
                    logger.error(f"Error listing servers with rack and data center info: {e}")
                    return f"I encountered an error processing your request: {str(e)}. Please try asking in a different way."
            
            # Which servers run specific OS?
            if "servers" in user_input and "os" in user_input.lower() or "ubuntu" in user_input.lower() or "centos" in user_input.lower() or "windows" in user_input.lower():
                try:
                    os_query = None
                    if "ubuntu" in user_input.lower():
                        os_query = "Ubuntu%"
                    elif "centos" in user_input.lower():
                        os_query = "CentOS%"
                    elif "windows" in user_input.lower():
                        os_query = "Windows%"
                    
                    if os_query:
                        results = self.execute_query("""
                            SELECT s.hostname, s.ip_address, s.os, r.rack_label, dc.name as data_center_name
                            FROM servers s
                            JOIN racks r ON s.rack_id = r.rack_id
                            JOIN data_centers dc ON r.data_center_id = dc.data_center_id
                            WHERE s.os LIKE ?
                            ORDER BY dc.name, r.rack_label
                        """, (os_query,))
                        
                        if not results:
                            return f"I couldn't find any servers running {os_query.replace('%', '')} in our system."
                        
                        os_type = os_query.replace('%', '')
                        response = f"Here are all servers running {os_type}:\n\n"
                        
                        for i, server in enumerate(results, 1):
                            response += f"{i}. {server['hostname']} ({server['ip_address']})\n"
                            response += f"   • Data Center: {server['data_center_name']}\n"
                            response += f"   • Rack: {server['rack_label']}\n"
                            response += f"   • OS: {server['os']}\n\n"
                        
                        return response
                except Exception as e:
                    logger.error(f"Error filtering servers by OS: {e}")
                    return f"I encountered an error processing your request: {str(e)}. Please try asking in a different way."
            
            # User asking for help or examples
            if any(word in user_input for word in ["help", "examples", "what can you do", "capabilities"]):
                return (
                    "I have information about our data centers and servers. You can ask questions like:\n\n"
                    "Data Center Questions:\n"
                    "• How many data centers do we have?\n"
                    "• List all data centers\n"
                    "• Tell me about the Seattle data center\n"
                    "• Which cities have data centers?\n"
                    "• How many racks are in each data center?\n\n"
                    "Server Questions:\n"
                    "• List all servers along with their rack label and data center name\n"
                    "• Which servers are running Ubuntu OS?\n"
                    "• What server models do we use?\n"
                    "• What is our total server capacity?\n\n"
                    "Advanced SQL Queries (for technical users):\n"
                    "• SQL: SELECT * FROM data_centers\n"
                    "• SQL: SELECT * FROM servers WHERE os LIKE 'Ubuntu%'\n"
                    "\nFor complex queries with joins, just ask naturally and I'll translate to SQL."
                )
            
            # Servers in a specific data center
            if any(phrase in user_input for phrase in ["servers in", "servers at", "how many servers"]):
                cities = ["new york", "san francisco", "london"]
                for city in cities:
                    if city in user_input.lower():
                        try:
                            # Find data centers in this city first
                            dc_results = self.execute_query("""
                                SELECT dc.data_center_id, dc.name, l.city 
                                FROM data_centers dc
                                JOIN locations l ON dc.location_id = l.location_id
                                WHERE LOWER(l.city) LIKE ?
                            """, (f"%{city}%",))
                            
                            if not dc_results:
                                return f"I couldn't find any data centers in {city.title()}."
                                
                            # If there's more than one data center in this city, list them all
                            if len(dc_results) > 1:
                                response = f"There are {len(dc_results)} data centers in {city.title()}. Which one are you interested in?\n\n"
                                for i, dc in enumerate(dc_results, 1):
                                    response += f"{i}. {dc['name']}\n"
                                return response
                                
                            # Get servers in the data center
                            dc_id = dc_results[0]['data_center_id']
                            dc_name = dc_results[0]['name']
                            
                            server_results = self.execute_query("""
                                SELECT s.hostname, s.ip_address, s.os
                                FROM servers s
                                JOIN racks r ON s.rack_id = r.rack_id
                                WHERE r.data_center_id = ?
                            """, (dc_id,))
                            
                            count = len(server_results)
                            
                            if count > 0:
                                response = f"The {dc_name} data center in {city.title()} has {count} servers:\n\n"
                                
                                for i, server in enumerate(server_results, 1):
                                    response += f"{i}. {server['hostname']} ({server['ip_address']})\n"
                                    response += f"   • OS: {server['os']}\n\n"
                                
                                return response
                            else:
                                return f"The {dc_name} data center in {city.title()} has no servers registered in the system."
                        except Exception as e:
                            logger.error(f"Error getting servers for city {city}: {e}")
                            return f"I encountered an error getting server information: {str(e)}. Please try asking in a different way."
                
                # General server count across all data centers
                if "how many" in user_input:
                    try:
                        server_results = self.execute_query("""
                            SELECT COUNT(*) as count FROM servers
                        """)
                        
                        if server_results:
                            count = server_results[0]['count']
                            
                            # Count by OS
                            os_results = self.execute_query("""
                                SELECT os, COUNT(*) as count 
                                FROM servers 
                                GROUP BY os 
                                ORDER BY count DESC
                            """)
                            
                            response = f"We have a total of {count} servers across all data centers.\n\n"
                            
                            if os_results:
                                response += "Server OS breakdown:\n"
                                for os_row in os_results:
                                    response += f"• {os_row['os']}: {os_row['count']} servers\n"
                            
                            return response
                        else:
                            return "I couldn't get server count information."
                    except Exception as e:
                        logger.error(f"Error counting servers: {e}")
                        return f"I encountered an error counting servers: {str(e)}. Please try asking in a different way."
            
            # Total server count 
            if any(phrase in user_input for phrase in ["total server count", "combined servers", "all servers count"]):
                try:
                    results = self.execute_query("""
                        SELECT COUNT(*) as total FROM servers
                    """)
                    
                    if results:
                        count = results[0]['total']
                        return f"We have a total of {count} servers across all data centers."
                    else:
                        return "I couldn't determine the total number of servers."
                except Exception as e:
                    logger.error(f"Error getting total server count: {e}")
                    return f"I encountered an error processing your request: {str(e)}. Please try asking in a different way."
            
            # Server operating systems
            if any(phrase in user_input for phrase in ["server os", "operating systems", "what os", "os types"]):
                try:
                    results = self.execute_query("""
                        SELECT os, COUNT(*) as count 
                        FROM servers 
                        GROUP BY os 
                        ORDER BY count DESC
                    """)
                    
                    if results:
                        response = "Here are the operating systems used across our servers:\n\n"
                        for i, row in enumerate(results, 1):
                            response += f"{i}. {row['os']} ({row['count']} servers)\n"
                        
                        return response
                    else:
                        return "I couldn't find information about server operating systems."
                except Exception as e:
                    logger.error(f"Error listing server OS: {e}")
                    return f"I encountered an error processing your request: {str(e)}. Please try asking in a different way."
            
            # List all servers
            if any(phrase in user_input for phrase in ["list all servers", "show all servers", "all servers"]) and not "count" in user_input:
                try:
                    servers = self.execute_query("""
                        SELECT s.hostname, s.ip_address, s.os, dc.name as data_center_name
                        FROM servers s
                        JOIN racks r ON s.rack_id = r.rack_id
                        JOIN data_centers dc ON r.data_center_id = dc.data_center_id
                        ORDER BY dc.name, s.hostname
                    """)
                    
                    if servers:
                        response = "Here's a list of all servers across our data centers:\n\n"
                        current_dc = None
                        
                        for server in servers:
                            if current_dc != server['data_center_name']:
                                current_dc = server['data_center_name']
                                response += f"\n📍 {current_dc} Data Center:\n"
                            
                            response += f"• {server['hostname']} ({server['ip_address']}) - {server['os']}\n"
                        
                        return response
                    else:
                        return "There are no servers registered in the system."
                except Exception as e:
                    logger.error(f"Error listing all servers: {e}")
                    return f"I encountered an error processing your request: {str(e)}. Please try asking in a different way."
            
            # Generic fallback for data center questions
            if any(term in user_input for term in ["data center", "datacenter", "facility", "location", "server", "servers"]):
                return (
                    "I have information about our data centers and servers. "
                    "You can ask questions like:\n\n"
                    "• List all data centers\n"
                    "• Tell me about the Seattle data center\n"
                    "• How many servers are in the New York data center?\n"
                    "• What server models do we use?\n"
                    "• What is our total server capacity?"
                )
                
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            return f"I encountered an error processing your request: {str(e)}. Please try asking in a different way."
        
        # Default response
        return (
            "I'm not sure how to answer that question. I specialize in providing information about our data centers and servers. "
            "You can ask me about specific data centers, their servers, capacities, locations, or request a list of all data centers."
        )

# Initialize the data center chatbot
chatbot = DataCenterChatbot()

@app.route('/')
def index():
    """Render the main chat interface."""
    # Initialize session if needed
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    return render_template('index.html', chat_history=session['chat_history'])

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat interactions."""
    user_input = request.json.get('message', '')
    
    if not user_input:
        return jsonify({'error': 'No message provided'}), 400
    
    try:
        # Process the user input
        response = chatbot.process_input(user_input)
        
        # Update chat history
        if 'chat_history' not in session:
            session['chat_history'] = []
        
        session['chat_history'].append({
            'user': user_input,
            'bot': response
        })
        
        # Truncate history if it gets too long
        if len(session['chat_history']) > 20:
            session['chat_history'] = session['chat_history'][-20:]
        
        session.modified = True
        
        return jsonify({
            'response': response,
            'history': session['chat_history']
        })
    
    except Exception as e:
        logger.error(f"Error processing chat: {e}")
        return jsonify({
            'error': 'An error occurred processing your request',
            'details': str(e)
        }), 500

@app.route('/clear_history', methods=['POST'])
def clear_history():
    """Clear the chat history."""
    session['chat_history'] = []
    return jsonify({'status': 'success'})

@app.route('/static/images/<path:filename>')
def serve_static_images(filename):
    """Serve static images."""
    return send_from_directory(os.path.join(app.root_path, 'static', 'images'), filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)