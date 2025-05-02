"""
Database module for the chatbot application.
Manages connections and queries to the SQLite database containing datacenter information.
"""

import logging
import sqlite3
from typing import List, Dict, Any, Tuple, Optional
import os
import pandas as pd

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages connections and queries to the SQLite database.
    """
    
    def __init__(self, db_path: str):
        """
        Initialize the database manager.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        self._create_db_if_not_exists()
        self.tables_info = self._get_tables_info()
        
        logger.info(f"Database manager initialized with database at {db_path}")
        logger.info(f"Found {len(self.tables_info)} tables in the database")
        
    def _create_db_if_not_exists(self):
        """Create the database and tables if they don't exist already"""
        if not os.path.exists(self.db_path):
            logger.info(f"Database file not found. Creating new database at {self.db_path}")
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create basic data center tables
            cursor.execute('''
            CREATE TABLE data_centers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                location TEXT NOT NULL,
                capacity_kw REAL NOT NULL,
                tier INTEGER NOT NULL,
                commissioned_date TEXT NOT NULL,
                last_audit_date TEXT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE servers (
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
            
            cursor.execute('''
            CREATE TABLE network_devices (
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
            
            cursor.execute('''
            CREATE TABLE power_usage (
                id INTEGER PRIMARY KEY,
                datacenter_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                power_kw REAL NOT NULL,
                pue REAL NOT NULL,
                FOREIGN KEY (datacenter_id) REFERENCES data_centers (id)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE maintenance_logs (
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
            
            logger.info("Created new database with tables: data_centers, servers, network_devices, power_usage, maintenance_logs")
    
    def _get_tables_info(self) -> Dict[str, List[str]]:
        """
        Get information about tables in the database.
        
        Returns:
            Dict[str, List[str]]: Dictionary mapping table names to their column names
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        tables_info = {}
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            tables_info[table_name] = [col[1] for col in columns]  # col[1] is the column name
            
        conn.close()
        return tables_info
    
    def get_schema_info(self) -> str:
        """
        Get a human-readable description of the database schema.
        
        Returns:
            str: Formatted schema information
        """
        schema_info = "Database Schema:\n\n"
        
        for table_name, columns in self.tables_info.items():
            schema_info += f"Table: {table_name}\n"
            schema_info += "Columns:\n"
            
            # Get column details
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            column_details = cursor.fetchall()
            conn.close()
            
            for col in column_details:
                # col format: (id, name, type, notnull, default, pk)
                col_name = col[1]
                col_type = col[2]
                is_pk = "PRIMARY KEY" if col[5] == 1 else ""
                is_not_null = "NOT NULL" if col[3] == 1 else ""
                
                schema_info += f"  - {col_name} ({col_type}) {is_pk} {is_not_null}\n"
            
            schema_info += "\n"
        
        return schema_info
    
    def execute_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute an SQL query and return the results.
        
        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query
            
        Returns:
            List[Dict[str, Any]]: List of rows as dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert rows to dictionaries
            results = [dict(row) for row in rows]
            
            conn.close()
            return results
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            raise
    
    def execute_pandas_query(self, query: str, params: Tuple = ()) -> pd.DataFrame:
        """
        Execute an SQL query and return the results as a pandas DataFrame.
        
        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query
            
        Returns:
            pd.DataFrame: Results as a pandas DataFrame
        """
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            return df
        except (sqlite3.Error, pd.io.sql.DatabaseError) as e:
            logger.error(f"Database error: {e}")
            raise
    
    def sql_query_to_natural_language(self, query: str) -> str:
        """
        Converts an SQL query to a natural language description.
        
        Args:
            query (str): SQL query to convert
            
        Returns:
            str: Natural language description of the query
        """
        query = query.lower()
        
        # Very basic conversion, would need more sophisticated parsing for complex queries
        if "select" in query and "from" in query:
            select_part = query.split("from")[0].replace("select", "").strip()
            from_part = query.split("from")[1].strip()
            
            if "where" in from_part:
                table_part = from_part.split("where")[0].strip()
                where_part = from_part.split("where")[1].strip()
                return f"Retrieving {select_part} from {table_part} where {where_part}"
            else:
                return f"Retrieving {select_part} from {from_part}"
        
        return f"Executing SQL: {query}"
    
    def natural_language_to_sql_query(self, natural_language: str) -> Optional[str]:
        """
        Attempts to convert a natural language question to an SQL query.
        This is a very basic implementation and will only work for simple queries.
        
        Args:
            natural_language (str): Natural language question
            
        Returns:
            Optional[str]: SQL query or None if conversion not possible
        """
        # This is a very basic implementation that would need to be enhanced with a more sophisticated approach
        # Ideally, this would use the LLM with proper prompting to generate SQL
        
        nl = natural_language.lower()
        
        # Basic patterns
        if "list all data centers" in nl or "show all data centers" in nl:
            return "SELECT * FROM data_centers"
        
        if "list all servers" in nl or "show all servers" in nl:
            return "SELECT * FROM servers"
        
        if "count servers" in nl:
            return "SELECT COUNT(*) as server_count FROM servers"
        
        if "average power usage" in nl or "avg power" in nl:
            return "SELECT AVG(power_kw) as avg_power FROM power_usage"
        
        # More complex patterns would be needed for real-world use
        
        return None
