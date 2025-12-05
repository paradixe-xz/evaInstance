"""
Analytics API endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.analytics_service import get_analytics_service
from app.core.dependencies import get_current_user
from app.models.system_user import SystemUser

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_metrics(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    """Get dashboard metrics for the last N days"""
    analytics_service = get_analytics_service(db)
    return analytics_service.get_dashboard_metrics(user_id=current_user.id, days=days)


@router.get("/agents/{agent_id}/performance")
async def get_agent_performance(
    agent_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    """Get performance metrics for a specific agent"""
    analytics_service = get_analytics_service(db)
    return analytics_service.get_agent_performance(agent_id=agent_id, days=days)


@router.get("/campaigns/{campaign_id}")
async def get_campaign_analytics(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    """Get analytics for a specific campaign"""
    analytics_service = get_analytics_service(db)
    return analytics_service.get_campaign_analytics(campaign_id=campaign_id)


@router.get("/messages/statistics")
async def get_message_statistics(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    """Get message statistics"""
    analytics_service = get_analytics_service(db)
    return analytics_service.get_message_statistics(days=days)


@router.get("/calls/statistics")
async def get_call_statistics(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    """Get call statistics"""
    analytics_service = get_analytics_service(db)
    return analytics_service.get_call_statistics(days=days)
