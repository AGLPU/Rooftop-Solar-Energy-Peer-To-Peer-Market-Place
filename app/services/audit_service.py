import json
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.audit import AuditLog, AuditEventType
from app.models.user import User


class AuditService:
    """Service for managing audit logs and tracing energy credit history"""

    @staticmethod
    def log_event(
        db: Session,
        event_type: AuditEventType,
        listing_id: UUID,
        energy_kwh: Optional[int] = None,
        purchase_id: Optional[UUID] = None,
        initiated_by: Optional[User] = None,
        blockchain_tx_hash: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Log an audit event to the database.
        
        Args:
            db: Database session
            event_type: Type of event
            listing_id: ID of the listing (energy credit)
            energy_kwh: Amount of energy involved (kWh)
            purchase_id: ID of purchase (if applicable)
            initiated_by: User who initiated the event
            blockchain_tx_hash: Blockchain transaction hash (if applicable)
            details: Additional event details (dict)
        
        Returns:
            Created AuditLog record
        """
        audit_log = AuditLog(
            event_type=event_type,
            listing_id=listing_id,
            purchase_id=purchase_id,
            initiated_by=initiated_by.id if initiated_by else None,
            energy_kwh=energy_kwh,
            blockchain_tx_hash=blockchain_tx_hash,
            details=json.dumps(details) if details else None,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        return audit_log

    @staticmethod
    def get_listing_history(
        db: Session,
        listing_id: UUID,
        skip: int = 0,
        limit: int = 50
    ) -> List[AuditLog]:
        """
        Get complete audit history for a listing (energy credit).
        
        Returns all events in chronological order (newest first).
        """
        return db.query(AuditLog)\
            .filter(AuditLog.listing_id == listing_id)\
            .order_by(AuditLog.timestamp.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    @staticmethod
    def get_purchase_history(
        db: Session,
        purchase_id: UUID,
        skip: int = 0,
        limit: int = 50
    ) -> List[AuditLog]:
        """
        Get audit history for a specific purchase.
        """
        return db.query(AuditLog)\
            .filter(AuditLog.purchase_id == purchase_id)\
            .order_by(AuditLog.timestamp.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    @staticmethod
    def get_user_history(
        db: Session,
        user_id: UUID,
        event_types: Optional[List[AuditEventType]] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[AuditLog]:
        """
        Get audit history for events initiated by a user.
        """
        query = db.query(AuditLog).filter(AuditLog.initiated_by == user_id)
        
        if event_types:
            query = query.filter(AuditLog.event_type.in_(event_types))
        
        return query.order_by(AuditLog.timestamp.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    @staticmethod
    def get_blockchain_hash_history(
        db: Session,
        blockchain_tx_hash: str
    ) -> List[AuditLog]:
        """
        Get all audit events related to a blockchain transaction.
        Useful for tracing a token across multiple events.
        """
        return db.query(AuditLog)\
            .filter(AuditLog.blockchain_tx_hash == blockchain_tx_hash)\
            .order_by(AuditLog.timestamp.desc())\
            .all()
