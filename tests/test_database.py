"""
Unit tests for the database module.
"""

import os
import unittest
import sqlite3
import tempfile

from chatbot.database import DatabaseManager

class TestDatabaseManager(unittest.TestCase):
    """Test cases for the DatabaseManager class."""
    
    def setUp(self):
        """Set up a temporary database for testing."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # Create a test database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create a simple test table
        cursor.execute('''
        CREATE TABLE test_table (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            value INTEGER NOT NULL
        )
        ''')
        
        # Insert some test data
        test_data = [
            (1, "Item 1", 100),
            (2, "Item 2", 200),
            (3, "Item 3", 300)
        ]
        
        cursor.executemany(
            "INSERT INTO test_table (id, name, value) VALUES (?, ?, ?)",
            test_data
        )
        
        conn.commit()
        conn.close()
        
        # Initialize the database manager
        self.db_manager = DatabaseManager(self.db_path)
    
    def tearDown(self):
        """Clean up temporary database after tests."""
        os.unlink(self.db_path)
    
    def test_get_tables_info(self):
        """Test getting table information."""
        tables_info = self.db_manager.tables_info
        
        self.assertIn("test_table", tables_info)
        self.assertEqual(tables_info["test_table"], ["id", "name", "value"])
    
    def test_execute_query(self):
        """Test executing a query."""
        query = "SELECT * FROM test_table WHERE value > ?"
        results = self.db_manager.execute_query(query, (150,))
        
        self.assertEqual(len(results), 2)  # Should return 2 rows
        self.assertEqual(results[0]["name"], "Item 2")
        self.assertEqual(results[1]["value"], 300)
    
    def test_execute_pandas_query(self):
        """Test executing a query with pandas."""
        query = "SELECT * FROM test_table ORDER BY value DESC"
        df = self.db_manager.execute_pandas_query(query)
        
        self.assertEqual(len(df), 3)  # Should return 3 rows
        self.assertEqual(df.iloc[0]["value"], 300)
        self.assertEqual(df.iloc[2]["name"], "Item 1")
    
    def test_get_schema_info(self):
        """Test getting schema information."""
        schema_info = self.db_manager.get_schema_info()
        
        self.assertIn("test_table", schema_info)
        self.assertIn("id", schema_info)
        self.assertIn("name", schema_info)
        self.assertIn("value", schema_info)
    
    def test_natural_language_to_sql_query(self):
        """Test converting natural language to SQL query."""
        nl_query = "list all data centers"
        sql_query = self.db_manager.natural_language_to_sql_query(nl_query)
        
        self.assertEqual(sql_query, "SELECT * FROM data_centers")

if __name__ == "__main__":
    unittest.main()
