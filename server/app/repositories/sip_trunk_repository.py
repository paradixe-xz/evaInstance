"""
Repository for SIP Trunk database operations
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.sip_trunk import SIPTrunk
from app.schemas.sip_trunk import SIPTrunkCreate, SIPTrunkUpdate


class SIPTrunkRepository:
    """Repository for SIP Trunk operations"""
    
    @staticmethod
    def create(db: Session, trunk_data: SIPTrunkCreate) -> SIPTrunk:
        """Create a new SIP Trunk"""
        trunk = SIPTrunk(**trunk_data.model_dump())
        db.add(trunk)
        db.commit()
        db.refresh(trunk)
        return trunk
    
    @staticmethod
    def get_by_id(db: Session, trunk_id: int) -> Optional[SIPTrunk]:
        """Get SIP Trunk by ID"""
        return db.query(SIPTrunk).filter(SIPTrunk.id == trunk_id).first()
    
    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[SIPTrunk]:
        """Get SIP Trunk by username"""
        return db.query(SIPTrunk).filter(SIPTrunk.sip_username == username).first()
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[SIPTrunk]:
        """Get all SIP Trunks"""
        return db.query(SIPTrunk).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_active(db: Session) -> List[SIPTrunk]:
        """Get all active SIP Trunks"""
        return db.query(SIPTrunk).filter(SIPTrunk.is_active == True).all()
    
    @staticmethod
    def get_registered(db: Session) -> List[SIPTrunk]:
        """Get all registered SIP Trunks"""
        return db.query(SIPTrunk).filter(
            and_(
                SIPTrunk.is_active == True,
                SIPTrunk.is_registered == True
            )
        ).all()
    
    @staticmethod
    def update(db: Session, trunk_id: int, trunk_data: SIPTrunkUpdate) -> Optional[SIPTrunk]:
        """Update a SIP Trunk"""
        trunk = db.query(SIPTrunk).filter(SIPTrunk.id == trunk_id).first()
        if not trunk:
            return None
        
        update_data = trunk_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(trunk, key, value)
        
        db.commit()
        db.refresh(trunk)
        return trunk
    
    @staticmethod
    def delete(db: Session, trunk_id: int) -> bool:
        """Delete a SIP Trunk"""
        trunk = db.query(SIPTrunk).filter(SIPTrunk.id == trunk_id).first()
        if not trunk:
            return False
        
        db.delete(trunk)
        db.commit()
        return True
    
    @staticmethod
    def increment_call_count(db: Session, trunk_id: int) -> Optional[SIPTrunk]:
        """Increment call count for a trunk"""
        trunk = db.query(SIPTrunk).filter(SIPTrunk.id == trunk_id).first()
        if not trunk:
            return None
        
        trunk.current_calls += 1
        trunk.total_calls += 1
        trunk.last_call_at = datetime.utcnow()
        db.commit()
        db.refresh(trunk)
        return trunk
    
    @staticmethod
    def decrement_call_count(db: Session, trunk_id: int) -> Optional[SIPTrunk]:
        """Decrement call count for a trunk"""
        trunk = db.query(SIPTrunk).filter(SIPTrunk.id == trunk_id).first()
        if not trunk:
            return None
        
        if trunk.current_calls > 0:
            trunk.current_calls -= 1
        db.commit()
        db.refresh(trunk)
        return trunk

