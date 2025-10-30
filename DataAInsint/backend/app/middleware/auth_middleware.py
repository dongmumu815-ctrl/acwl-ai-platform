from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from app.services.auth_service import AuthService
import json

class AuthMiddleware:
    """认证中间件"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # 检查是否是需要认证的路径
        if self.should_authenticate(request.url.path):
            # 验证token
            authorization = request.headers.get("authorization")
            token = AuthService.extract_token_from_header(authorization)
            
            if not token or not AuthService.verify_token(token):
                response = JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "未授权访问，请先登录"}
                )
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)
    
    def should_authenticate(self, path: str) -> bool:
        """判断路径是否需要认证"""
        # 不需要认证的路径
        public_paths = [
            "/",
            "/api/auth/login",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        
        # 静态文件不需要认证
        if path.startswith("/assets/") or path.endswith(".html") or path.endswith(".js") or path.endswith(".css"):
            return False
        
        # 检查是否在公开路径中
        for public_path in public_paths:
            if path == public_path or path.startswith(public_path):
                return False
        
        # API路径需要认证（除了登录接口）
        if path.startswith("/api/"):
            return True
        
        return False