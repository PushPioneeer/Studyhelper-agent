# 📝 题目识别和解题功能开发报告

## 📅 开发时间
2026-03-18

## 🎯 开发目标
实现题目拍照上传、AI 识别、智能解答、对话式追问等核心功能。

---

## ✅ 完成内容

### 1. 核心服务层

#### 1.1 硅基流动 API 服务
**文件**: `backend/app/services/guiji_service.py`

**功能**:
- ✅ 图片 base64 编码（支持本地文件和网络 URL）
- ✅ 题目图片分析（多模态输入）
- ✅ 追问回答生成
- ✅ 响应解析（JSON 格式提取）

**关键方法**:
```python
async def encode_image(image_path: str) -> str
async def analyze_question(image_urls: List[str], description: Optional[str]) -> Dict
async def answer_follow_up(question_text, previous_context, follow_up_question) -> str
```

**技术要点**:
- 使用 aiohttp 异步 HTTP 请求
- 支持多图片输入（1-5 张）
- 自动 MIME 类型识别
- JSON 响应智能解析

---

#### 1.2 LangChain Agent 工具
**文件**: `backend/app/services/agent_tools.py`

**工具列表**:
1. **recognize_question** - 题目识别工具
   - 输入：图片 URL 列表
   - 输出：题目文本、类型、科目、难度

2. **solve_question** - 解答题目工具
   - 输入：题目文本 + 可选图片
   - 输出：解题步骤、答案、知识点

3. **extract_knowledge_points** - 知识点提取工具
   - 输入：题目文本 + 解答
   - 输出：知识点列表（含难度等级）

4. **generate_similar_questions** - 类似题目生成工具
   - 输入：原题目 + 知识点
   - 输出：3-5 道类似题目

5. **answer_follow_up** - 追问回答工具
   - 输入：题目文本 + 对话历史 + 追问
   - 输出：追问回答

**技术要点**:
- 使用 `@tool` 装饰器定义
- 所有工具都是异步的
- 统一的错误处理
- 符合 LangChain 最佳实践

---

#### 1.3 解题 Agent 服务
**文件**: `backend/app/services/question_solver_agent.py`

**核心功能**:
```python
class QuestionSolverAgent:
    async def initialize()  # 初始化 Agent
    async def process_question_upload()  # 处理题目上传
    async def process_follow_up()  # 处理追问
```

**Agent 配置**:
- **模型**: Qwen/Qwen2.5-VL-72B-Instruct（通义千问视觉语言模型）
- **框架**: LangChain create_agent()
- **持久化**: MemorySaver checkpointer
- **会话 ID**: `thread_id = user:{user_id}:question:{question_id}`
- **递归限制**: 15（防止无限循环）

**System Prompt**:
```
你是一名专业的移动端学习助手，专门帮助学生解答学习题目。

职责：
1. 识别学生上传的题目图片
2. 提供详细、清晰的解题步骤
3. 提取题目涉及的核心知识点
4. 支持对话式追问，帮助学生深入理解
5. 生成类似题目供学生练习

要求：
- 回答准确、专业
- 解题步骤详细、易懂
- 循循善诱，引导学生思考
- 排版清晰、美观
- 适合移动端阅读

注意：
- 每道题目最多支持 10 次追问
- 追问次数用完后，礼貌地告知学生
- 保持友好、鼓励的语气
```

---

### 2. 数据访问层

#### 2.1 题目 Repository
**文件**: `backend/app/repositories/question_repository.py`

**核心方法**:
```python
async def create()  # 创建题目
async def get_by_id()  # 根据 ID 获取
async def get_list()  # 获取题目列表
async def update_analysis()  # 更新解析结果
async def increment_follow_up_count()  # 增加追问次数
async def get_follow_up_count()  # 获取追问次数
async def delete()  # 删除题目
```

**错题 Repository**:
```python
class WrongQuestionRepository:
    async def create()  # 创建错题记录
    async def get_by_user()  # 获取用户错题列表
    async def mark_mastered()  # 标记为已掌握
    async def delete()  # 删除错题记录
```

---

### 3. API 接口层

#### 3.1 题目接口
**文件**: `backend/app/api/v1/endpoints/questions.py`

**接口列表**:

1. **POST /api/v1/questions/upload**
   - 功能：上传题目图片并 AI 识别
   - 参数：images (1-5 张), subject, grade_level, description
   - 返回：题目详情（含解析、知识点）
   - 限流：每分钟 10 次

2. **GET /api/v1/questions/{question_id}**
   - 功能：获取题目详情
   - 返回：完整题目信息

3. **POST /api/v1/questions/{question_id}/follow-up**
   - 功能：对话式追问
   - 参数：question (追问内容)
   - 返回：AI 回答 + 剩余次数
   - 限制：最多 10 次

4. **GET /api/v1/questions/{question_id}/similar**
   - 功能：生成类似题目
   - 参数：count (默认 3)
   - 返回：类似题目列表

