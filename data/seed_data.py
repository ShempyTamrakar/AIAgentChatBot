"""
Script to populate the SQLite database with sample data-center information.
Run this script to create a populated database for testing the chatbot.
"""

import sqlite3
import os
import random
import datetime
from pathlib import Path

# Ensure directory exists
data_dir = Path(__file__).parent
os.makedirs(data_dir, exist_ok=True)

# Database path
DB_PATH = data_dir / "datacenter.db"

def create_tables():
    """Create the database tables if they don't exist."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Create Tables
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

def generate_random_date(start_year=2018, end_year=2023):
    """Generate a random date between start_year and end_year."""
    year = random.randint(start_year, end_year)
    month = random.randint(1, 12)
    day = random.randint(1, 28)  # Simplified for all months
    return f"{year}-{month:02d}-{day:02d}"

def generate_random_ip():
    """Generate a random IP address."""
    return f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}"

def populate_data_centers():
    """Populate the data_centers table with sample data."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Check if table already has data
    cursor.execute("SELECT COUNT(*) FROM data_centers")
    if cursor.fetchone()[0] > 0:
        print("Data centers table already populated. Skipping.")
        conn.close()
        return
    
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
    conn.close()
    print(f"Populated {len(data_centers)} data centers")

def populate_servers():
    """Populate the servers table with sample data."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Check if table already has data
    cursor.execute("SELECT COUNT(*) FROM servers")
    if cursor.fetchone()[0] > 0:
        print("Servers table already populated. Skipping.")
        conn.close()
        return
    
    # Get data center IDs
    cursor.execute("SELECT id FROM data_centers")
    datacenter_ids = [row[0] for row in cursor.fetchall()]
    
    server_models = ["Dell PowerEdge R740", "HP ProLiant DL380", "Lenovo ThinkSystem SR650", 
                     "Cisco UCS C240 M5", "Supermicro SuperServer 2029U-TR4"]
    
    server_statuses = ["active", "maintenance", "standby", "decommissioned"]
    
    servers = []
    for _ in range(50):  # 50 servers across all data centers
        datacenter_id = random.choice(datacenter_ids)
        hostname = f"srv-{random.randint(1000, 9999)}"
        ip_address = generate_random_ip()
        model = random.choice(server_models)
        cpu_cores = random.choice([16, 24, 32, 48, 64])
        ram_gb = random.choice([64, 128, 256, 512])
        storage_tb = random.choice([2.0, 4.0, 8.0, 16.0, 32.0])
        status = random.choices(server_statuses, weights=[0.7, 0.1, 0.15, 0.05])[0]
        commissioned_date = generate_random_date(2018, 2022)
        
        servers.append((datacenter_id, hostname, ip_address, model, cpu_cores, ram_gb, storage_tb, status, commissioned_date))
    
    cursor.executemany(
        "INSERT INTO servers (datacenter_id, hostname, ip_address, model, cpu_cores, ram_gb, storage_tb, status, commissioned_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        servers
    )
    
    conn.commit()
    conn.close()
    print(f"Populated {len(servers)} servers")

def populate_network_devices():
    """Populate the network_devices table with sample data."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Check if table already has data
    cursor.execute("SELECT COUNT(*) FROM network_devices")
    if cursor.fetchone()[0] > 0:
        print("Network devices table already populated. Skipping.")
        conn.close()
        return
    
    # Get data center IDs
    cursor.execute("SELECT id FROM data_centers")
    datacenter_ids = [row[0] for row in cursor.fetchall()]
    
    device_types = ["router", "switch", "firewall", "load_balancer"]
    manufacturers = ["Cisco", "Juniper", "Arista", "Palo Alto Networks", "F5 Networks"]
    
    models = {
        "Cisco": ["Nexus 9000", "Catalyst 9500", "ASR 9000"],
        "Juniper": ["MX240", "EX4600", "SRX4600"],
        "Arista": ["7280R", "7500R", "7050X"],
        "Palo Alto Networks": ["PA-5250", "PA-7080", "PA-3260"],
        "F5 Networks": ["BIG-IP i4800", "BIG-IP i7800", "BIG-IP i10800"]
    }
    
    statuses = ["active", "maintenance", "standby"]
    
    network_devices = []
    for _ in range(30):  # 30 network devices across all data centers
        datacenter_id = random.choice(datacenter_ids)
        device_name = f"net-{random.randint(100, 999)}"
        device_type = random.choice(device_types)
        ip_address = generate_random_ip()
        manufacturer = random.choice(manufacturers)
        model = random.choice(models[manufacturer])
        firmware_version = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(1, 9)}"
        status = random.choices(statuses, weights=[0.8, 0.1, 0.1])[0]
        
        network_devices.append((datacenter_id, device_name, device_type, ip_address, manufacturer, model, firmware_version, status))
    
    cursor.executemany(
        "INSERT INTO network_devices (datacenter_id, device_name, device_type, ip_address, manufacturer, model, firmware_version, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        network_devices
    )
    
    conn.commit()
    conn.close()
    print(f"Populated {len(network_devices)} network devices")

