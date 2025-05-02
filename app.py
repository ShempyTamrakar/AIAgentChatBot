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
        
        # Handle greetings and farewells
        greetings = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']
        farewells = ['bye', 'goodbye', 'see you', 'talk to you later', 'thanks']
        
        if any(greeting in user_input for greeting in greetings):
            return "Hello! I'm your data center assistant. I can provide information about our data centers, servers, and infrastructure. How can I help you today?"
        
        if any(farewell in user_input for farewell in farewells):
            return "Goodbye! Feel free to chat again when you need information about our data centers."
        
        # Handle questions about data centers
        try:
            # Count of data centers
            if any(phrase in user_input for phrase in ["how many data centers", "number of data centers", "count of data centers"]):
                results = self.execute_query("SELECT COUNT(*) as count FROM data_centers")
                count = results[0]['count']
                return f"We currently have {count} data centers in our system."
            
            # List all data centers
            if any(phrase in user_input for phrase in ["list all data centers", "show all data centers", "what data centers", "which data centers"]):
                results = self.execute_query("SELECT name, location, capacity_kw, tier FROM data_centers ORDER BY name")
                if not results:
                    return "I couldn't find any data centers in our system."
                
                response = "Here are all our data centers:\n\n"
                for i, dc in enumerate(results, 1):
                    response += f"{i}. {dc['name']} in {dc['location']}\n   - Capacity: {dc['capacity_kw']} kW\n   - Tier: {dc['tier']}\n"
                return response
            
            # Information about a specific data center by location
            locations = ["seattle", "austin", "new york", "san francisco", "chicago"]
            for location in locations:
                if location in user_input:
                    results = self.execute_query(
                        "SELECT * FROM data_centers WHERE location LIKE ?", 
                        (f"%{location.title()}%",)
                    )
                    if results:
                        dc = results[0]
                        return f"📍 {dc['name']} Data Center in {dc['location']}:\n\n" \
                               f"• Capacity: {dc['capacity_kw']} kW\n" \
                               f"• Tier Level: {dc['tier']}\n" \
                               f"• Commissioned: {dc['commissioned_date']}\n" \
                               f"• Last Audit: {dc['last_audit_date']}\n"
            
            # Data center with highest capacity
            if any(phrase in user_input for phrase in ["highest capacity", "most powerful", "largest data center"]):
                results = self.execute_query(
                    "SELECT name, location, capacity_kw FROM data_centers ORDER BY capacity_kw DESC LIMIT 1"
                )
                if results:
                    dc = results[0]
                    return f"The data center with the highest capacity is {dc['name']} in {dc['location']} with {dc['capacity_kw']} kW capacity."
            
            # Data center with lowest capacity
            if any(phrase in user_input for phrase in ["lowest capacity", "smallest data center"]):
                results = self.execute_query(
                    "SELECT name, location, capacity_kw FROM data_centers ORDER BY capacity_kw ASC LIMIT 1"
                )
                if results:
                    dc = results[0]
                    return f"The data center with the lowest capacity is {dc['name']} in {dc['location']} with {dc['capacity_kw']} kW capacity."
            
            # Newest data center
            if any(phrase in user_input for phrase in ["newest data center", "most recent", "latest data center"]):
                results = self.execute_query(
                    "SELECT name, location, commissioned_date FROM data_centers ORDER BY commissioned_date DESC LIMIT 1"
                )
                if results:
                    dc = results[0]
                    return f"The newest data center is {dc['name']} in {dc['location']}, commissioned on {dc['commissioned_date']}."
            
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
                            d.name as datacenter_name,
                            d.location,
                            COUNT(s.id) as server_count,
                            SUM(s.cpu_cores) as total_cpu_cores,
                            SUM(s.ram_gb) as total_ram_gb,
                            SUM(s.storage_tb) as total_storage_tb,
                            COUNT(CASE WHEN s.status = 'active' THEN 1 END) as active_servers,
                            COUNT(CASE WHEN s.status = 'maintenance' THEN 1 END) as maintenance_servers,
                            COUNT(CASE WHEN s.status = 'standby' THEN 1 END) as standby_servers,
                            COUNT(CASE WHEN s.status = 'decommissioned' THEN 1 END) as decommissioned_servers
                        FROM 
                            data_centers d
                        LEFT JOIN 
                            servers s ON d.id = s.datacenter_id
                        GROUP BY 
                            d.id
                        ORDER BY 
                            server_count DESC
                        """
                    elif "server_model_analysis" in complex_query:
                        # A complex query to analyze server models across data centers
                        query = """
                        SELECT 
                            s.model,
                            COUNT(s.id) as server_count,
                            AVG(s.cpu_cores) as avg_cpu_cores,
                            AVG(s.ram_gb) as avg_ram_gb,
                            AVG(s.storage_tb) as avg_storage_tb,
                            GROUP_CONCAT(DISTINCT d.name) as used_in_datacenters
                        FROM 
                            servers s
                        JOIN 
                            data_centers d ON s.datacenter_id = d.id
                        GROUP BY 
                            s.model
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
                            s.model as detail, 
                            d.name as datacenter
                        FROM 
                            servers s
                        JOIN 
                            data_centers d ON s.datacenter_id = d.id
                        WHERE 
                            s.hostname LIKE ? OR s.model LIKE ? OR s.ip_address LIKE ?
                        UNION
                        SELECT 
                            'datacenter' as type, 
                            d.name as name, 
                            d.location as detail, 
                            CAST(d.capacity_kw AS TEXT) || ' kW' as datacenter
                        FROM 
                            data_centers d
                        WHERE 
                            d.name LIKE ? OR d.location LIKE ?
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
            
            # User asking for help or examples
            if any(word in user_input for word in ["help", "examples", "what can you do", "capabilities"]):
                return (
                    "I can answer questions about our data centers and servers. Here are some examples of what you can ask:\n\n"
                    "Data Center Questions:\n"
                    "• How many data centers do we have?\n"
                    "• List all data centers\n"
                    "• Tell me about the Seattle data center\n"
                    "• Which data center has the highest capacity?\n\n"
                    "Server Questions:\n"
                    "• How many servers do we have in total?\n"
                    "• What server models do we use?\n"
                    "• List servers in the New York data center\n"
                    "• What is our total server capacity?\n\n"
                    "Advanced SQL Queries (for technical users):\n"
                    "• SQL: SELECT * FROM data_centers\n"
                    "• SQL: complex:server_usage_by_datacenter\n"
                    "• SQL: complex:server_model_analysis\n"
                    "• SQL: complex:search:Dell\n"
                    "\nThese complex queries provide detailed analytics and search capabilities."
                )
            
            # Servers in a specific data center
            if any(phrase in user_input for phrase in ["servers in", "servers at", "how many servers"]):
                for location in locations:
                    if location in user_input:
                        dc_results = self.execute_query(
                            "SELECT id, name FROM data_centers WHERE location LIKE ?", 
                            (f"%{location.title()}%",)
                        )
                        if dc_results:
                            dc_id = dc_results[0]['id']
                            dc_name = dc_results[0]['name']
                            
                            server_results = self.execute_query(
                                "SELECT COUNT(*) as count FROM servers WHERE datacenter_id = ?",
                                (dc_id,)
                            )
                            
                            count = server_results[0]['count']
                            
                            if count > 0:
                                servers = self.execute_query(
                                    "SELECT hostname, model, cpu_cores, ram_gb, storage_tb, status FROM servers WHERE datacenter_id = ?",
                                    (dc_id,)
                                )
                                
                                response = f"The {dc_name} data center in {location.title()} has {count} servers:\n\n"
                                
                                for i, server in enumerate(servers, 1):
                                    response += f"{i}. {server['hostname']}\n"
                                    response += f"   • Model: {server['model']}\n"
                                    response += f"   • CPU: {server['cpu_cores']} cores\n"
                                    response += f"   • RAM: {server['ram_gb']} GB\n"
                                    response += f"   • Storage: {server['storage_tb']} TB\n"
                                    response += f"   • Status: {server['status']}\n\n"
                                
                                return response
                            else:
                                return f"The {dc_name} data center in {location.title()} has no servers registered in the system."
                
                # General server count across all data centers
                if "how many" in user_input:
                    server_results = self.execute_query("SELECT COUNT(*) as count FROM servers")
                    count = server_results[0]['count']
                    
                    if count > 0:
                        # Count by status
                        status_results = self.execute_query(
                            "SELECT status, COUNT(*) as count FROM servers GROUP BY status ORDER BY count DESC"
                        )
                        
                        response = f"We have a total of {count} servers across all data centers.\n\n"
                        response += "Server status breakdown:\n"
                        for status in status_results:
                            response += f"• {status['status']}: {status['count']} servers\n"
                        
                        return response
                    else:
                        return "There are no servers registered in the system."
            
            # Total server capacity
            if any(phrase in user_input for phrase in ["total capacity", "total server capacity", "combined capacity"]):
                results = self.execute_query(
                    "SELECT SUM(cpu_cores) as total_cpu, SUM(ram_gb) as total_ram, SUM(storage_tb) as total_storage FROM servers"
                )
                
                if results[0]['total_cpu']:
                    return (
                        f"Our total server capacity across all data centers is:\n\n"
                        f"• CPU: {results[0]['total_cpu']} cores\n"
                        f"• RAM: {results[0]['total_ram']} GB\n"
                        f"• Storage: {results[0]['total_storage']} TB"
                    )
            
            # Server models
            if any(phrase in user_input for phrase in ["server models", "models of servers", "what server models", "server types"]):
                results = self.execute_query(
                    "SELECT model, COUNT(*) as count FROM servers GROUP BY model ORDER BY count DESC"
                )
                
                if results:
                    response = "Here are the server models used across our data centers:\n\n"
                    for i, row in enumerate(results, 1):
                        response += f"{i}. {row['model']} ({row['count']} servers)\n"
                    
                    return response
            
            # List all servers
            if any(phrase in user_input for phrase in ["list all servers", "show all servers", "all servers"]):
                servers = self.execute_query("""
                    SELECT s.hostname, s.model, s.status, s.cpu_cores, s.ram_gb, d.name as datacenter
                    FROM servers s
                    JOIN data_centers d ON s.datacenter_id = d.id
                    ORDER BY d.name, s.hostname
                """)
                
                if servers:
                    response = "Here's a list of all servers across our data centers:\n\n"
                    current_dc = None
                    
                    for server in servers:
                        if current_dc != server['datacenter']:
                            current_dc = server['datacenter']
                            response += f"\n📍 {current_dc}:\n"
                        
                        response += f"• {server['hostname']} ({server['model']}) - {server['status']}\n"
                    
                    return response
                else:
                    return "There are no servers registered in the system."
            
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)