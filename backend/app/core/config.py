from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    # 应用配置
    APP_NAME: str = "学习助手 API"
    APP_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/study_helper"

    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 追问次数限制
    MAX_FOLLOW_UP_COUNT: int = 10

    # 硅基流动 API 配置
    GUIJI_API_KEY: str = "sk-wgffeealqezrbzdcycwqimxffvhypuqjzqfirmdpndmdcstl"
    GUIJI_API_BASE: str = "https://api.siliconflow.cn/v1"
    GUIJI_MODEL: str = "THUDM/GLM-4.1V-9B-Thinking"
    GUIJI_TEMPERATURE: float = 0.7
    GUIJI_MAX_TOKENS: int = 2048

    # CORS 配置
    ALLOWED_ORIGINS: str = "*"

    # BFF 配置（可选）
    BFF_PORT: int = 3000
    BACKEND_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()
