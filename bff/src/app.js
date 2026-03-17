const Fastify = require('fastify');
const cors = require('@fastify/cors');
const helmet = require('@fastify/helmet');
const compress = require('@fastify/compress');
const jwt = require('@fastify/jwt');
const formbody = require('@fastify/formbody');

const config = require('./config');
const authRoutes = require('./routes/auth.routes');
const userRoutes = require('./routes/user.routes');
const questionRoutes = require('./routes/question.routes');

// 创建 Fastify 实例
const buildApp = async () => {
  const app = Fastify({
    logger: {
      level: config.logging.level,
      transport: config.logging.prettyPrint
        ? {
            target: 'pino-pretty',
            options: {
              colorize: true,
              translateTime: 'SYS:standard',
            },
          }
        : undefined,
    },
  });

  // 注册插件
  await app.register(cors, config.cors);
  await app.register(helmet);
  await app.register(compress);
  await app.register(formbody);
  await app.register(jwt, {
    secret: config.jwt.secret,
    sign: {
      expiresIn: config.jwt.expiresIn,
    },
  });

  // 健康检查
  app.get('/health', async (request, reply) => {
    return {
      status: 'healthy',
      timestamp: new Date().toISOString(),
    };
  });

  // 注册路由
  await app.register(authRoutes, { prefix: '/api/auth' });
  await app.register(userRoutes, { prefix: '/api/users' });
  await app.register(questionRoutes, { prefix: '/api/questions' });

  // 全局错误处理
  app.setErrorHandler((error, request, reply) => {
    app.log.error(error);

    // JWT 错误
    if (error.code === 'FST_JWT_AUTHORIZATION_TOKEN_INVALID') {
      return reply.code(401).send({
        status: 'error',
        message: '无效的令牌',
      });
    }

    if (error.code === 'FST_JWT_AUTHORIZATION_TOKEN_MISSING') {
      return reply.code(401).send({
        status: 'error',
        message: '缺少令牌',
      });
    }

    // 默认错误
    return reply.code(error.statusCode || 500).send({
      status: 'error',
      message: error.message || '内部服务器错误',
    });
  });

  return app;
};

// 启动服务器
const start = async () => {
  const app = await buildApp();

  try {
    await app.listen({
      host: config.server.host,
      port: config.server.port,
    });

    console.log(`🚀 BFF 服务器运行在 http://${config.server.host}:${config.server.port}`);
    console.log(`📡 后端地址：${config.backend.baseUrl}${config.backend.apiPrefix}`);
  } catch (err) {
    app.log.error(err);
    process.exit(1);
  }
};

// 优雅关闭
const gracefulShutdown = async (signal) => {
  console.log(`\n${signal} 信号收到，开始优雅关闭...`);
  process.exit(0);
};

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

// 如果是主模块，启动服务
if (require.main === module) {
  start();
}

module.exports = { buildApp, start };
