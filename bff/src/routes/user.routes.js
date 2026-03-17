const http = require('http');
const config = require('../config');

/**
 * 向 FastAPI 后端发送请求
 */
async function proxyRequest(method, path, body = null, token = null) {
  const url = new URL(path, config.backend.baseUrl);
  
  const options = {
    hostname: url.hostname,
    port: url.port || 8000,
    path: url.pathname + url.search,
    method,
    headers: {
      'Content-Type': 'application/json',
    },
  };

  if (token) {
    options.headers['Authorization'] = `Bearer ${token}`;
  }

  return new Promise((resolve, reject) => {
    const req = http.request(options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        try {
          resolve({
            statusCode: res.statusCode,
            headers: res.headers,
            data: JSON.parse(data),
          });
        } catch (e) {
          resolve({
            statusCode: res.statusCode,
            headers: res.headers,
            data,
          });
        }
      });
    });

    req.on('error', reject);

    if (body) {
      req.write(JSON.stringify(body));
    }

    req.end();
  });
}

/**
 * 用户路由
 */
const userRoutes = async (fastify, options) => {
  // 添加 JWT 认证
  fastify.addHook('preHandler', async (request, reply) => {
    try {
      await request.jwtVerify();
    } catch (err) {
      reply.code(401).send({
        status: 'error',
        message: '未授权',
      });
    }
  });

  // 获取当前用户信息
  fastify.get('/me', async (request, reply) => {
    try {
      const token = request.headers.authorization?.replace('Bearer ', '');
      
      const response = await proxyRequest(
        'GET',
        `${config.backend.apiPrefix}/users/me`,
        null,
        token
      );

      reply.send(response.data);
    } catch (error) {
      request.log.error(error);
      reply.code(500).send({
        status: 'error',
        message: '获取用户信息失败',
      });
    }
  });

  // 更新当前用户信息
  fastify.patch('/me', async (request, reply) => {
    try {
      const token = request.headers.authorization?.replace('Bearer ', '');
      const { nickname, avatar_url, email } = request.body;

      const response = await proxyRequest(
        'PATCH',
        `${config.backend.apiPrefix}/users/me`,
        { nickname, avatar_url, email },
        token
      );

      reply.send(response.data);
    } catch (error) {
      request.log.error(error);
      reply.code(500).send({
        status: 'error',
        message: '更新用户信息失败',
      });
    }
  });

  // 获取指定用户信息
  fastify.get('/:userId', async (request, reply) => {
    try {
      const token = request.headers.authorization?.replace('Bearer ', '');
      const { userId } = request.params;

      const response = await proxyRequest(
        'GET',
        `${config.backend.apiPrefix}/users/${userId}`,
        null,
        token
      );

      reply.send(response.data);
    } catch (error) {
      request.log.error(error);
      reply.code(500).send({
        status: 'error',
        message: '获取用户信息失败',
      });
    }
  });
};

module.exports = userRoutes;
