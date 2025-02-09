from typing import Dict, List, Set, Optional
from fastapi import Request, HTTPException
from app.core.logging import logger

class Permission:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description

class Role:
    def __init__(self, name: str, permissions: List[Permission]):
        self.name = name
        self.permissions = set(p.name for p in permissions)

class AuthorizationManager:
    def __init__(self):
        self._roles: Dict[str, Role] = {}
        self._user_roles: Dict[str, Set[str]] = {}

    def add_role(self, role: Role) -> None:
        self._roles[role.name] = role
        logger.info(f"Added role: {role.name}")

    def assign_role_to_user(self, user_id: str, role_name: str) -> None:
        if role_name not in self._roles:
            raise ValueError(f"Role {role_name} does not exist")
            
        if user_id not in self._user_roles:
            self._user_roles[user_id] = set()
            
        self._user_roles[user_id].add(role_name)
        logger.info(f"Assigned role {role_name} to user {user_id}")

    def remove_role_from_user(self, user_id: str, role_name: str) -> None:
        if user_id in self._user_roles:
            self._user_roles[user_id].discard(role_name)
            logger.info(f"Removed role {role_name} from user {user_id}")

    def get_user_permissions(self, user_id: str) -> Set[str]:
        permissions = set()
        user_roles = self._user_roles.get(user_id, set())
        
        for role_name in user_roles:
            role = self._roles.get(role_name)
            if role:
                permissions.update(role.permissions)
                
        return permissions

    def check_permission(
        self,
        user_id: str,
        required_permission: str
    ) -> bool:
        user_permissions = self.get_user_permissions(user_id)
        return required_permission in user_permissions

    async def authorize_request(
        self,
        request: Request,
        required_permission: str
    ) -> None:
        user_id = request.state.user_id
        
        if not user_id:
            logger.warning("No user ID found in request state")
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
            
        if not self.check_permission(user_id, required_permission):
            logger.warning(
                f"User {user_id} does not have required permission: {required_permission}"
            )
            raise HTTPException(
                status_code=403,
                detail="Permission denied"
            )

def requires_permission(permission: str):
    async def dependency(
        request: Request,
        auth_manager: AuthorizationManager
    ):
        await auth_manager.authorize_request(request, permission)
    return dependency 