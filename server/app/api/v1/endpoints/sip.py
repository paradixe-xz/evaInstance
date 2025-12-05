"""
Endpoints para gestión de SIP Trunks
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.sip_trunk_repository import SIPTrunkRepository
from app.schemas.sip_trunk import (
    SIPTrunkCreate,
    SIPTrunkUpdate,
    SIPTrunkResponse,
    SIPTrunkListResponse,
    SIPTrunkRegisterRequest,
    SIPTrunkRegisterResponse,
    SIPCallRequest,
    SIPCallResponse
)
from app.services.sip_service import sip_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/trunks", response_model=SIPTrunkResponse, status_code=201)
async def create_sip_trunk(
    trunk_data: SIPTrunkCreate,
    db: Session = Depends(get_db)
):
    """Crear un nuevo SIP Trunk"""
    try:
        # Verificar si ya existe un tronco con el mismo username
        existing = SIPTrunkRepository.get_by_username(db, trunk_data.sip_username)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Ya existe un tronco SIP con el username: {trunk_data.sip_username}"
            )
        
        trunk = SIPTrunkRepository.create(db, trunk_data)
        logger.info(f"SIP Trunk creado: {trunk.name} (ID: {trunk.id})")
        return trunk
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando SIP Trunk: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trunks", response_model=SIPTrunkListResponse)
async def list_sip_trunks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Listar todos los SIP Trunks"""
    try:
        if active_only:
            trunks = SIPTrunkRepository.get_active(db)
        else:
            trunks = SIPTrunkRepository.get_all(db, skip=skip, limit=limit)
        
        return SIPTrunkListResponse(
            trunks=[SIPTrunkResponse.model_validate(trunk) for trunk in trunks],
            total=len(trunks)
        )
    except Exception as e:
        logger.error(f"Error listando SIP Trunks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trunks/{trunk_id}", response_model=SIPTrunkResponse)
