"""
Analytics service for calculating metrics and statistics
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.agent import Agent
from ..models.chat import ChatSession, Message
from ..models.call_log import CallLog
from ..models.campaign import Campaign
from ..core.logging import get_logger

logger = get_logger(__name__)


class AnalyticsService:
    """Service for analytics and metrics calculation"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_dashboard_metrics(self, user_id: Optional[int] = None, days: int = 30) -> Dict[str, Any]:
        """
        Get dashboard metrics for the last N days
        
        Args:
            user_id: Optional user ID to filter metrics
            days: Number of days to look back
            
        Returns:
            Dictionary with dashboard metrics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total agents
        agents_query = self.db.query(Agent)
        if user_id:
            agents_query = agents_query.filter(Agent.creator_id == user_id)
        total_agents = agents_query.count()
        active_agents = agents_query.filter(Agent.status == "active").count()
        
        # Chat metrics
        sessions_query = self.db.query(ChatSession).filter(
            ChatSession.created_at >= start_date
        )
        total_sessions = sessions_query.count()
        
        messages_query = self.db.query(Message).filter(
            Message.created_at >= start_date
        )
        total_messages = messages_query.count()
        
        # Call metrics
        calls_query = self.db.query(CallLog).filter(
            CallLog.created_at >= start_date
        )
        total_calls = calls_query.count()
        avg_call_duration = self.db.query(func.avg(CallLog.duration)).filter(
            CallLog.created_at >= start_date
        ).scalar() or 0
        
        # Campaign metrics
        campaigns_query = self.db.query(Campaign)
        if user_id:
            campaigns_query = campaigns_query.filter(Campaign.owner_id == user_id)
        total_campaigns = campaigns_query.count()
        active_campaigns = campaigns_query.filter(Campaign.status == "active").count()
        
        return {
            "period_days": days,
            "agents": {
                "total": total_agents,
                "active": active_agents,
                "inactive": total_agents - active_agents
            },
            "conversations": {
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "avg_messages_per_session": round(total_messages / total_sessions, 2) if total_sessions > 0 else 0
            },
            "calls": {
                "total": total_calls,
                "avg_duration_seconds": round(avg_call_duration, 2)
            },
            "campaigns": {
                "total": total_campaigns,
                "active": active_campaigns,
                "paused": total_campaigns - active_campaigns
            }
        }
    
    def get_agent_performance(self, agent_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Get performance metrics for a specific agent
        
        Args:
            agent_id: Agent ID
            days: Number of days to look back
            
        Returns:
            Dictionary with agent performance metrics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get agent
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return {}
        
        # Sessions with this agent
        sessions = self.db.query(ChatSession).filter(
            ChatSession.agent_id == agent_id,
            ChatSession.created_at >= start_date
        ).all()
        
        total_sessions = len(sessions)
        
        # Messages
        total_messages = 0
        ai_messages = 0
        user_messages = 0
        
        for session in sessions:
            messages = self.db.query(Message).filter(
                Message.chat_session_id == session.id
            ).all()
            total_messages += len(messages)
            ai_messages += sum(1 for m in messages if m.direction == "outgoing")
            user_messages += sum(1 for m in messages if m.direction == "incoming")
        
        # Response time (average time between user message and AI response)
        avg_response_time = self._calculate_avg_response_time(agent_id, start_date)
        
        return {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "period_days": days,
            "sessions": {
                "total": total_sessions,
                "avg_per_day": round(total_sessions / days, 2)
            },
            "messages": {
                "total": total_messages,
                "from_ai": ai_messages,
                "from_users": user_messages,
                "avg_per_session": round(total_messages / total_sessions, 2) if total_sessions > 0 else 0
            },
            "performance": {
                "avg_response_time_seconds": round(avg_response_time, 2),
                "status": agent.status
            }
        }
    
    def get_campaign_analytics(self, campaign_id: int) -> Dict[str, Any]:
        """
        Get analytics for a specific campaign
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Dictionary with campaign analytics
        """
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return {}
        
        return {
            "campaign_id": campaign_id,
            "name": campaign.name,
            "status": campaign.status,
            "metrics": {
                "total_calls": campaign.total_calls or 0,
                "total_whatsapp_messages": campaign.total_whatsapp_messages or 0,
                "success_rate": campaign.success_rate or 0,
                "total_cost": campaign.total_cost or 0,
                "average_call_duration": campaign.average_call_duration or 0,
                "conversion_rate": campaign.conversion_rate or 0
            },
            "agents": {
                "total": len(campaign.agents),
                "active": len([a for a in campaign.agents if a.status == "active"])
            }
        }
    
    def get_message_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get message statistics
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with message statistics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Messages by direction
        incoming = self.db.query(Message).filter(
            Message.direction == "incoming",
            Message.created_at >= start_date
        ).count()
        
        outgoing = self.db.query(Message).filter(
            Message.direction == "outgoing",
            Message.created_at >= start_date
        ).count()
        
        # Messages by type
        text_messages = self.db.query(Message).filter(
            Message.message_type == "text",
            Message.created_at >= start_date
        ).count()
        
        return {
            "period_days": days,
            "by_direction": {
                "incoming": incoming,
                "outgoing": outgoing,
                "total": incoming + outgoing
            },
            "by_type": {
                "text": text_messages,
                "other": (incoming + outgoing) - text_messages
            },
            "avg_per_day": round((incoming + outgoing) / days, 2)
        }
    
    def get_call_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get call statistics
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with call statistics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        calls = self.db.query(CallLog).filter(
            CallLog.created_at >= start_date
        ).all()
        
        total_calls = len(calls)
        total_duration = sum(c.duration or 0 for c in calls)
        
        # Calls by status
        completed = sum(1 for c in calls if c.status == "completed")
        failed = sum(1 for c in calls if c.status == "failed")
        
        return {
            "period_days": days,
            "total_calls": total_calls,
            "by_status": {
                "completed": completed,
                "failed": failed,
                "success_rate": round(completed / total_calls * 100, 2) if total_calls > 0 else 0
            },
            "duration": {
                "total_seconds": total_duration,
                "avg_seconds": round(total_duration / total_calls, 2) if total_calls > 0 else 0,
                "total_minutes": round(total_duration / 60, 2)
            },
            "avg_per_day": round(total_calls / days, 2)
        }
    
    def _calculate_avg_response_time(self, agent_id: int, start_date: datetime) -> float:
        """Calculate average response time for an agent"""
        sessions = self.db.query(ChatSession).filter(
            ChatSession.agent_id == agent_id,
            ChatSession.created_at >= start_date
        ).all()
        
        response_times = []
        
        for session in sessions:
            messages = self.db.query(Message).filter(
                Message.chat_session_id == session.id
            ).order_by(Message.created_at).all()
            
            for i in range(len(messages) - 1):
                if messages[i].direction == "incoming" and messages[i+1].direction == "outgoing":
                    time_diff = (messages[i+1].created_at - messages[i].created_at).total_seconds()
                    response_times.append(time_diff)
        
        return sum(response_times) / len(response_times) if response_times else 0


def get_analytics_service(db: Session) -> AnalyticsService:
    """Get analytics service instance"""
    return AnalyticsService(db)
