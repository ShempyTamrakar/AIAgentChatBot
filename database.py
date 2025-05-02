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