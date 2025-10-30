import jwt
from datetime import datetime, timedelta
from typing import Optional
from app.models.auth import AuthConfig

class AuthService:
    """认证服务"""
    
    @staticmethod
    def verify_secret_key(secret_key: str) -> bool:
        """验证密钥"""
        return secret_key == AuthConfig.SECRET_KEY
    
    @staticmethod
    def generate_token() -> str:
        """生成JWT token"""
        payload = {
            "exp": datetime.utcnow() + timedelta(hours=AuthConfig.TOKEN_EXPIRE_HOURS),
            "iat": datetime.utcnow(),
            "sub": "datainsight_user"
        }
        return jwt.encode(payload, AuthConfig.JWT_SECRET, algorithm="HS256")
    
    @staticmethod
    def verify_token(token: str) -> bool:
        """验证JWT token"""
        try:
            payload = jwt.decode(token, AuthConfig.JWT_SECRET, algorithms=["HS256"])
            return True
        except jwt.ExpiredSignatureError:
            return False
        except jwt.InvalidTokenError:
            return False
    
    @staticmethod
    def extract_token_from_header(authorization: Optional[str]) -> Optional[str]:
        """从Authorization header中提取token"""
        if not authorization:
            return None
        
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        
        return parts[1]