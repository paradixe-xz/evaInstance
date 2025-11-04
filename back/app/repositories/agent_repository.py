"""
Agent repository for database operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_

from .base import BaseRepository
from ..models.agent import Agent
from ..core.exceptions import DatabaseError


class AgentRepository(BaseRepository[Agent]):
    """Repository for Agent model operations"""
    
    def __init__(self, db: Session):
        super().__init__(Agent, db)
    
    def get_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Agent]:
        """Get all agents created by a specific user"""
        try:
            return (
                self.db.query(Agent)
                .filter(Agent.creator_id == user_id)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting agents for user {user_id}: {str(e)}")
    
    def get_by_campaign(self, campaign_id: int) -> List[Agent]:
        """Get all agents associated with a campaign"""
        try:
            return (
                self.db.query(Agent)
                .filter(Agent.campaign_id == campaign_id)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting agents for campaign {campaign_id}: {str(e)}")
    
    def get_active_agents(self, user_id: Optional[int] = None) -> List[Agent]:
        """Get all active agents, optionally filtered by user"""
        try:
            query = self.db.query(Agent).filter(
                and_(Agent.is_active == True, Agent.status == "active")
            )
            
            if user_id:
                query = query.filter(Agent.creator_id == user_id)
            
            return query.all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting active agents: {str(e)}")
    
    def get_by_type(self, agent_type: str, user_id: Optional[int] = None) -> List[Agent]:
        """Get agents by type (calls, whatsapp)"""
        try:
            query = self.db.query(Agent).filter(Agent.agent_type == agent_type)
            
            if user_id:
                query = query.filter(Agent.creator_id == user_id)
            
            return query.all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting agents by type {agent_type}: {str(e)}")
    
    def get_ollama_agents(self, user_id: Optional[int] = None) -> List[Agent]:
        """Get all Ollama-based agents"""
        try:
            query = self.db.query(Agent).filter(Agent.is_ollama_model == True)
            
            if user_id:
                query = query.filter(Agent.creator_id == user_id)
            
            return query.all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting Ollama agents: {str(e)}")
    
    def get_by_ollama_model_name(self, model_name: str) -> Optional[Agent]:
        """Get agent by Ollama model name"""
        try:
            return (
                self.db.query(Agent)
                .filter(Agent.ollama_model_name == model_name)
                .first()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting agent by Ollama model name {model_name}: {str(e)}")
    
    def search_agents(self, query: str, user_id: Optional[int] = None) -> List[Agent]:
        """Search agents by name or description"""
        try:
            search_filter = or_(
                Agent.name.ilike(f"%{query}%"),
                Agent.description.ilike(f"%{query}%")
            )
            
            db_query = self.db.query(Agent).filter(search_filter)
            
            if user_id:
                db_query = db_query.filter(Agent.creator_id == user_id)
            
            return db_query.all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error searching agents with query '{query}': {str(e)}")
    
    def update_metrics(self, agent_id: int, metrics: Dict[str, Any]) -> Optional[Agent]:
        """Update agent performance metrics"""
        try:
            agent = self.get(agent_id)
            if not agent:
                return None
            
            # Update metrics fields
            for field, value in metrics.items():
                if hasattr(agent, field):
                    setattr(agent, field, value)
            
            # Recalculate success rate if needed
            if 'total_interactions' in metrics or 'successful_interactions' in metrics:
                agent.calculate_success_rate()
            
            self.db.commit()
            self.db.refresh(agent)
            return agent
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Error updating metrics for agent {agent_id}: {str(e)}")
    
    def update_last_used(self, agent_id: int) -> Optional[Agent]:
        """Update the last used timestamp for an agent"""
        try:
            agent = self.get(agent_id)
            if not agent:
                return None
            
            agent.update_last_used()
            self.db.commit()
            self.db.refresh(agent)
            return agent
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Error updating last used for agent {agent_id}: {str(e)}")
    
    def get_agent_stats(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get aggregated statistics for agents"""
        try:
            query = self.db.query(Agent)
            
            if user_id:
                query = query.filter(Agent.creator_id == user_id)
            
            agents = query.all()
            
            total_agents = len(agents)
            active_agents = len([a for a in agents if a.is_active and a.status == "active"])
            ollama_agents = len([a for a in agents if a.is_ollama_model])
            
            total_interactions = sum(a.total_interactions for a in agents)
            total_successful = sum(a.successful_interactions for a in agents)
            avg_success_rate = sum(a.success_rate for a in agents) / total_agents if total_agents > 0 else 0
            
            return {
                "total_agents": total_agents,
                "active_agents": active_agents,
                "ollama_agents": ollama_agents,
                "total_interactions": total_interactions,
                "total_successful_interactions": total_successful,
                "average_success_rate": round(avg_success_rate, 2)
            }
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting agent statistics: {str(e)}")
    
    def deactivate_agent(self, agent_id: int) -> Optional[Agent]:
        """Deactivate an agent (soft delete)"""
        try:
            agent = self.get(agent_id)
            if not agent:
                return None
            
            agent.is_active = False
            agent.status = "paused"
            
            self.db.commit()
            self.db.refresh(agent)
            return agent
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Error deactivating agent {agent_id}: {str(e)}")
    
    def activate_agent(self, agent_id: int) -> Optional[Agent]:
        """Activate an agent"""
        try:
            agent = self.get(agent_id)
            if not agent:
                return None
            
            agent.is_active = True
            agent.status = "active"
            
            self.db.commit()
            self.db.refresh(agent)
            return agent
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Error activating agent {agent_id}: {str(e)}")