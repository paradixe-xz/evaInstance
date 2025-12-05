"""
SIP Trunk model for managing SIP trunk connections
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship

from ..core.database import Base


class SIPTrunk(Base):
    """SIP Trunk model for managing PBX connections"""
    
    __tablename__ = "sip_trunks"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Trunk identification
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # SIP connection details
    sip_username = Column(String(100), unique=True, nullable=False, index=True)
    sip_password = Column(String(255), nullable=False)  # Should be hashed in production
    sip_domain = Column(String(255), nullable=False)  # IP or domain of the PBX
    sip_port = Column(Integer, default=5060)
    sip_transport = Column(String(10), default="UDP")  # UDP, TCP, TLS
    
    # Network configuration
    remote_ip = Column(String(45), nullable=True)  # IPv4 or IPv6
    local_ip = Column(String(45), nullable=True)  # Local IP for binding
    local_port = Column(Integer, nullable=True)  # Local port for binding
    
    # Trunk status
    is_active = Column(Boolean, default=True)
    is_registered = Column(Boolean, default=False)
    registration_status = Column(String(50), nullable=True)  # registered, failed, pending
    
    # Call routing configuration
    inbound_routing = Column(JSON, nullable=True)  # Rules for inbound calls
    outbound_routing = Column(JSON, nullable=True)  # Rules for outbound calls
    allowed_prefixes = Column(JSON, nullable=True)  # Allowed number prefixes
    blocked_prefixes = Column(JSON, nullable=True)  # Blocked number prefixes
    
    # Capacity and limits
    max_concurrent_calls = Column(Integer, default=10)
    current_calls = Column(Integer, default=0)
    
    # Authentication and security
    auth_username = Column(String(100), nullable=True)  # Different from SIP username if needed
    auth_realm = Column(String(255), nullable=True)
    require_authentication = Column(Boolean, default=True)
    ip_whitelist = Column(JSON, nullable=True)  # List of allowed IPs
    
    # Statistics
    total_calls = Column(Integer, default=0)
    successful_calls = Column(Integer, default=0)
    failed_calls = Column(Integer, default=0)
    last_call_at = Column(DateTime, nullable=True)
    last_registration_at = Column(DateTime, nullable=True)
    
    # Trunk Metadata
    trunk_metadata = Column(JSON, nullable=True)  # Additional configuration
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SIPTrunk(id={self.id}, name='{self.name}', sip_username='{self.sip_username}')>"
    
    def to_dict(self):
        """Convert SIP trunk to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "sip_username": self.sip_username,
            "sip_domain": self.sip_domain,
            "sip_port": self.sip_port,
            "sip_transport": self.sip_transport,
            "remote_ip": self.remote_ip,
            "local_ip": self.local_ip,
            "local_port": self.local_port,
            "is_active": self.is_active,
            "is_registered": self.is_registered,
            "registration_status": self.registration_status,
            "inbound_routing": self.inbound_routing,
            "outbound_routing": self.outbound_routing,
            "allowed_prefixes": self.allowed_prefixes,
            "blocked_prefixes": self.blocked_prefixes,
            "max_concurrent_calls": self.max_concurrent_calls,
            "current_calls": self.current_calls,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "last_call_at": self.last_call_at.isoformat() if self.last_call_at else None,
            "last_registration_at": self.last_registration_at.isoformat() if self.last_registration_at else None,
            "trunk_metadata": self.trunk_metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    def can_accept_call(self) -> bool:
        """Check if trunk can accept a new call"""
        return (
            self.is_active and 
            self.is_registered and 
            self.current_calls < self.max_concurrent_calls
        )

