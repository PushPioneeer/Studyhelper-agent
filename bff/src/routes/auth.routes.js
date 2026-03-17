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
 * 认证路由
 */
const authRoutes = async (fastify, options) => {
  // 登录
  fastify.post('/login', async (request, reply) => {
    try {
      const { phone, password } = request.body;

      const response = await proxyRequest(
        'POST',
        `${config.backend.apiPrefix}/auth/login`,
        { phone, password }
      );

      if (response.statusCode === 200) {
        // 设置 JWT
        const token = fastify.jwt.sign({
          userId: response.data.user.id,
          phone: response.data.user.phone,
        });

        reply.send({
          ...response.data,
          bff_token: token,
        });
      } else {
        reply.code(response.statusCode).send(response.data);
      }
    } catch (error) {
      request.log.error(error);
      reply.code(500).send({
        status: 'error',
        message: '登录失败',
      });
    }
  });

  // 注册
  fastify.post('/register', async (request, reply) => {
    try {
      const { phone, password, email, nickname } = request.body;

      const response = await proxyRequest(
        'POST',
        `${config.backend.apiPrefix}/auth/register`,
        { phone, password, email, nickname }
      );

      if (response.statusCode === 200) {
        reply.send(response.data);
      } else {
        reply.code(response.statusCode).send(response.data);
      }
    } catch (error) {
      request.log.error(error);
      reply.code(500).send({
        status: 'error',
        message: '注册失败',
      });
    }
  });

  // 刷新令牌
  fastify.post('/refresh', async (request, reply) => {
    try {
      const { refresh_token } = request.body;

      const response = await proxyRequest(
        'POST',
        `${config.backend.apiPrefix}/auth/refresh`,
        { refresh_token }
      );

      reply.send(response.data);
    } catch (error) {
      request.log.error(error);
      reply.code(500).send({
        status: 'error',
        message: '刷新令牌失败',
      });
    }
  });
};

module.exports = authRoutes;
