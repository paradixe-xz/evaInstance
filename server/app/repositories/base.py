"""
Base repository class for common database operations
"""

from typing import Generic, TypeVar, Type, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..core.database import Base
from ..core.exceptions import DatabaseError

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository class with common CRUD operations"""
    
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db
    
    def create(self, obj_data: Dict[str, Any]) -> ModelType:
        """Create a new record"""
        try:
            db_obj = self.model(**obj_data)
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Error creating {self.model.__name__}: {str(e)}")
    
    def get(self, id: int) -> Optional[ModelType]:
        """Get a record by ID"""
        try:
            return self.db.query(self.model).filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting {self.model.__name__} by ID {id}: {str(e)}")
    
    def get_by_field(self, field_name: str, value: Any) -> Optional[ModelType]:
        """Get a record by a specific field"""
        try:
            field = getattr(self.model, field_name)
            return self.db.query(self.model).filter(field == value).first()
        except (AttributeError, SQLAlchemyError) as e:
            raise DatabaseError(f"Error getting {self.model.__name__} by {field_name}: {str(e)}")
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[ModelType]:
        """Get all records with pagination"""
        try:
            return self.db.query(self.model).offset(offset).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting all {self.model.__name__}: {str(e)}")
    
    def update(self, id: int, obj_data: Dict[str, Any]) -> Optional[ModelType]:
        """Update a record by ID"""
        try:
            db_obj = self.get(id)
            if not db_obj:
                return None
            
            for field, value in obj_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            self.db.commit()
            self.db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Error updating {self.model.__name__} with ID {id}: {str(e)}")
    
    def delete(self, id: int) -> bool:
        """Delete a record by ID"""
        try:
            db_obj = self.get(id)
            if not db_obj:
                return False
            
            self.db.delete(db_obj)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Error deleting {self.model.__name__} with ID {id}: {str(e)}")
    
    def count(self) -> int:
        """Count total records"""
        try:
            return self.db.query(self.model).count()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error counting {self.model.__name__}: {str(e)}")
    
    def exists(self, id: int) -> bool:
        """Check if a record exists by ID"""
        try:
            return self.db.query(self.model).filter(self.model.id == id).first() is not None
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error checking existence of {self.model.__name__} with ID {id}: {str(e)}")
    
    def bulk_create(self, obj_data_list: List[Dict[str, Any]]) -> List[ModelType]:
        """Create multiple records in bulk"""
        try:
            db_objs = [self.model(**obj_data) for obj_data in obj_data_list]
            self.db.add_all(db_objs)
            self.db.commit()
            for db_obj in db_objs:
                self.db.refresh(db_obj)
            return db_objs
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Error bulk creating {self.model.__name__}: {str(e)}")
    
    def filter_by(self, **filters) -> List[ModelType]:
        """Filter records by multiple fields"""
        try:
            query = self.db.query(self.model)
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)
            return query.all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error filtering {self.model.__name__}: {str(e)}")