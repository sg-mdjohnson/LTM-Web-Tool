from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
from fastapi import Request, Response, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
from app.core.errors import AuthenticationError
from app.models.user import User
from app.db.session import SessionLocal
from app.core.logging import logger
from starlette.middleware.base import BaseHTTPMiddleware

class AuthManager:
    """Unified authentication manager"""
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
        self.security = HTTPBearer()
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_minutes = settings.REFRESH_TOKEN_EXPIRE_MINUTES
        self.blacklisted_tokens: set = set()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification error: {str(e)}")
            return False

    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        try:
            return self.pwd_context.hash(password)
        except Exception as e:
            logger.error(f"Password hashing error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Error processing password"
            )

    def create_token(
        self,
        data: Dict[str, Any],
        token_type: str = "access",
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT token"""
        try:
            to_encode = data.copy()
            expire = datetime.utcnow() + (
                expires_delta if expires_delta
                else timedelta(minutes=self.access_token_expire_minutes)
            )
            
            to_encode.update({
                "exp": expire,
                "iat": datetime.utcnow(),
                "type": token_type
            })
            
            return jwt.encode(
                to_encode,
                self.secret_key,
                algorithm=self.algorithm
            )
        except Exception as e:
            logger.error(f"Token creation error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Could not create token"
            )

    def create_refresh_token(self, user_id: int) -> str:
        """Create a refresh token"""
        try:
            expires = timedelta(minutes=self.refresh_token_expire_minutes)
            return self.create_token(
                {"sub": str(user_id)},
                token_type="refresh",
                expires_delta=expires
            )
        except Exception as e:
            logger.error(f"Refresh token creation error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Could not create refresh token"
            )

    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and verify a JWT token"""
        try:
            if token in self.blacklisted_tokens:
                raise AuthenticationError("Token has been revoked")

            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Token has expired"
            )
        except jwt.JWTError as e:
            logger.error(f"Token decode error: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials"
            )

    def verify_token_type(self, token: str, expected_type: str) -> bool:
        """Verify token type (access or refresh)"""
        try:
            payload = self.decode_token(token)
            return payload.get("type") == expected_type
        except Exception:
            return False

    def blacklist_token(self, token: str) -> None:
        """Add token to blacklist"""
        self.blacklisted_tokens.add(token)

    def refresh_token(self, token: str) -> str:
        """Create new access token from refresh token"""
        try:
            payload = self.decode_token(token)
            if not self.verify_token_type(token, "refresh"):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token type"
                )
            
            user_id = payload['sub']
            return self.create_token({"sub": user_id})
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise

    async def authenticate_user(
        self,
        username: str,
        password: str
    ) -> Optional[User]:
        """Authenticate a user"""
        try:
            db = SessionLocal()
            user = await db.query(User).filter(User.username == username).first()
            if not user:
                return None
            if not self.verify_password(password, user.hashed_password):
                return None
            return user
        except Exception as e:
            logger.error(f"User authentication error: {str(e)}")
            return None
        finally:
            await db.close()

    async def authenticate_request(
        self,
        request: Request
    ) -> Optional[Dict[str, Any]]:
        """Authenticate an HTTP request"""
        try:
            auth = await self.security(request)
            return self.decode_token(auth.credentials)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Authentication failed"
            )

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        auth_manager: AuthManager,
        exclude_paths: Optional[set] = None
    ):
        super().__init__(app)
        self.auth_manager = auth_manager
        self.exclude_paths = exclude_paths or {
            '/auth/login',
            '/auth/refresh',
            '/docs',
            '/redoc',
            '/openapi.json'
        }

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        try:
            payload = await self.auth_manager.authenticate_request(request)
            request.state.user_id = int(payload.get("sub"))
            request.state.token_payload = payload
            return await call_next(request)

        except HTTPException as e:
            return Response(
                content=str(e.detail),
                status_code=e.status_code
            )
        except Exception as e:
            logger.error(f"Auth middleware error: {str(e)}")
            return Response(
                content="Internal server error",
                status_code=500
            )

async def get_current_user(
    request: Request,
    token: str = Security(OAuth2PasswordBearer(tokenUrl="auth/login"))
) -> User:
    """Helper function to get current user from request"""
    try:
        auth_manager = AuthManager()
        payload = auth_manager.decode_token(token)
        user_id = int(payload.get("sub"))
        db = SessionLocal()
        user = await db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        return user
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )
    finally:
        await db.close() 