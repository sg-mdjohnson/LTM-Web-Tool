from typing import Dict, Any, Optional
from datetime import datetime
import json
from app.core.logging import logger
from app.db.connection import DatabaseManager
from app.core.context import RequestContext

class AuditLogger:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def log_event(
        self,
        event_type: str,
        action: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success"
    ) -> None:
        try:
            context = RequestContext.get_current()
            
            audit_entry = {
                'timestamp': datetime.utcnow(),
                'event_type': event_type,
                'action': action,
                'user_id': user_id or context.user_id,
                'request_id': context.request_id,
                'client_ip': context.get_tag('client_ip'),
                'status': status,
                'details': json.dumps(details) if details else None
            }
            
            async with self.db_manager.get_session() as session:
                await session.execute(
                    """
                    INSERT INTO audit_logs (
                        timestamp, event_type, action, user_id,
                        request_id, client_ip, status, details
                    ) VALUES (
                        :timestamp, :event_type, :action, :user_id,
                        :request_id, :client_ip, :status, :details
                    )
                    """,
                    audit_entry
                )
                await session.commit()
                
            logger.info(
                f"Audit log created: {event_type} - {action}",
                extra={
                    'audit_entry': audit_entry
                }
            )
            
        except Exception as e:
            logger.error(
                f"Failed to create audit log: {str(e)}",
                extra={
                    'event_type': event_type,
                    'action': action,
                    'user_id': user_id,
                    'details': details
                }
            )
            # Don't raise the exception - audit logging should not break the main flow 