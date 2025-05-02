"""
Query handler for the Data Center Chatbot application.
Contains specialized queries for answering common questions about data centers.
"""

import logging
from sqlalchemy import text
from app import db

logger = logging.getLogger(__name__)

class QueryHandler:
    """Handles specialized SQL queries for the chatbot."""
    
    @staticmethod
    def execute_query(query, params=()):
        """Execute a raw SQL query and return the results."""
        try:
            result = db.session.execute(text(query), params)
            rows = result.fetchall()
            results = [dict(row._mapping) for row in rows]
            return results
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return [{"error": str(e)}]
    
    # Location & Data Center Questions
    
    @staticmethod
    def get_cities_with_data_centers():
        """Which cities have data centers?"""
        query = """
        SELECT DISTINCT city FROM locations l
        JOIN data_centers dc ON l.location_id = dc.location_id
        ORDER BY city;
        """
        results = QueryHandler.execute_query(query)
        
        if results and 'error' not in results[0]:
            cities = [row['city'] for row in results]
            return {
                "success": True,
                "cities": cities,
                "count": len(cities)
            }
        return {"success": False, "error": results[0].get('error', 'Unknown error')}
        
    @staticmethod
    def get_data_centers_by_country():
        """How many data centers are in each country?"""
        query = """
        SELECT l.country, COUNT(dc.data_center_id) as data_center_count
        FROM locations l
        JOIN data_centers dc ON l.location_id = dc.location_id
        GROUP BY l.country
        ORDER BY data_center_count DESC;
        """
        results = QueryHandler.execute_query(query)
        
        if results and 'error' not in results[0]:
            return {
                "success": True,
                "countries": results
            }
        return {"success": False, "error": results[0].get('error', 'Unknown error')}
    
    @staticmethod
    def list_data_centers_with_locations():
        """List all data centers along with their corresponding city and country."""
        query = """
        SELECT dc.name, l.city, l.state, l.country
        FROM data_centers dc
        JOIN locations l ON dc.location_id = l.location_id
        ORDER BY dc.name;
        """
        results = QueryHandler.execute_query(query)
        
        if results and 'error' not in results[0]:
            return {
                "success": True,
                "data_centers": results
            }
        return {"success": False, "error": results[0].get('error', 'Unknown error')}
    
    # Rack & Server Questions
    
    @staticmethod
    def get_racks_by_data_center():
        """How many racks are in each data center?"""
        query = """
        SELECT dc.name as data_center_name, COUNT(r.rack_id) as rack_count
        FROM data_centers dc
        LEFT JOIN racks r ON dc.data_center_id = r.data_center_id
        GROUP BY dc.data_center_id
        ORDER BY rack_count DESC;
        """
        results = QueryHandler.execute_query(query)
        
        if results and 'error' not in results[0]:
            return {
                "success": True,
                "rack_counts": results
            }
        return {"success": False, "error": results[0].get('error', 'Unknown error')}
    
    @staticmethod
    def list_servers_with_racks_and_data_centers():
        """List all servers along with their rack label and data center name."""
        query = """
        SELECT s.hostname, s.ip_address, s.os, r.rack_label, dc.name as data_center_name
        FROM servers s
        JOIN racks r ON s.rack_id = r.rack_id
        JOIN data_centers dc ON r.data_center_id = dc.data_center_id
        ORDER BY dc.name, r.rack_label, s.hostname;
        """
        results = QueryHandler.execute_query(query)
        
        if results and 'error' not in results[0]:
            return {
                "success": True,
                "servers": results
            }
        return {"success": False, "error": results[0].get('error', 'Unknown error')}
    
    @staticmethod
    def get_servers_with_os(os_filter):
        """Which servers are running a specific OS?"""
        query = """
        SELECT s.hostname, s.os, r.rack_label, dc.name as data_center_name
        FROM servers s
        JOIN racks r ON s.rack_id = r.rack_id
        JOIN data_centers dc ON r.data_center_id = dc.data_center_id
        WHERE LOWER(s.os) LIKE LOWER(:os_filter)
        ORDER BY dc.name, r.rack_label, s.hostname;
        """
        results = QueryHandler.execute_query(query, {"os_filter": f"%{os_filter}%"})
        
        if results is not None:
            return {
                "success": True,
                "servers": results,
                "count": len(results)
            }
        return {"success": False, "error": "Error searching for servers by OS"}
    
    @staticmethod
    def get_empty_racks():
        """Which racks do not have any servers?"""
        query = """
        SELECT r.rack_label, dc.name as data_center_name
        FROM racks r
        JOIN data_centers dc ON r.data_center_id = dc.data_center_id
        LEFT JOIN servers s ON r.rack_id = s.rack_id
        WHERE s.server_id IS NULL
        ORDER BY dc.name, r.rack_label;
        """
        results = QueryHandler.execute_query(query)
        
        if results is not None:
            return {
                "success": True,
                "empty_racks": results,
                "count": len(results)
            }
        return {"success": False, "error": "Error finding empty racks"}
    
    # Network Device Questions
    
    @staticmethod
    def list_network_devices_with_data_centers():
        """List all network devices along with their type and the data center they are located in."""
        query = """
        SELECT nd.device_name, nd.device_type, nd.ip_address, dc.name as data_center_name
        FROM network_devices nd
        JOIN data_centers dc ON nd.data_center_id = dc.data_center_id
        ORDER BY dc.name, nd.device_type, nd.device_name;
        """
        results = QueryHandler.execute_query(query)
        
        if results and 'error' not in results[0]:
            return {
                "success": True,
                "network_devices": results
            }
        return {"success": False, "error": results[0].get('error', 'Unknown error')}
    
    @staticmethod
    def get_network_devices_by_data_center():
        """How many network devices are in each data center?"""
        query = """
        SELECT dc.name as data_center_name, COUNT(nd.device_id) as device_count
        FROM data_centers dc
        LEFT JOIN network_devices nd ON dc.data_center_id = nd.data_center_id
        GROUP BY dc.data_center_id
        ORDER BY device_count DESC;
        """
        results = QueryHandler.execute_query(query)
        
        if results and 'error' not in results[0]:
            return {
                "success": True,
                "device_counts": results
            }
        return {"success": False, "error": results[0].get('error', 'Unknown error')}
    
    @staticmethod
    def find_network_devices_by_location(location):
        """Find all IP addresses of network devices in a specific location."""
        query = """
        SELECT nd.device_name, nd.device_type, nd.ip_address, dc.name as data_center_name
        FROM network_devices nd
        JOIN data_centers dc ON nd.data_center_id = dc.data_center_id
        JOIN locations l ON dc.location_id = l.location_id
        WHERE LOWER(l.city) LIKE LOWER(:location) OR LOWER(l.country) LIKE LOWER(:location)
        ORDER BY dc.name, nd.device_type, nd.device_name;
        """
        results = QueryHandler.execute_query(query, {"location": f"%{location}%"})
        
        if results is not None:
            return {
                "success": True,
                "network_devices": results,
                "count": len(results)
            }
        return {"success": False, "error": f"Error finding network devices in {location}"}
    
    # Maintenance Log Questions
    
    @staticmethod
    def get_maintenance_by_technician(technician):
        """Which entities had maintenance performed by a specific technician?"""
        query = """
        SELECT 
            ml.log_id, ml.entity_type, ml.entity_id, ml.maintenance_date, ml.performed_by, ml.notes,
            CASE 
                WHEN ml.entity_type = 'server' THEN s.hostname
                WHEN ml.entity_type = 'network_device' THEN nd.device_name
                ELSE 'Unknown'
            END as entity_name
        FROM maintenance_logs ml
        LEFT JOIN servers s ON ml.entity_type = 'server' AND ml.entity_id = s.server_id
        LEFT JOIN network_devices nd ON ml.entity_type = 'network_device' AND ml.entity_id = nd.device_id
        WHERE LOWER(ml.performed_by) LIKE LOWER(:technician)
        ORDER BY ml.maintenance_date DESC;
        """
        results = QueryHandler.execute_query(query, {"technician": f"%{technician}%"})
        
        if results is not None:
            return {
                "success": True,
                "maintenance_logs": results,
                "count": len(results)
            }
        return {"success": False, "error": f"Error finding maintenance logs for technician {technician}"}
    
    @staticmethod
    def get_maintenance_count_by_entity_type():
        """How many maintenance tasks were performed on servers vs. network devices?"""
        query = """
        SELECT entity_type, COUNT(log_id) as maintenance_count
        FROM maintenance_logs
        GROUP BY entity_type
        ORDER BY maintenance_count DESC;
        """
        results = QueryHandler.execute_query(query)
        
        if results and 'error' not in results[0]:
            return {
                "success": True,
                "maintenance_counts": results
            }
        return {"success": False, "error": results[0].get('error', 'Unknown error')}
    
    @staticmethod
    def get_server_maintenance_by_year(year):
        """Which servers had maintenance in a specific year?"""
        query = """
        SELECT s.hostname, s.ip_address, ml.maintenance_date, ml.performed_by, ml.notes
        FROM maintenance_logs ml
        JOIN servers s ON ml.entity_type = 'server' AND ml.entity_id = s.server_id
        WHERE EXTRACT(YEAR FROM ml.maintenance_date) = :year
        ORDER BY ml.maintenance_date DESC;
        """
        results = QueryHandler.execute_query(query, {"year": year})
        
        if results is not None:
            return {
                "success": True,
                "server_maintenance": results,
                "count": len(results)
            }
        return {"success": False, "error": f"Error finding server maintenance for year {year}"}
    
    @staticmethod
    def list_maintenance_logs_with_entity_names():
        """List all maintenance logs with the corresponding server or device name."""
        query = """
        SELECT 
            ml.log_id, ml.entity_type, ml.maintenance_date, ml.performed_by, ml.notes,
            CASE 
                WHEN ml.entity_type = 'server' THEN s.hostname
                WHEN ml.entity_type = 'network_device' THEN nd.device_name
                ELSE 'Unknown'
            END as entity_name
        FROM maintenance_logs ml
        LEFT JOIN servers s ON ml.entity_type = 'server' AND ml.entity_id = s.server_id
        LEFT JOIN network_devices nd ON ml.entity_type = 'network_device' AND ml.entity_id = nd.device_id
        ORDER BY ml.maintenance_date DESC;
        """
        results = QueryHandler.execute_query(query)
        
        if results and 'error' not in results[0]:
            return {
                "success": True,
                "maintenance_logs": results
            }
        return {"success": False, "error": results[0].get('error', 'Unknown error')}
    
    # Join-Based Analytical Questions
    
    @staticmethod
    def get_server_count_by_country():
        """Find the total number of servers in each country."""
        query = """
        SELECT l.country, COUNT(s.server_id) as server_count
        FROM locations l
        JOIN data_centers dc ON l.location_id = dc.location_id
        JOIN racks r ON dc.data_center_id = r.data_center_id
        JOIN servers s ON r.rack_id = s.rack_id
        GROUP BY l.country
        ORDER BY server_count DESC;
        """
        results = QueryHandler.execute_query(query)
        
        if results and 'error' not in results[0]:
            return {
                "success": True,
                "country_servers": results
            }
        return {"success": False, "error": results[0].get('error', 'Unknown error')}
    
    @staticmethod
    def get_data_centers_with_both_servers_and_network_devices():
        """Which data centers have both servers and network devices?"""
        query = """
        SELECT dc.name, 
               COUNT(DISTINCT s.server_id) as server_count, 
               COUNT(DISTINCT nd.device_id) as network_device_count
        FROM data_centers dc
        JOIN racks r ON dc.data_center_id = r.data_center_id
        JOIN servers s ON r.rack_id = s.rack_id
        JOIN network_devices nd ON dc.data_center_id = nd.data_center_id
        GROUP BY dc.data_center_id
        HAVING COUNT(DISTINCT s.server_id) > 0 AND COUNT(DISTINCT nd.device_id) > 0
        ORDER BY dc.name;
        """
        results = QueryHandler.execute_query(query)
        
        if results is not None:
            return {
                "success": True,
                "data_centers": results,
                "count": len(results)
            }
        return {"success": False, "error": "Error finding data centers with both servers and network devices"}
    
    @staticmethod
    def get_most_recent_server_maintenance():
        """Which server had the most recent maintenance performed?"""
        query = """
        SELECT s.hostname, s.ip_address, s.os, r.rack_label, dc.name as data_center_name,
               ml.maintenance_date, ml.performed_by, ml.notes
        FROM maintenance_logs ml
        JOIN servers s ON ml.entity_type = 'server' AND ml.entity_id = s.server_id
        JOIN racks r ON s.rack_id = r.rack_id
        JOIN data_centers dc ON r.data_center_id = dc.data_center_id
        ORDER BY ml.maintenance_date DESC
        LIMIT 1;
        """
        results = QueryHandler.execute_query(query)
        
        if results and len(results) > 0 and 'error' not in results[0]:
            return {
                "success": True,
                "server": results[0]
            }
        return {"success": False, "error": "Error finding most recent server maintenance"}
    
    @staticmethod
    def get_entities_without_maintenance():
        """Show all entities (servers or network devices) that have never had maintenance."""
        query = """
        -- Servers without maintenance
        SELECT 'server' as entity_type, s.hostname as entity_name, s.ip_address, 
               r.rack_label, dc.name as data_center_name
        FROM servers s
        JOIN racks r ON s.rack_id = r.rack_id
        JOIN data_centers dc ON r.data_center_id = dc.data_center_id
        LEFT JOIN maintenance_logs ml ON ml.entity_type = 'server' AND ml.entity_id = s.server_id
        WHERE ml.log_id IS NULL
        
        UNION ALL
        
        -- Network devices without maintenance
        SELECT 'network_device' as entity_type, nd.device_name as entity_name, nd.ip_address,
               NULL as rack_label, dc.name as data_center_name
        FROM network_devices nd
        JOIN data_centers dc ON nd.data_center_id = dc.data_center_id
        LEFT JOIN maintenance_logs ml ON ml.entity_type = 'network_device' AND ml.entity_id = nd.device_id
        WHERE ml.log_id IS NULL
        
        ORDER BY entity_type, entity_name;
        """
        results = QueryHandler.execute_query(query)
        
        if results is not None:
            return {
                "success": True,
                "entities": results,
                "count": len(results)
            }
        return {"success": False, "error": "Error finding entities without maintenance"}