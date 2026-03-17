module.exports = {
  // 服务器配置
  server: {
    host: '0.0.0.0',
    port: process.env.BFF_PORT || 3000,
  },

  // FastAPI 后端地址
  backend: {
    baseUrl: process.env.BACKEND_URL || 'http://localhost:8000',
    apiPrefix: '/api/v1',
  },

  // JWT 配置
  jwt: {
    secret: process.env.JWT_SECRET || 'your-secret-key-change-in-production',
    expiresIn: '1d',
  },

  // CORS 配置
  cors: {
    origin: process.env.ALLOWED_ORIGINS?.split(',') || '*',
    credentials: true,
  },

  // 日志配置
  logging: {
    level: process.env.LOG_LEVEL || 'info',
    prettyPrint: process.env.NODE_ENV !== 'production',
  },
};