async def get_sip_trunk(
    trunk_id: int,
    db: Session = Depends(get_db)
):
    """Obtener un SIP Trunk por ID"""
    try:
        trunk = SIPTrunkRepository.get_by_id(db, trunk_id)
        if not trunk:
            raise HTTPException(status_code=404, detail="SIP Trunk no encontrado")
        return trunk
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo SIP Trunk: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/trunks/{trunk_id}", response_model=SIPTrunkResponse)
async def update_sip_trunk(
    trunk_id: int,
    trunk_data: SIPTrunkUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar un SIP Trunk"""
    try:
        trunk = SIPTrunkRepository.update(db, trunk_id, trunk_data)
        if not trunk:
            raise HTTPException(status_code=404, detail="SIP Trunk no encontrado")
        
        logger.info(f"SIP Trunk actualizado: {trunk.name} (ID: {trunk.id})")
        return trunk
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando SIP Trunk: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/trunks/{trunk_id}", status_code=204)
async def delete_sip_trunk(
    trunk_id: int,
    db: Session = Depends(get_db)
):
    """Eliminar un SIP Trunk"""
    try:
        # Desregistrar el tronco si está registrado
        trunk = SIPTrunkRepository.get_by_id(db, trunk_id)
        if trunk and trunk.is_registered:
            sip_service.unregister_trunk(trunk_id)
        
        success = SIPTrunkRepository.delete(db, trunk_id)
        if not success:
            raise HTTPException(status_code=404, detail="SIP Trunk no encontrado")
        
        logger.info(f"SIP Trunk eliminado: ID {trunk_id}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando SIP Trunk: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trunks/{trunk_id}/register", response_model=SIPTrunkRegisterResponse)
async def register_sip_trunk(
    trunk_id: int,
    db: Session = Depends(get_db)
):
    """Registrar un SIP Trunk"""
    try:
        trunk = SIPTrunkRepository.get_by_id(db, trunk_id)
        if not trunk:
            raise HTTPException(status_code=404, detail="SIP Trunk no encontrado")
        
        if not trunk.is_active:
            raise HTTPException(
                status_code=400,
                detail="No se puede registrar un tronco inactivo"
            )
        
        success, message = sip_service.register_trunk(trunk)
        if success:
            # Actualizar estado en la base de datos
            trunk = SIPTrunkRepository.get_by_id(db, trunk_id)
            return SIPTrunkRegisterResponse(
                success=True,
                message=message,
                registration_status=trunk.registration_status
            )
        else:
            raise HTTPException(status_code=500, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registrando SIP Trunk: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trunks/{trunk_id}/unregister", response_model=SIPTrunkRegisterResponse)
async def unregister_sip_trunk(
    trunk_id: int,
    db: Session = Depends(get_db)
):
    """Desregistrar un SIP Trunk"""
    try:
        trunk = SIPTrunkRepository.get_by_id(db, trunk_id)
        if not trunk:
            raise HTTPException(status_code=404, detail="SIP Trunk no encontrado")
        
        success, message = sip_service.unregister_trunk(trunk_id)
        if success:
            trunk = SIPTrunkRepository.get_by_id(db, trunk_id)
            return SIPTrunkRegisterResponse(
                success=True,
                message=message,
                registration_status=trunk.registration_status
            )
        else:
            raise HTTPException(status_code=500, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error desregistrando SIP Trunk: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trunks/{trunk_id}/status")
async def get_trunk_status(
    trunk_id: int,
    db: Session = Depends(get_db)
):
    """Obtener estado de un SIP Trunk"""
    try:
        trunk = SIPTrunkRepository.get_by_id(db, trunk_id)
        if not trunk:
            raise HTTPException(status_code=404, detail="SIP Trunk no encontrado")
        
        # Obtener estado del servicio SIP
        status = sip_service.get_trunk_status(trunk_id)
        if status:
            return status
        
        # Si no está en el servicio, devolver estado de la base de datos
        return {
            'id': trunk.id,
            'name': trunk.name,
            'is_registered': trunk.is_registered,
            'registration_status': trunk.registration_status,
            'current_calls': trunk.current_calls,
            'max_concurrent_calls': trunk.max_concurrent_calls,
            'last_registration_at': trunk.last_registration_at.isoformat() if trunk.last_registration_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estado del tronco: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trunks/active/status")
async def get_all_active_trunks_status():
    """Obtener estado de todos los troncos activos"""
    try:
        trunks = sip_service.get_all_active_trunks()
        return {
            "trunks": trunks,
            "total": len(trunks)
        }
    except Exception as e:
        logger.error(f"Error obteniendo estado de troncos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calls/initiate", response_model=SIPCallResponse)
async def initiate_sip_call(
    call_request: SIPCallRequest,
    db: Session = Depends(get_db)
):
    """Iniciar una llamada SIP a través de un tronco"""
    try:
        trunk = SIPTrunkRepository.get_by_id(db, call_request.trunk_id)
        if not trunk:
            raise HTTPException(status_code=404, detail="SIP Trunk no encontrado")
        
        if not trunk.can_accept_call():
            raise HTTPException(
                status_code=400,
                detail="El tronco no puede aceptar más llamadas en este momento"
            )
        
        # Aquí se integraría con el sistema de llamadas real
        # Por ahora, simulamos la llamada
        import uuid
        call_id = str(uuid.uuid4())
        
        # Incrementar contador de llamadas
        SIPTrunkRepository.increment_call_count(db, call_request.trunk_id)
        
        logger.info(f"Llamada SIP iniciada: {call_id} a {call_request.destination}")
        
        return SIPCallResponse(
            success=True,
            call_id=call_id,
            message="Llamada iniciada exitosamente",
            status="initiated"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error iniciando llamada SIP: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/server/status")
async def get_sip_server_status():
    """Obtener estado del servidor SIP"""
    try:
        return {
            "is_running": sip_service.is_running,
            "active_trunks": len(sip_service.active_trunks),
            "active_calls": len(sip_service.active_calls)
        }
    except Exception as e:
        logger.error(f"Error obteniendo estado del servidor SIP: {e}")
        raise HTTPException(status_code=500, detail=str(e))

