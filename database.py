"""
Database module for the Data Center Chatbot application.
This simplified version uses SQLite to store data center information.
"""

import sqlite3
import os
import logging
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages the SQLite database for data center information."""
    
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
        self._create_tables_if_not_exist()
        self._check_and_populate_sample_data()
    
    def _create_tables_if_not_exist(self):
        """Create database tables if they don't exist already."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create data centers table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_centers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            capacity_kw REAL NOT NULL,
            tier INTEGER NOT NULL,
            commissioned_date TEXT NOT NULL,
            last_audit_date TEXT
        )
        ''')
        
        # Create servers table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS servers (
            id INTEGER PRIMARY KEY,
            datacenter_id INTEGER NOT NULL,
            hostname TEXT NOT NULL,
            ip_address TEXT NOT NULL,
            model TEXT NOT NULL,
            cpu_cores INTEGER NOT NULL,
            ram_gb INTEGER NOT NULL,
            storage_tb REAL NOT NULL,
            status TEXT NOT NULL,
            commissioned_date TEXT NOT NULL,
            FOREIGN KEY (datacenter_id) REFERENCES data_centers (id)
        )
        ''')
        
        # Create network devices table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS network_devices (
            id INTEGER PRIMARY KEY,
            datacenter_id INTEGER NOT NULL,
            device_name TEXT NOT NULL,
            device_type TEXT NOT NULL,
            ip_address TEXT NOT NULL,
            manufacturer TEXT NOT NULL,
            model TEXT NOT NULL,
            firmware_version TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (datacenter_id) REFERENCES data_centers (id)
        )
        ''')
        
        # Create power usage table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS power_usage (
            id INTEGER PRIMARY KEY,
            datacenter_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            power_kw REAL NOT NULL,
            pue REAL NOT NULL,
            FOREIGN KEY (datacenter_id) REFERENCES data_centers (id)
        )
        ''')
        
        # Create maintenance logs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS maintenance_logs (
            id INTEGER PRIMARY KEY,
            datacenter_id INTEGER NOT NULL,
            maintenance_date TEXT NOT NULL,
            maintenance_type TEXT NOT NULL,
            description TEXT NOT NULL,
            technician TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (datacenter_id) REFERENCES data_centers (id)
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Created database tables in {self.db_path}")
    
    def _check_and_populate_sample_data(self):
        """Check if database has data and populate with sample data if needed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if data_centers table has any rows
        cursor.execute("SELECT COUNT(*) FROM data_centers")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Add sample data centers
            data_centers = [
                ("DC-North-1", "Seattle, WA", 5000.0, 4, "2018-06-15", "2023-01-10"),
                ("DC-South-1", "Austin, TX", 3500.0, 3, "2019-03-22", "2022-11-05"),
                ("DC-East-1", "New York, NY", 6000.0, 4, "2017-09-01", "2023-02-15"),
                ("DC-West-1", "San Francisco, CA", 4500.0, 3, "2020-01-10", "2022-12-20"),
                ("DC-Central-1", "Chicago, IL", 4000.0, 3, "2019-07-05", "2023-01-25")
            ]
            
            cursor.executemany(
                "INSERT INTO data_centers (name, location, capacity_kw, tier, commissioned_date, last_audit_date) VALUES (?, ?, ?, ?, ?, ?)",
                data_centers
            )
            
            # Check if servers table exists and has any rows
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='servers'")
            table_exists = cursor.fetchone() is not None
            
            if table_exists:
                cursor.execute("SELECT COUNT(*) FROM servers")
                server_count = cursor.fetchone()[0]
                
                if server_count == 0:
                    # Get data center IDs for foreign key references
                    cursor.execute("SELECT id, name FROM data_centers")
                    dc_ids = {name: id for id, name in cursor.fetchall()}
                    
                    # Add sample servers for each data center
                    servers = [
                        # Seattle servers
                        (dc_ids["DC-North-1"], "srv-sea-001", "10.1.1.1", "Dell PowerEdge R740", 32, 256, 10.0, "active", "2020-03-15"),
                        (dc_ids["DC-North-1"], "srv-sea-002", "10.1.1.2", "Dell PowerEdge R740", 32, 256, 10.0, "active", "2020-03-15"),
                        (dc_ids["DC-North-1"], "srv-sea-003", "10.1.1.3", "HP ProLiant DL380", 48, 512, 20.0, "active", "2021-05-10"),
                        
                        # Austin servers
                        (dc_ids["DC-South-1"], "srv-aus-001", "10.2.1.1", "Lenovo ThinkSystem SR650", 24, 128, 5.0, "active", "2019-06-22"),
                        (dc_ids["DC-South-1"], "srv-aus-002", "10.2.1.2", "Lenovo ThinkSystem SR650", 24, 128, 5.0, "maintenance", "2019-06-22"),
                        
                        # New York servers
                        (dc_ids["DC-East-1"], "srv-nyc-001", "10.3.1.1", "Dell PowerEdge R840", 64, 1024, 30.0, "active", "2018-10-05"),
                        (dc_ids["DC-East-1"], "srv-nyc-002", "10.3.1.2", "Dell PowerEdge R840", 64, 1024, 30.0, "active", "2018-10-05"),
                        (dc_ids["DC-East-1"], "srv-nyc-003", "10.3.1.3", "Cisco UCS C240 M5", 40, 512, 15.0, "standby", "2019-04-15"),
                        (dc_ids["DC-East-1"], "srv-nyc-004", "10.3.1.4", "Cisco UCS C240 M5", 40, 512, 15.0, "active", "2019-04-15"),
                        
                        # San Francisco servers
                        (dc_ids["DC-West-1"], "srv-sfo-001", "10.4.1.1", "HP ProLiant DL380", 32, 256, 10.0, "active", "2020-02-20"),
                        (dc_ids["DC-West-1"], "srv-sfo-002", "10.4.1.2", "HP ProLiant DL380", 32, 256, 10.0, "decommissioned", "2020-02-20"),
                        
                        # Chicago servers
                        (dc_ids["DC-Central-1"], "srv-chi-001", "10.5.1.1", "Supermicro SuperServer", 16, 128, 8.0, "active", "2020-01-10"),
                        (dc_ids["DC-Central-1"], "srv-chi-002", "10.5.1.2", "Supermicro SuperServer", 16, 128, 8.0, "active", "2020-01-10"),
                    ]
                    
                    cursor.executemany(
                        "INSERT INTO servers (datacenter_id, hostname, ip_address, model, cpu_cores, ram_gb, storage_tb, status, commissioned_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        servers
                    )
                    
                    logger.info(f"Populated database with {len(servers)} sample servers")
            
            conn.commit()
            logger.info(f"Populated database with {len(data_centers)} sample data centers")
        
        conn.close()
    
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
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
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