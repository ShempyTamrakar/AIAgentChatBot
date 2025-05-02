"""
Flask web application for the Data Center Chatbot.
"""

import os
import logging
from flask import Flask, render_template, request, jsonify, session
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
    
    def execute_query(self, query):
        """Execute a SQL query against the database."""
        try:
            return self.db_manager.execute_query(query)
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
            
            # Direct SQL query handling (only for advanced users)
            if user_input.startswith("sql:"):
                query = user_input[4:].strip()
                results = self.execute_query(query)
                if isinstance(results, list) and len(results) > 0:
                    if 'error' in results[0]:
                        return f"Error executing your SQL query: {results[0]['error']}"
                    
                    response = f"Query results ({len(results)} rows):\n\n"
                    for i, row in enumerate(results[:10], 1):  # Limit to first 10 rows
                        response += f"Row {i}:\n"
                        for key, value in row.items():
                            response += f"  {key}: {value}\n"
                        response += "\n"
                    
                    if len(results) > 10:
                        response += f"...and {len(results) - 10} more rows."
                    
                    return response
                return "Your query returned no results."
            
            # User asking for help or examples
            if any(word in user_input for word in ["help", "examples", "what can you do", "capabilities"]):
                return (
                    "I can answer questions about our data centers. Here are some examples of what you can ask:\n\n"
                    "• How many data centers do we have?\n"
                    "• List all data centers\n"
                    "• Tell me about the Seattle data center\n"
                    "• Which data center has the highest capacity?\n"
                    "• What is the newest data center?\n\n"
                    "You can also execute SQL queries by prefixing them with 'SQL:' (for advanced users)."
                )
            
            # Generic fallback for data center questions
            if any(term in user_input for term in ["data center", "datacenter", "facility", "location"]):
                return (
                    "I have information about our data centers including their locations, capacities, and tier levels. "
                    "Please try asking a more specific question, such as 'list all data centers' or 'tell me about the Seattle data center'."
                )
                
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            return "I encountered an error processing your request. Please try asking in a different way."
        
        # Default response
        return (
            "I'm not sure how to answer that question. I specialize in providing information about our data centers. "
            "You can ask me about specific data centers, their capacities, locations, or request a list of all data centers."
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