# 🚀 项目启动指南

## ✅ 环境配置完成

所有环境已经配置完成，项目结构已创建！

### 已完成的任务

- ✅ 创建项目目录结构
- ✅ 初始化 React Native + Expo 项目
- ✅ 创建 FastAPI 后端项目
- ✅ 创建 Node.js BFF 层
- ✅ 安装 Python 依赖（FastAPI、LangChain 等）
- ✅ 安装 Node.js 依赖
- ✅ 使用 Docker 启动 PostgreSQL 和 Redis
- ✅ 执行数据库迁移

---

## 📁 项目结构

```
d:\Desktop\test/
├── mobile/                    # React Native 移动端
│   ├── src/
│   ├── App.tsx
│   └── package.json
│
├── backend/                   # FastAPI 后端
│   ├── app/
│   │   ├── api/              # API 路由
│   │   ├── core/             # 核心配置
│   │   ├── db/               # 数据库模型
│   │   ├── services/         # 业务逻辑
│   │   ├── repositories/     # 数据访问层
│   │   └── agents/           # LangChain Agents
│   ├── venv/                 # Python 虚拟环境
│   ├── .env                  # 环境变量
│   ├── requirements.txt      # Python 依赖
│   └── Dockerfile
│
├── bff/                       # Node.js BFF 层
│   ├── src/
│   │   ├── routes/           # 路由
│   │   ├── controllers/      # 控制器
│   │   └── config/           # 配置
│   ├── node_modules/
│   ├── package.json
│   └── Dockerfile
│
├── docs/                      # 项目文档
│   ├── 01-需求分析.md
│   ├── 02-系统架构设计.md
│   ├── 03-数据库设计.md
│   ├── 04-API 接口设计.md
│   ├── 05-前端设计.md
│   └── 06-部署和运维设计.md
│
├── docker-compose.yml         # Docker 配置
└── .gitignore
```

---

## 🛠️ 启动服务

### 1. 启动数据库和缓存（Docker）

```powershell
# 启动 PostgreSQL 和 Redis
docker-compose up -d postgres redis

# 查看状态
docker-compose ps

# 停止服务
docker-compose down
```

**服务地址：**
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

---

### 2. 启动 FastAPI 后端

```powershell
# 进入后端目录
cd backend

# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 启动后端服务（开发模式）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或者使用生产模式
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**访问地址：**
- API 文档：http://localhost:8000/docs
- 备用文档：http://localhost:8000/redoc
- 健康检查：http://localhost:8000/health

---

### 3. 启动 Node.js BFF 层

```powershell
# 进入 BFF 目录
cd bff

# 启动服务（开发模式）
npm run dev

# 或者使用生产模式
npm start
```

**访问地址：**
- BFF 服务：http://localhost:3000
- 健康检查：http://localhost:3000/health

---

### 4. 启动 React Native 移动端

```powershell
# 进入移动端目录
cd mobile

# 启动 Expo 开发服务器
npm start

# 或者
npx expo start
```

**运行方式：**
- **Android**: 按 `a` 键（需要 Android 模拟器）
- **iOS**: 按 `i` 键（需要 macOS 和 iOS 模拟器）
- **Web**: 按 `w` 键（在浏览器中运行）
- **扫码**: 使用 Expo Go App 扫描二维码

---

## 🧪 测试 API

### 使用 cURL 测试

```bash
# 健康检查
curl http://localhost:8000/health

# 用户注册
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "13800138001",
    "password": "123456",
    "email": "test@example.com",
    "nickname": "测试用户"
  }'

# 用户登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "13800138000",
    "password": "123456"
  }'
```

### 使用 Postman

导入 API 文档或使用 Swagger UI: http://localhost:8000/docs

---

## 📊 数据库信息

### 已创建的表

- `users` - 用户表
- `questions` - 题目表
- `wrong_questions` - 错题表
- `learning_notes` - 学习笔记表
- `courseware` - 课件表

### 测试用户

- **手机号**: 13800138000
- **密码**: 123456

---

## 🔑 环境变量配置

### 后端 (.env)

```bash
# 数据库
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/study_helper

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# 安全
SECRET_KEY=your-secret-key-change-in-production

# 硅基流动 API
GUIJI_API_KEY=sk-wgffeealqezrbzdcycwqimxffvhypuqjzqfirmdpndmdcstl
GUIJI_API_BASE=https://api.siliconflow.cn/v1
GUIJI_MODEL=THUDM/GLM-4.1V-9B-Thinking
```

### BFF 环境

```bash
# .env 文件（需要创建）
BACKEND_URL=http://localhost:8000
BFF_PORT=3000
JWT_SECRET=your-secret-key-change-in-production
```

---

## 🐛 常见问题

### 1. Docker 容器无法启动

```powershell
# 检查 Docker Desktop 是否运行
docker info

# 查看容器日志
docker-compose logs postgres
docker-compose logs redis
```

### 2. 数据库连接失败

```powershell
# 检查 PostgreSQL 是否运行
docker-compose ps

# 测试连接
psql -h localhost -U postgres -d study_helper
```

### 3. 端口被占用

修改 `docker-compose.yml` 或 `.env` 文件中的端口配置。

### 4. Python 虚拟环境问题

```powershell
# 重新创建虚拟环境
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 5. Node.js 依赖问题

```powershell
# 重新安装依赖
cd bff
rm -rf node_modules package-lock.json
npm install
```

---

## 📝 下一步

1. **实现题目识别功能**
   - 调用硅基流动 API
   - 实现 OCR 和题目分析

2. **实现追问功能**
   - 实现对话历史管理
   - 限制追问次数

3. **实现错题集功能**
   - 错题自动收录
   - 错题整理和生成

4. **实现课件上传**
   - 文件上传处理
   - 课件内容解析

5. **完善移动端 UI**
   - 实现登录页面
   - 实现拍照上传
   - 实现题目展示

---

## 📞 技术支持

如有问题，请查看：
- 项目文档：`docs/` 目录
- API 文档：http://localhost:8000/docs
- Docker 日志：`docker-compose logs`

---

**祝开发愉快！** 🎉
