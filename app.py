"""
Flask web application for the Data Center Chatbot.
"""

import os
import logging
from flask import Flask, render_template, request, jsonify, session, send_from_directory
import pandas as pd
import numpy as np
import requests
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app and SQLAlchemy database
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure the database with PostgreSQL
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

# Import models for initializing the database
with app.app_context():
    import models
    db.create_all()
    
    # Add sample data if no data exists
    from models import Location, DataCenter, Rack, Server, NetworkDevice, MaintenanceLog
    if not Location.query.first():
        logger.info("No data found. Populating database with sample data.")
        
        # Add locations
        locations = [
            Location(location_id=1, city='New York', state='NY', country='USA'),
            Location(location_id=2, city='San Francisco', state='CA', country='USA'),
            Location(location_id=3, city='London', state=None, country='UK')
        ]
        db.session.add_all(locations)
        db.session.commit()
        
        # Add data centers
        data_centers = [
            DataCenter(data_center_id=1, name='NYC-01', location_id=1),
            DataCenter(data_center_id=2, name='SFO-01', location_id=2),
            DataCenter(data_center_id=3, name='LON-01', location_id=3),
            DataCenter(data_center_id=4, name='LON-02', location_id=3)
        ]
        db.session.add_all(data_centers)
        db.session.commit()
        
        # Add racks
        racks = [
            Rack(rack_id=1, rack_label='R101', data_center_id=1),
            Rack(rack_id=2, rack_label='R102', data_center_id=1),
            Rack(rack_id=3, rack_label='R201', data_center_id=2),
            Rack(rack_id=4, rack_label='R301', data_center_id=3)
        ]
        db.session.add_all(racks)
        db.session.commit()
        
        # Add servers
        from datetime import datetime
        servers = [
            Server(server_id=1, hostname='web-01', ip_address='192.168.1.10', rack_id=1, os='Ubuntu 22.04'),
            Server(server_id=2, hostname='db-01', ip_address='192.168.1.11', rack_id=1, os='CentOS 8'),
            Server(server_id=3, hostname='app-01', ip_address='192.168.2.10', rack_id=3, os='Windows Server 2022'),
            Server(server_id=4, hostname='cache-01', ip_address='192.168.3.10', rack_id=4, os='Ubuntu 20.04')
        ]
        db.session.add_all(servers)
        db.session.commit()
        
        # Add network devices
        network_devices = [
            NetworkDevice(device_id=1, device_name='sw-nyc-01', device_type='Switch', ip_address='10.0.1.1', data_center_id=1),
            NetworkDevice(device_id=2, device_name='fw-nyc-01', device_type='Firewall', ip_address='10.0.1.254', data_center_id=1),
            NetworkDevice(device_id=3, device_name='sw-sfo-01', device_type='Switch', ip_address='10.0.2.1', data_center_id=2),
            NetworkDevice(device_id=4, device_name='sw-lon-01', device_type='Switch', ip_address='10.0.3.1', data_center_id=3)
        ]
        db.session.add_all(network_devices)
        db.session.commit()
        
        # Add maintenance logs
        import datetime
        maintenance_logs = [
            MaintenanceLog(log_id=1, entity_type='server', entity_id=1, maintenance_date=datetime.date(2023, 1, 15), performed_by='John Doe', notes='OS update'),
            MaintenanceLog(log_id=2, entity_type='network_device', entity_id=1, maintenance_date=datetime.date(2023, 2, 20), performed_by='Jane Smith', notes='Firmware update'),
            MaintenanceLog(log_id=3, entity_type='server', entity_id=3, maintenance_date=datetime.date(2023, 3, 10), performed_by='John Doe', notes='Hardware replacement')
        ]
        db.session.add_all(maintenance_logs)
        db.session.commit()
        
        logger.info("Sample data added to the database.")

class DataCenterChatbot:
    """An enhanced chatbot for interacting with the data center database."""
    
    def __init__(self):
        """Initialize the chatbot with a question processor."""
        from question_processor import QuestionProcessor
        self.processor = QuestionProcessor()
        self.schema_info = self.get_schema_info()
        logger.info("Data Center Chatbot initialized with database connection")
    
    def get_schema_info(self):
        """Get database schema information."""
        # Use SQLAlchemy models to describe the schema
        schema_info = "Database Schema:\n\n"
        
        # Add info for each table
        from models import Location, DataCenter, Rack, Server, NetworkDevice, MaintenanceLog
        models = [Location, DataCenter, Rack, Server, NetworkDevice, MaintenanceLog]
        
        for model in models:
            schema_info += f"Table: {model.__tablename__}\n"
            schema_info += "Columns:\n"
            
            for column in model.__table__.columns:
                primary_key = "PRIMARY KEY" if column.primary_key else ""
                nullable = "" if column.nullable else "NOT NULL"
                foreign_key = ""
                if column.foreign_keys:
                    for fk in column.foreign_keys:
                        foreign_key = f"REFERENCES {fk.target_fullname}"
                
                schema_info += f"  - {column.name} ({column.type}) {primary_key} {nullable} {foreign_key}\n"
            
            schema_info += "\n"
        
        return schema_info
    
    def process_input(self, user_input):
        """Process user input and generate a response based on database information."""
        user_input = user_input.strip()
        
        # Handle greetings and farewells
        greetings = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']
        farewells = ['bye', 'goodbye', 'see you', 'talk to you later', 'thanks']
        
        if any(greeting in user_input.lower() for greeting in greetings):
            return "Hello! I'm your data center assistant. I can provide information about our data centers, servers, and infrastructure. How can I help you today?"
        
        if any(farewell in user_input.lower() for farewell in farewells):
            return "Goodbye! Feel free to chat again when you need information about our data centers."
        
        # Process the question using the question processor
        try:
            return self.processor.process_question(user_input)
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            
            # If something goes wrong, provide a helpful fallback message
            examples = [
                "Which cities have data centers?",
                "How many data centers are in each country?",
                "List all servers along with their rack and data center.",
                "Which servers are running Ubuntu?",
                "How many network devices are in each data center?",
                "Which entities had maintenance performed by John Doe?",
                "Show all entities that have never had maintenance."
            ]
            
            help_message = "I encountered an error processing your request. Here are some examples of questions I can answer:\n\n"
            for i, example in enumerate(examples, 1):
                help_message += f"{i}. {example}\n"
            
            return help_message

# Initialize the chatbot
chatbot = DataCenterChatbot()

# Routes
@app.route('/')
def index():
    """Render the main chat interface."""
    # Clear any existing session data for a fresh start
    if 'chat_history' not in session:
        session['chat_history'] = []
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat interactions."""
    user_input = request.json.get('message', '').strip()
    
    if not user_input:
        return jsonify({'response': 'Please enter a message.'})
    
    # Process the user input through the chatbot
    response = chatbot.process_input(user_input)
    
    # Store the interaction in session
    if 'chat_history' not in session:
        session['chat_history'] = []
    session['chat_history'].append({'user': user_input, 'bot': response})
    session.modified = True
    
    return jsonify({'response': response})

@app.route('/clear', methods=['POST'])
def clear_history():
    """Clear the chat history."""
    session['chat_history'] = []
    return jsonify({'status': 'success'})

@app.route('/images/<filename>')
def serve_static_images(filename):
    """Serve static images."""
    return send_from_directory('static/images', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)