5. **GET /api/v1/questions/**
   - 功能：获取题目列表
   - 参数：subject, question_type, limit, offset
   - 返回：分页题目列表

6. **DELETE /api/v1/questions/{question_id}**
   - 功能：删除题目
   - 返回：删除结果

---

### 4. 测试文件

#### 4.1 单元测试
**文件**: `backend/tests/test_question_solver.py`

**测试用例**:
- ✅ API 健康检查
- ✅ 用户注册和登录
- ✅ 题目图片上传
- ✅ 获取题目详情
- ✅ 追问功能
- ✅ 类似题目生成
- ✅ 追问次数限制测试

#### 4.2 手动测试脚本
**文件**: `backend/test_api_manual.py`

**功能**:
- 交互式测试界面
- 支持真实图片上传
- 连续追问测试
- 题目列表查看

---

## 🔧 技术实现细节

### 1. LangChain Agent 最佳实践

✅ **使用 create_agent()**
```python
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver

agent = create_agent(
    model=llm,
    tools=[...],
    system_prompt="...",
    checkpointer=MemorySaver(),
)
```

✅ **会话持久化**
```python
config = {
    "configurable": {"thread_id": f"user:{user_id}:question:{question_id}"},
    "recursion_limit": 15,
}
result = await agent.ainvoke({"messages": messages}, config=config)
```

✅ **工具定义**
```python
from langchain_core.tools import tool

@tool
async def tool_name(param: str) -> Dict:
    """工具描述"""
    # 实现
```

---

### 2. 多模态输入处理

✅ **图片编码**
```python
async def encode_image(image_path: str) -> str:
    if image_path.startswith("http"):
        # 下载网络图片
        async with aiohttp.ClientSession() as session:
            async with session.get(image_path) as response:
                image_content = await response.read()
    else:
        # 读取本地文件
        with open(image_path, "rb") as f:
            image_content = f.read()
    
    base64_data = base64.b64encode(image_content).decode()
    mime_type, _ = mimetypes.guess_type(image_path)
    return f"data:{mime_type};base64,{base64_data}"
```

✅ **消息构建**
```python
content = []
for image_url in image_urls:
    base64_image = await encode_image(image_url)
    content.append({
        "type": "image_url",
        "image_url": {"url": base64_image}
    })
content.append({
    "type": "text",
    "text": text_instruction
})
messages = [HumanMessage(content=content)]
```

---

### 3. 错误处理

✅ **统一错误响应**
```python
try:
    result = await agent.process_question_upload(...)
    return result
except Exception as e:
    # 清理上传的文件
    for image_url in image_urls:
        file_path = image_url.replace("http://localhost:8000/", "")
        if os.path.exists(file_path):
            os.remove(file_path)
    raise HTTPException(status_code=500, detail=f"题目识别失败：{str(e)}")
```

✅ **追问次数检查**
```python
if question.follow_up_count >= question.max_follow_up:
    raise HTTPException(
        status_code=400,
        detail=f"追问次数已达上限（{question.max_follow_up}次）",
    )
```

---

## 📊 功能流程图

### 题目上传流程
```
用户上传图片
    ↓
验证图片（格式、大小、数量）
    ↓
保存到本地/云存储
    ↓
创建题目记录（初始状态）
    ↓
调用 Agent 识别和解答
    ↓
解析 AI 响应
    ↓
更新题目记录（解析、知识点）
    ↓
返回完整题目信息
```

### 追问流程
```
用户发送追问
    ↓
获取题目信息
    ↓
检查追问次数
    ↓
未超限 → 调用 Agent 回答
    ↓
增加追问计数
    ↓
返回 AI 回答 + 剩余次数
    ↓
已超限 → 返回错误提示
```

---

## 🎯 下一步计划

### 高优先级
1. ✅ 测试真实图片上传和识别
2. ✅ 验证追问对话连续性
3. ✅ 测试知识点提取准确性
4. ✅ 验证类似题目生成质量

### 中优先级
1. 错题集功能实现
2. 课件上传功能实现
3. 移动端 UI 开发
4. BFF 层路由转发

### 低优先级
1. 性能优化
2. 缓存策略
3. 日志系统
4. 监控告警

---

## 📝 注意事项

### 1. API Key 安全
- ⚠️ 当前 API Key 硬编码在配置中
- ✅ 建议使用环境变量
- ✅ 生产环境使用密钥管理服务

### 2. 文件存储
- ⚠️ 当前使用本地存储
- ✅ 生产环境建议使用云存储（AWS S3、阿里云 OSS）
- ✅ 需要实现文件 CDN 加速

### 3. 并发性能
- ✅ Agent 使用异步调用
- ✅ 数据库使用连接池
- ⚠️ 需要压力测试验证并发能力

### 4. 追问次数
- ✅ 硬性限制 10 次
- ✅ 数据库级别计数
- ⚠️ 需要考虑分布式场景下的计数一致性

---

## 🏆 技术亮点

1. **LangChain 最佳实践**
   - 使用 create_agent() 而非旧版 AgentExecutor
   - 正确的会话持久化
   - 规范的工具定义

2. **多模态处理**
   - 支持图片和文本混合输入
   - 自动 MIME 类型识别
   - 异步图片处理

3. **错误处理**
   - 统一的错误响应格式
   - 资源自动清理
   - 友好的错误提示

4. **代码组织**
   - 清晰的分层架构
   - Repository 模式
   - Service 层封装

---

## 📖 相关文档

- [需求分析](../docs/01-需求分析.md)
- [API 接口设计](../docs/04-API 接口设计.md)
- [部署和运维设计](../docs/06-部署和运维设计.md)
- [环境配置指南](../SETUP.md)

---

**报告生成时间**: 2026-03-18 21:20
**开发者**: AI Assistant
**状态**: ✅ 核心功能开发完成，等待测试验证
