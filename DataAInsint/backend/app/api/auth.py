from fastapi import APIRouter, HTTPException, status
from app.models.auth import LoginRequest, LoginResponse
from app.services.auth_service import AuthService

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """用户登录"""
    try:
        # 验证密钥
        if not AuthService.verify_secret_key(request.secret_key):
            return LoginResponse(
                success=False,
                message="密钥错误，请检查后重试"
            )
        
        # 生成token
        token = AuthService.generate_token()
        
        return LoginResponse(
            success=True,
            message="登录成功",
            token=token
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )

@router.post("/verify")
async def verify_token(authorization: str = None):
    """验证token有效性"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少Authorization header"
        )
    
    token = AuthService.extract_token_from_header(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的Authorization格式"
        )
    
    if not AuthService.verify_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token已过期或无效"
        )
    
    return {"message": "Token有效"}