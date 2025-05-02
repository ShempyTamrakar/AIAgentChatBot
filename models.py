from app import db
from datetime import datetime
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql import expression
from sqlalchemy.orm import foreign, remote

class Location(db.Model):
    __tablename__ = 'locations'
    
    location_id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=True)
    country = db.Column(db.String(50), nullable=False)
    
    # Relationships
    data_centers = db.relationship('DataCenter', back_populates='location')
    
    def __repr__(self):
        return f"<Location {self.city}, {self.country}>"

class DataCenter(db.Model):
    __tablename__ = 'data_centers'
    
    data_center_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.location_id'))
    
    # Relationships
    location = db.relationship('Location', back_populates='data_centers')
    racks = db.relationship('Rack', back_populates='data_center')
    network_devices = db.relationship('NetworkDevice', back_populates='data_center')
    
    def __repr__(self):
        return f"<DataCenter {self.name}>"

class Rack(db.Model):
    __tablename__ = 'racks'
    
    rack_id = db.Column(db.Integer, primary_key=True)
    rack_label = db.Column(db.String(50), nullable=False)
    data_center_id = db.Column(db.Integer, db.ForeignKey('data_centers.data_center_id'))
    
    # Relationships
    data_center = db.relationship('DataCenter', back_populates='racks')
    servers = db.relationship('Server', back_populates='rack')
    
    def __repr__(self):
        return f"<Rack {self.rack_label}>"

class Server(db.Model):
    __tablename__ = 'servers'
    
    server_id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(50), nullable=True)
    rack_id = db.Column(db.Integer, db.ForeignKey('racks.rack_id'))
    os = db.Column(db.String(50), nullable=True)
    
    # Relationships
    rack = db.relationship('Rack', back_populates='servers')
    
    @property
    def maintenance_logs(self):
        from sqlalchemy import and_
        return MaintenanceLog.query.filter(
            and_(
                MaintenanceLog.entity_type == 'server',
                MaintenanceLog.entity_id == self.server_id
            )
        ).all()
    
    def __repr__(self):
        return f"<Server {self.hostname}>"

class NetworkDevice(db.Model):
    __tablename__ = 'network_devices'
    
    device_id = db.Column(db.Integer, primary_key=True)
    device_name = db.Column(db.String(100), nullable=False)
    device_type = db.Column(db.String(50), nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    data_center_id = db.Column(db.Integer, db.ForeignKey('data_centers.data_center_id'))
    
    # Relationships
    data_center = db.relationship('DataCenter', back_populates='network_devices')
    
    @property
    def maintenance_logs(self):
        from sqlalchemy import and_
        return MaintenanceLog.query.filter(
            and_(
                MaintenanceLog.entity_type == 'network_device',
                MaintenanceLog.entity_id == self.device_id
            )
        ).all()
    
    def __repr__(self):
        return f"<NetworkDevice {self.device_name}>"

class MaintenanceLog(db.Model):
    __tablename__ = 'maintenance_logs'
    
    log_id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    maintenance_date = db.Column(db.Date, nullable=False)
    performed_by = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    def get_entity(self):
        """
        Return the associated entity (server or network device)
        """
        if self.entity_type == 'server':
            return Server.query.get(self.entity_id)
        elif self.entity_type == 'network_device':
            return NetworkDevice.query.get(self.entity_id)
        return None
    
    def __repr__(self):
        return f"<MaintenanceLog {self.log_id} on {self.entity_type} {self.entity_id}>"