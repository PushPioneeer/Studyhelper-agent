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
 * 题目路由
 */
const questionRoutes = async (fastify, options) => {
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

  // 创建题目
  fastify.post('/', async (request, reply) => {
    try {
      const token = request.headers.authorization?.replace('Bearer ', '');
      const { image_url } = request.body;

      const response = await proxyRequest(
        'POST',
        `${config.backend.apiPrefix}/questions/`,
        { image_url },
        token
      );

      reply.send(response.data);
    } catch (error) {
      request.log.error(error);
      reply.code(500).send({
        status: 'error',
        message: '创建题目失败',
      });
    }
  });

  // 获取题目详情
  fastify.get('/:questionId', async (request, reply) => {
    try {
      const token = request.headers.authorization?.replace('Bearer ', '');
      const { questionId } = request.params;

      const response = await proxyRequest(
        'GET',
        `${config.backend.apiPrefix}/questions/${questionId}`,
        null,
        token
      );

      reply.send(response.data);
    } catch (error) {
      request.log.error(error);
      reply.code(500).send({
        status: 'error',
        message: '获取题目失败',
      });
    }
  });

  // 追问题目
  fastify.post('/:questionId/follow-up', async (request, reply) => {
    try {
      const token = request.headers.authorization?.replace('Bearer ', '');
      const { questionId } = request.params;
      const { question } = request.body;

      const response = await proxyRequest(
        'POST',
        `${config.backend.apiPrefix}/questions/${questionId}/follow-up`,
        { question_id: parseInt(questionId), question },
        token
      );

      reply.send(response.data);
    } catch (error) {
      request.log.error(error);
      reply.code(500).send({
        status: 'error',
        message: '追问失败',
      });
    }
  });
};

module.exports = questionRoutes;
