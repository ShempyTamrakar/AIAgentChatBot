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
class SimpleChatbot:
    """A simplified chatbot that simulates RAG functionality."""
    
    def __init__(self):
        self.database = self._initialize_database()
        
    def _initialize_database(self):
        """Create a simple in-memory database."""
        # Data centers table
        data_centers = pd.DataFrame({
            'id': range(1, 6),
            'name': ['DC-North-1', 'DC-South-1', 'DC-East-1', 'DC-West-1', 'DC-Central-1'],
            'location': ['Seattle, WA', 'Austin, TX', 'New York, NY', 'San Francisco, CA', 'Chicago, IL'],
            'capacity_kw': [5000.0, 3500.0, 6000.0, 4500.0, 4000.0],
            'tier': [4, 3, 4, 3, 3],
            'commissioned_date': ['2018-06-15', '2019-03-22', '2017-09-01', '2020-01-10', '2019-07-05'],
            'last_audit_date': ['2023-01-10', '2022-11-05', '2023-02-15', '2022-12-20', '2023-01-25']
        })
        
        return {'data_centers': data_centers}
    
    def get_schema_info(self):
        """Get database schema information."""
        schema_info = "Database Schema:\n\n"
        schema_info += "Table: data_centers\n"
        schema_info += "Columns:\n"
        schema_info += "  - id (INTEGER) PRIMARY KEY\n"
        schema_info += "  - name (TEXT) NOT NULL\n"
        schema_info += "  - location (TEXT) NOT NULL\n"
        schema_info += "  - capacity_kw (REAL) NOT NULL\n"
        schema_info += "  - tier (INTEGER) NOT NULL\n"
        schema_info += "  - commissioned_date (TEXT) NOT NULL\n"
        schema_info += "  - last_audit_date (TEXT)\n"
        return schema_info
    
    def execute_query(self, query):
        """Execute a query on the in-memory database."""
        # Very basic query handling
        query = query.lower()
        
        if "select * from data_centers" in query:
            return self.database['data_centers'].to_dict('records')
        
        if "select count(*) from data_centers" in query:
            return [{'count': len(self.database['data_centers'])}]
        
        # More specific queries
        if "seattle" in query or "dc-north-1" in query:
            return self.database['data_centers'][self.database['data_centers']['name'] == 'DC-North-1'].to_dict('records')
        
        # Default response if query not recognized
        return [{"result": "Query not recognized"}]
    
    def process_input(self, user_input):
        """Process user input and generate a response."""
        user_input = user_input.lower()
        
        # Handle greetings
        greetings = ['hi', 'hello', 'hey', 'greetings']
        if any(greeting in user_input for greeting in greetings):
            return "Hello! I'm your data center assistant. How can I help you today?"
        
        # Handle data center questions
        if "data center" in user_input or "datacenter" in user_input:
            if "how many" in user_input:
                result = self.execute_query("SELECT COUNT(*) FROM data_centers")
                return f"We have {result[0]['count']} data centers in our system."
            
            if "list" in user_input or "show" in user_input:
                results = self.execute_query("SELECT * FROM data_centers")
                response = "Here are our data centers:\n"
                for dc in results:
                    response += f"- {dc['name']} in {dc['location']} (Tier {dc['tier']})\n"
                return response
            
            if "seattle" in user_input:
                results = self.execute_query("Seattle query")
                if results:
                    dc = results[0]
                    return f"{dc['name']} in {dc['location']} has a capacity of {dc['capacity_kw']} kW and is a Tier {dc['tier']} facility."
        
        # Default response
        return "I'm not sure how to answer that. You can ask me about our data centers, their locations, capacities, and other details."

# Initialize the simplified chatbot
chatbot = SimpleChatbot()

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