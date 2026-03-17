# 📚 学习助手 (Study Helper)

基于 React Native + FastAPI 的智能学习助手移动端应用。

## 🎯 项目简介

学习助手是一款智能学习应用，通过 AI 技术帮助学生：
- 📸 拍照识别题目，智能讲解
- 💬 对话式追问，深入理解知识点
- 📝 自动生成详细学习笔记
- 📚 错题集自动整理和例题生成
- 🎓 课件上传和智能解析

## 🚀 技术栈

### 移动端
- **框架**: React Native + TypeScript
- **开发工具**: Expo
- **BFF 层**: Node.js + Fastify

### 后端
- **API 框架**: FastAPI (Python)
- **Agent 框架**: LangChain
- **主数据库**: PostgreSQL
- **缓存/会话**: Redis

### AI 模型
- **视觉模型**: THUDM/GLM-4.1V-9B-Thinking (硅基流动)
- **OCR**: 集成在视觉模型中

## 📁 项目结构

```
study-helper/
├── mobile/              # React Native 移动端
│   ├── src/           # 源代码
│   ├── App.tsx        # 应用入口
│   └── package.json   # 依赖配置
│
├── backend/           # FastAPI 后端
│   ├── app/          # 应用代码
│   │   ├── api/      # API 路由
│   │   ├── core/     # 核心配置
│   │   ├── models/   # 数据模型
│   │   ├── schemas/  # 数据 Schema
│   │   ├── services/ # 业务逻辑
│   │   └── repositories/ # 数据访问层
│   ├── init-db/      # 数据库初始化脚本
│   ├── Dockerfile    # Docker 配置
│   └── requirements.txt # Python 依赖
│
├── bff/              # Node.js BFF 层
│   ├── src/         # 源代码
│   ├── Dockerfile   # Docker 配置
│   └── package.json # 依赖配置
│
├── docs/             # 项目文档
│   ├── 01-需求分析.md
│   ├── 02-系统架构设计.md
│   ├── 03-数据库设计.md
│   ├── 04-API 接口设计.md
│   ├── 05-前端设计.md
│   └── 06-部署和运维设计.md
│
├── docker-compose.yml  # Docker 编排
├── SETUP.md           # 环境配置指南
└── README.md          # 项目说明
```

## ✅ 当前状态

### 已完成
- ✅ 项目结构搭建
- ✅ FastAPI 后端基础框架
- ✅ Node.js BFF 层框架
- ✅ React Native + Expo 项目初始化
- ✅ PostgreSQL + Redis 数据库配置
- ✅ 用户认证系统（注册/登录/JWT）
- ✅ 数据库迁移和初始化

### 开发中
- ⏸️ 题目识别功能
- ⏸️ 对话式追问功能
- ⏸️ 错题集功能
- ⏸️ 课件上传功能
- ⏸️ 移动端 UI 开发

## 🛠️ 快速开始

### 环境要求

- Python 3.11+
- Node.js 20+
- Docker Desktop

### 1. 启动数据库

```bash
# 启动 PostgreSQL 和 Redis
docker-compose up -d postgres redis

# 查看状态
docker-compose ps
```

### 2. 启动后端服务

```bash
cd backend

# 激活虚拟环境
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# 或
source venv/bin/activate     # macOS/Linux

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**访问 API 文档**: http://localhost:8000/docs

### 3. 启动 BFF 层

```bash
cd bff

# 安装依赖（首次运行）
npm install

# 启动服务
npm run dev
```

**访问 BFF 服务**: http://localhost:3000

### 4. 启动移动端

```bash
cd mobile

# 安装依赖（首次运行）
npm install

# 启动 Expo
npm start
# 或
npx expo start
```

## 🧪 测试

### 后端 API 测试

```bash
cd backend
python -m pytest
```

详细测试报告查看：[backend/API_TEST_REPORT.md](backend/API_TEST_REPORT.md)

### 测试用户

- **手机号**: 13800138000
- **密码**: 123456

## 📊 API 端点

### 认证相关
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/refresh` - 刷新令牌

### 用户相关
- `GET /api/v1/users/me` - 获取当前用户信息
- `PUT /api/v1/users/me` - 更新用户信息

### 题目相关（开发中）
- `POST /api/v1/questions` - 创建题目
- `GET /api/v1/questions` - 获取题目列表
- `GET /api/v1/questions/{id}` - 获取题目详情
- `POST /api/v1/questions/{id}/follow-up` - 追问

## 📝 开发指南

### 数据库配置

数据库连接信息在 `backend/.env` 文件中配置：

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/study_helper
```

### 环境变量

#### 后端配置
```env
# 应用配置
APP_NAME=学习助手 API
APP_VERSION=1.0.0

# 安全配置
SECRET_KEY=your-secret-key-change-in-production

# 硅基流动 API
GUIJI_API_KEY=sk-wgffeealqezrbzdcycwqimxffvhypuqjzqfirmdpndmdcstl
GUIJI_API_BASE=https://api.siliconflow.cn/v1
GUIJI_MODEL=THUDM/GLM-4.1V-9B-Thinking
```

#### BFF 配置
```env
BACKEND_URL=http://localhost:8000
BFF_PORT=3000
JWT_SECRET=your-secret-key-change-in-production
```

## 🐛 常见问题

### Docker 容器无法启动
```bash
# 检查 Docker Desktop 是否运行
docker info

# 查看容器日志
docker-compose logs postgres
docker-compose logs redis
```

### 端口被占用
修改 `docker-compose.yml` 或 `.env` 文件中的端口配置。

### Python 虚拟环境问题
```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 📋 开发计划

### 短期目标（1-2 周）
- [ ] 实现题目识别功能（调用硅基流动 API）
- [ ] 实现对话式追问功能
- [ ] 实现错题集基础功能
- [ ] 开发移动端登录页面
- [ ] 开发移动端拍照上传功能

### 中期目标（1 个月）
- [ ] 实现课件上传和解析
- [ ] 完善错题集功能
- [ ] 实现学习笔记生成
- [ ] 优化移动端 UI/UX
- [ ] 添加单元测试

### 长期目标（3 个月）
- [ ] 性能优化
- [ ] 添加更多 AI 功能
- [ ] 用户反馈系统
- [ ] 数据分析和统计
- [ ] 多语言支持

## 🤝 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

- 项目仓库：https://github.com/yourusername/study-helper
- 问题反馈：请在 GitHub Issues 中提交

## 🙏 致谢

感谢以下开源项目：
- [FastAPI](https://fastapi.tiangolo.com/)
- [React Native](https://reactnative.dev/)
- [Expo](https://expo.dev/)
- [LangChain](https://www.langchain.com/)
- [硅基流动](https://www.siliconflow.cn/)

---

**最后更新**: 2026-03-18  
**项目状态**: 开发中 🚧
