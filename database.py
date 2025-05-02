"""
Database module for the Data Center Chatbot application.
Manages connections and queries to the database containing datacenter information.
"""

import sqlite3
import os
import logging
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages the database for data center information."""
    
    def __init__(self, db_path=None):
        """
        Initialize the database manager.
        
        Args:
            db_path (str, optional): Path to the SQLite database file
        """
        if db_path is None:
            # Use a default path in the data directory
            data_dir = Path('data')
            os.makedirs(data_dir, exist_ok=True)
            db_path = data_dir / 'datacenter.db'
            
        self.db_path = str(db_path)
        self._create_db_structure()
    
    def _create_db_structure(self):
        """Create the database structure and populate with sample data if needed."""
        # First, check if the database file exists
        if os.path.exists(self.db_path):
            # If it exists, try to check if it has data
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='locations'")
                if cursor.fetchone():
                    # Table exists, check if it has data
                    cursor.execute("SELECT COUNT(*) FROM locations")
                    if cursor.fetchone()[0] > 0:
                        # Has data, we're good
                        conn.close()
                        return
                conn.close()
            except sqlite3.Error:
                pass
                
        # Either the database doesn't exist or it doesn't have the right schema
        # Let's create a fresh one
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
        CREATE TABLE locations (
            location_id INTEGER PRIMARY KEY,
            city TEXT NOT NULL,
            state TEXT,
            country TEXT NOT NULL
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE data_centers (
            data_center_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            location_id INTEGER,
            FOREIGN KEY (location_id) REFERENCES locations (location_id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE racks (
            rack_id INTEGER PRIMARY KEY,
            rack_label TEXT NOT NULL,
            data_center_id INTEGER,
            FOREIGN KEY (data_center_id) REFERENCES data_centers (data_center_id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE servers (
            server_id INTEGER PRIMARY KEY,
            hostname TEXT NOT NULL,
            ip_address TEXT,
            rack_id INTEGER,
            os TEXT,
            FOREIGN KEY (rack_id) REFERENCES racks (rack_id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE network_devices (
            device_id INTEGER PRIMARY KEY,
            device_name TEXT NOT NULL,
            device_type TEXT,
            ip_address TEXT,
            data_center_id INTEGER,
            FOREIGN KEY (data_center_id) REFERENCES data_centers (data_center_id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE maintenance_logs (
            log_id INTEGER PRIMARY KEY,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            maintenance_date DATE NOT NULL,
            performed_by TEXT,
            notes TEXT
        )
        ''')
        
        # Insert sample data
        # Locations
        cursor.execute("INSERT INTO locations VALUES (1, 'New York', 'NY', 'USA')")
        cursor.execute("INSERT INTO locations VALUES (2, 'San Francisco', 'CA', 'USA')")
        cursor.execute("INSERT INTO locations VALUES (3, 'London', NULL, 'UK')")
        
        # Data Centers
        cursor.execute("INSERT INTO data_centers VALUES (1, 'NYC-01', 1)")
        cursor.execute("INSERT INTO data_centers VALUES (2, 'SFO-01', 2)")
        cursor.execute("INSERT INTO data_centers VALUES (3, 'LON-01', 3)")
        cursor.execute("INSERT INTO data_centers VALUES (4, 'LON-02', 3)")
        
        # Racks
        cursor.execute("INSERT INTO racks VALUES (1, 'R101', 1)")
        cursor.execute("INSERT INTO racks VALUES (2, 'R102', 1)")
        cursor.execute("INSERT INTO racks VALUES (3, 'R201', 2)")
        cursor.execute("INSERT INTO racks VALUES (4, 'R301', 3)")
        
        # Servers
        cursor.execute("INSERT INTO servers VALUES (1, 'web-01', '192.168.1.10', 1, 'Ubuntu 22.04')")
        cursor.execute("INSERT INTO servers VALUES (2, 'db-01', '192.168.1.11', 1, 'CentOS 8')")
        cursor.execute("INSERT INTO servers VALUES (3, 'app-01', '192.168.2.10', 3, 'Windows Server 2022')")
        cursor.execute("INSERT INTO servers VALUES (4, 'cache-01', '192.168.3.10', 4, 'Ubuntu 20.04')")
        
        # Network Devices
        cursor.execute("INSERT INTO network_devices VALUES (1, 'sw-nyc-01', 'Switch', '10.0.1.1', 1)")
        cursor.execute("INSERT INTO network_devices VALUES (2, 'fw-nyc-01', 'Firewall', '10.0.1.254', 1)")
        cursor.execute("INSERT INTO network_devices VALUES (3, 'sw-sfo-01', 'Switch', '10.0.2.1', 2)")
        cursor.execute("INSERT INTO network_devices VALUES (4, 'sw-lon-01', 'Switch', '10.0.3.1', 3)")
        
        # Maintenance Logs
        cursor.execute("INSERT INTO maintenance_logs VALUES (1, 'server', 1, '2023-01-15', 'John Doe', 'OS update')")
        cursor.execute("INSERT INTO maintenance_logs VALUES (2, 'network_device', 1, '2023-02-20', 'Jane Smith', 'Firmware update')")
        cursor.execute("INSERT INTO maintenance_logs VALUES (3, 'server', 3, '2023-03-10', 'John Doe', 'Hardware replacement')")

        conn.commit()
        conn.close()
        logger.info(f"Created database structure and populated with sample data in {self.db_path}")
    
    def execute_query(self, query, params=()):
        """
        Execute an SQL query and return the results.
        
        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query
            
        Returns:
            list: List of dictionaries representing rows
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            results = [dict(row) for row in rows]
            
            conn.close()
            return results
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            raise
    
    def execute_pandas_query(self, query, params=()):
        """
        Execute an SQL query and return the results as a pandas DataFrame.
        
        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query
            
        Returns:
            pandas.DataFrame: Results as a DataFrame
        """
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            return df
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            raise
    
    def get_schema_info(self):
        """
        Get a human-readable description of the database schema.
        
        Returns:
            str: Formatted schema information
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()
        
        schema_info = "Database Schema:\n\n"
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            schema_info += f"Table: {table_name}\n"
            schema_info += "Columns:\n"
            
            for col in columns:
                # col format: (id, name, type, notnull, default, pk)
                col_name = col[1]
                col_type = col[2]
                is_pk = "PRIMARY KEY" if col[5] == 1 else ""
                is_not_null = "NOT NULL" if col[3] == 1 else ""
                
                schema_info += f"  - {col_name} ({col_type}) {is_pk} {is_not_null}\n"
            
            schema_info += "\n"
        
        conn.close()
        return schema_info

# Test the module if run directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db_manager = DatabaseManager()
    print(db_manager.get_schema_info())
    
    # Test a simple query
    results = db_manager.execute_query("SELECT * FROM data_centers")
    for row in results:
        print(row)