def populate_power_usage():
    """Populate the power_usage table with sample data."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Check if table already has data
    cursor.execute("SELECT COUNT(*) FROM power_usage")
    if cursor.fetchone()[0] > 0:
        print("Power usage table already populated. Skipping.")
        conn.close()
        return
    
    # Get data center IDs and capacities
    cursor.execute("SELECT id, capacity_kw FROM data_centers")
    datacenters = cursor.fetchall()
    
    power_usage = []
    
    # Generate monthly power usage data for the past 2 years
    current_date = datetime.datetime.now()
    for dc_id, capacity_kw in datacenters:
        for month_back in range(24):  # 2 years = 24 months
            date = current_date - datetime.timedelta(days=30*month_back)
            timestamp = date.strftime("%Y-%m-%d %H:%M:%S")
            
            # Power usage varies between 60-85% of capacity with some randomness
            usage_percentage = random.uniform(0.6, 0.85)
            power_kw = capacity_kw * usage_percentage
            
            # PUE typically ranges from 1.1 to 1.6
            pue = random.uniform(1.1, 1.6)
            
            power_usage.append((dc_id, timestamp, power_kw, pue))
    
    cursor.executemany(
        "INSERT INTO power_usage (datacenter_id, timestamp, power_kw, pue) VALUES (?, ?, ?, ?)",
        power_usage
    )
    
    conn.commit()
    conn.close()
    print(f"Populated {len(power_usage)} power usage records")

def populate_maintenance_logs():
    """Populate the maintenance_logs table with sample data."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Check if table already has data
    cursor.execute("SELECT COUNT(*) FROM maintenance_logs")
    if cursor.fetchone()[0] > 0:
        print("Maintenance logs table already populated. Skipping.")
        conn.close()
        return
    
    # Get data center IDs
    cursor.execute("SELECT id FROM data_centers")
    datacenter_ids = [row[0] for row in cursor.fetchall()]
    
    maintenance_types = ["scheduled", "emergency", "preventive", "corrective"]
    
    descriptions = [
        "Cooling system maintenance",
        "UPS battery replacement",
        "Generator testing",
        "Network equipment firmware update",
        "Server hardware replacement",
        "Power distribution unit maintenance",
        "Fire suppression system testing",
        "Air handling unit service",
        "Cable management reorganization",
        "Security system upgrade"
    ]
    
    technicians = ["John Smith", "Maria Rodriguez", "David Chen", "Sarah Johnson", "Ahmed Hassan"]
    
    statuses = ["completed", "in_progress", "scheduled", "canceled"]
    
    maintenance_logs = []
    for _ in range(40):  # 40 maintenance logs across all data centers
        datacenter_id = random.choice(datacenter_ids)
        maintenance_date = generate_random_date(2020, 2023)
        maintenance_type = random.choice(maintenance_types)
        description = random.choice(descriptions)
        technician = random.choice(technicians)
        status = random.choices(statuses, weights=[0.7, 0.1, 0.15, 0.05])[0]
        
        maintenance_logs.append((datacenter_id, maintenance_date, maintenance_type, description, technician, status))
    
    cursor.executemany(
        "INSERT INTO maintenance_logs (datacenter_id, maintenance_date, maintenance_type, description, technician, status) VALUES (?, ?, ?, ?, ?, ?)",
        maintenance_logs
    )
    
    conn.commit()
    conn.close()
    print(f"Populated {len(maintenance_logs)} maintenance logs")

def main():
    """Main function to create tables and populate the database."""
    print(f"Setting up database at {DB_PATH}")
    
    create_tables()
    populate_data_centers()
    populate_servers()
    populate_network_devices()
    populate_power_usage()
    populate_maintenance_logs()
    
    print("Database setup complete!")

if __name__ == "__main__":
    main()
