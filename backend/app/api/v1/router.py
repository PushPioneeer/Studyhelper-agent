from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, questions, agents

# 创建 v1 版本路由器
api_router = APIRouter()

# 注册各个端点
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(questions.router, prefix="/questions", tags=["题目"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agent"])
