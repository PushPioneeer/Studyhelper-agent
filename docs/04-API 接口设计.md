# 学习助手 - API 接口设计

## 1. API 设计规范

### 1.1 接口版本
- 当前版本：`v1`
- URL 前缀：`/api/v1`
- 版本管理：URL 路径版本控制

### 1.2 请求规范

**基础 URL**
```
开发环境：http://localhost:3000/api/v1
生产环境：https://api.studyhelper.com/api/v1
```

**请求头**
```http
Content-Type: application/json
Authorization: Bearer {token}
X-Device-Id: {device_id}
X-App-Version: 1.0.0
```

**时间格式**
- 请求/响应时间：ISO 8601 格式
- 示例：`2026-03-17T10:30:00Z`

### 1.3 响应格式

**成功响应**
```json
{
  "status": "success",
  "message": "操作成功",
  "data": {
    // 具体数据
  },
  "timestamp": "2026-03-17T10:30:00Z"
}
```

**错误响应**
```json
{
  "status": "error",
  "message": "错误描述",
  "code": "ERROR_CODE",
  "details": [
    {
      "field": "phone",
      "message": "手机号格式不正确"
    }
  ],
  "timestamp": "2026-03-17T10:30:00Z"
}
```

**分页响应**
```json
{
  "status": "success",
  "data": [],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "total_pages": 5
  },
  "timestamp": "2026-03-17T10:30:00Z"
}
```

### 1.4 状态码规范

**HTTP 状态码**
- `200` - 成功
- `201` - 创建成功
- `204` - 删除成功（无内容）
- `400` - 请求参数错误
- `401` - 未授权
- `403` - 禁止访问
- `404` - 资源不存在
- `409` - 资源冲突
- `429` - 请求过于频繁
- `500` - 服务器内部错误

**业务错误码**
```
USER_001 - 用户不存在
USER_002 - 手机号已注册
USER_003 - 验证码错误
USER_004 - 验证码已过期

AUTH_001 - Token 无效
AUTH_002 - Token 已过期
AUTH_003 - 未授权访问

QUESTION_001 - 题目识别失败
QUESTION_002 - 追问次数已达上限
QUESTION_003 - 题目不存在

COURSEWARE_001 - 文件解析失败
COURSEWARE_002 - 不支持的文件格式
COURSEWARE_003 - 文件过大

MISTAKE_001 - 错题不存在
MISTAKE_002 - 错题已被删除
```

---

## 2. 认证接口（移动端优化）

### 2.1 发送验证码

**接口**: `POST /api/v1/auth/sms/send`

**权限**: 公开

**限流**: 同一手机号 60 秒内只能请求 1 次

**请求**
```json
{
  "phone": "13800138000",
  "purpose": "login"
}
```

**响应**
```json
{
  "status": "success",
  "message": "验证码已发送",
  "data": {
    "expire_in": 300,
    "retry_after": 60
  },
  "timestamp": "2026-03-17T10:30:00Z"
}
```

**错误码**
- `USER_002` - 手机号未注册（登录时）
- `USER_003` - 手机号已注册（注册时）
- `429` - 发送过于频繁

**移动端优化**
- 前端倒计时显示（60 秒）
- 自动读取短信验证码（iOS/Android）
- 验证码键盘（数字键盘）

---

### 2.2 验证码登录

**接口**: `POST /api/v1/auth/login/sms`

**权限**: 公开

**限流**: 同一 IP 每分钟最多 10 次请求

**请求**
```json
{
  "phone": "13800138000",
  "code": "123456",
  "device_info": {
    "device_id": "device-uuid",
    "device_name": "iPhone 15",
    "os_version": "iOS 17.0",
    "app_version": "1.0.0"
  }
}
```

**响应**
```json
{
  "status": "success",
  "message": "登录成功",
  "data": {
    "user": {
      "id": "uuid",
      "phone": "138****8000",
      "nickname": "用户昵称",
      "avatar_url": "https://...",
      "school": "XX 大学",
      "major": "计算机科学"
    },
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 604800
  },
  "timestamp": "2026-03-17T10:30:00Z"
}
```

**移动端 Token 存储**
```typescript
// 使用 React Native SafeStorage 或 Expo SecureStore
import * as SecureStore from 'expo-secure-store';

// 存储 Token
await SecureStore.setItemAsync('auth_token', token);
await SecureStore.setItemAsync('refresh_token', refresh_token);

// 读取 Token
const token = await SecureStore.getItemAsync('auth_token');
```

---

### 2.3 密码登录

**接口**: `POST /api/v1/auth/login/password`

**请求**
```json
{
  "phone": "13800138000",
  "password": "password123",
  "device_info": {
    "device_id": "xxx",
    "device_name": "iPhone 15",
    "os_version": "iOS 17.0",
    "app_version": "1.0.0"
  }
}
```

**响应**
```json
{
  "status": "success",
  "data": {
    "user": {...},
    "token": "...",
    "refresh_token": "...",
    "expires_in": 604800
  }
}
```

---

### 2.4 刷新 Token

**接口**: `POST /api/v1/auth/refresh`

**请求**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**响应**
```json
{
  "status": "success",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 604800
  }
}
```

---

### 2.5 退出登录

**接口**: `POST /api/v1/auth/logout`

**请求头**
```
Authorization: Bearer {token}
```

**响应**
```json
{
  "status": "success",
  "message": "退出成功"
}
```

---

### 2.6 获取当前用户信息

**接口**: `GET /api/v1/auth/me`

**请求头**
```
Authorization: Bearer {token}
```

**响应**
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "phone": "138****8000",
    "nickname": "用户昵称",
    "avatar_url": "https://...",
    "school": "XX 大学",
    "major": "计算机科学",
    "grade": "大三",
    "preferred_subjects": ["数学", "物理"],
    "learning_style": "visual",
    "statistics": {
      "total_questions": 100,
      "total_mistakes": 20,
      "total_coursewares": 5
    }
  }
}
```

---

### 2.7 更新用户信息

**接口**: `PUT /api/v1/auth/profile`

**请求**
```json
{
  "nickname": "新昵称",
  "avatar_url": "https://...",
  "school": "新学校",
  "major": "新专业",
  "grade": "大四",
  "preferred_subjects": ["数学", "物理", "化学"],
  "learning_style": "auditory"
}
```

**响应**
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "nickname": "新昵称",
    ...
  }
}
```

---

## 3. 题目接口（Agent 核心）

### 3.1 上传题目图片

**接口信息**
- **路径**: `/api/v1/questions/upload`
- **方法**: `POST`
- **权限**: 需认证
- **限流**: 每分钟最多 10 次上传

**请求参数**
- Content-Type: `multipart/form-data`
- 参数：
  - `images`: 图片文件（必填，JPG/PNG，1-5 张，单张≤10MB）
  - `subject`: 科目（可选，如 math/physics/chemistry）
  - `grade_level`: 年级（可选，如 high/middle/elementary）
  - `description`: 题目描述（可选，用户输入的补充说明）

**响应示例**
```json
{
  "status": "success",
  "message": "题目识别成功",
  "data": {
    "question_id": "uuid",
    "original_text": "已知函数 f(x) = x² + 2x + 1，求 f(3) 的值。",
    "question_type": "解答题",
    "subject": "数学",
    "grade_level": "基础",
    "images": [
      {
        "url": "https://...",
        "width": 1920,
        "height": 1080
      }
    ],
    "solution": "解题步骤：\n1. 将 x=3 代入函数...\n2. 计算得...",
    "answer": "f(3) = 16",
    "knowledge_points": [
      {
        "name": "二次函数",
        "level": "基础",
        "description": "形如 y=ax²+bx+c 的函数"
      },
      {
        "name": "函数求值",
        "level": "基础",
        "description": "将自变量代入函数表达式计算"
      }
    ],
    "follow_up_count": 0,
    "max_follow_ups": 10,
    "estimated_time": 3,
    "created_at": "2026-03-17T10:30:00Z"
  },
  "timestamp": "2026-03-17T10:30:05Z"
}
```

**移动端优化**
- 前端图片压缩（压缩至 2MB 以内）
- 显示上传进度
- 支持拍照和相册选择
- 图片预览和裁剪

**错误码**
- `QUESTION_001` - 题目识别失败
- `400` - 图片格式不正确
- `400` - 图片过大

### 3.2 获取题目解析结果（Agent 调用）

**接口信息**
- **路径**: `/api/v1/questions/:question_id/result`
- **方法**: `GET`
- **权限**: 需认证
- **轮询**: 每 2 秒轮询一次，最多轮询 30 秒

**路径参数**
```
question_id: uuid
```

**响应示例**
```json
{
  "status": "success",
  "data": {
    "question_id": "uuid",
    "status": "completed",
    "question_text": "已知函数 f(x) = x² + 2x + 1，求 f(3) 的值。",
    "solution": "## 解题步骤\n\n**步骤 1**: 将 x = 3 代入函数\n\nf(3) = 3² + 2×3 + 1\n\n**步骤 2**: 计算各项\n\n= 9 + 6 + 1\n\n**步骤 3**: 得出结果\n\n= 16\n\n**答案**: f(3) = 16",
    "knowledge_points": [
      {
        "id": "kp-1",
        "name": "函数求值",
        "difficulty": "基础",
        "description": "将自变量代入函数表达式计算"
      },
      {
        "id": "kp-2",
        "name": "代数运算",
        "difficulty": "基础",
        "description": "平方、乘法、加法运算"
      }
    ],
    "follow_up_count": 0,
    "max_follow_ups": 10,
    "created_at": "2026-03-17T10:30:00Z"
  }
}
```

**Agent 处理流程（硅基流动 API 调用）**
```python
# 后端 Agent 调用流程 - 使用硅基流动 API
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver

async def process_question_upload(question_id: str, image_url: str):
    # 1. 配置硅基流动视觉模型
    llm = ChatOpenAI(
        base_url="https://api.siliconflow.cn/v1",
        api_key="sk-wgffeealqezrbzdcycwqimxffvhypuqjzqfirmdpndmdcstl",
        model="Qwen/Qwen2.5-VL-72B-Instruct",
        temperature=0.7,
        max_tokens=2048,
    )
    
    # 2. 创建 Agent（带持久化）
    checkpointer = MemorySaver()
    agent = create_agent(
        model=llm,
        tools=[],  # 可根据需要添加工具
        checkpointer=checkpointer,
        system_prompt="你是专业的学习助手，负责识别题目图片并解答"
    )
    
    # 3. 配置会话（移动端需要 thread_id）
    config = {
        "configurable": {"thread_id": f"user:{question_id}"},
        "recursion_limit": 15  # 防止无限循环
    }
    
    # 4. 构建多模态消息（图片 + 文本）
    messages = [{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": image_url}},
            {"type": "text", "text": "请识别这道题目并解答，给出详细步骤"}
        ]
    }]
    
    # 5. 调用 Agent
    result = await agent.ainvoke({"messages": messages}, config=config)
    
    # 6. 提取结果
    response_text = result["messages"][-1].content
    
    # 7. 解析结果（题目文本、解答、知识点）
    question_text = extract_question_text(response_text)
    solution = extract_solution(response_text)
    knowledge_points = extract_knowledge_points(response_text)
    
    # 8. 保存到数据库
    await save_question_result(question_id, {
        "question_text": question_text,
        "solution": solution,
        "knowledge_points": knowledge_points,
    })
```

**硅基流动 API 图片编码工具**
```python
import requests
import base64
import mimetypes

def encode_image(image_path: str) -> str:
    """
    将图片编码为 base64 字符串，供硅基流动 API 使用
    
    Args:
        image_path: 图片路径（本地文件路径或网络 URL）
    
    Returns:
        base64 编码的图片字符串，格式：data:image/jpeg;base64,{base64_data}
    """
    if image_path.startswith("http://") or image_path.startswith("https://"):
        # 下载网络图片
        response = requests.get(image_path)
        if response.status_code == 200:
            image_content = response.content
        else:
            raise Exception(f"下载图片失败：{response.status_code}")
        # 猜测 MIME 类型
        mime_type, _ = mimetypes.guess_type(image_path)
        if mime_type is None:
            mime_type = "application/octet-stream"
    else:
        # 读取本地文件
        with open(image_path, "rb") as f:
            image_content = f.read()
        mime_type, _ = mimetypes.guess_type(image_path)
        if mime_type is None:
            mime_type = "application/octet-stream"
    
    # 返回 base64 编码
    base64_data = base64.b64encode(image_content).decode()
    return f"data:{mime_type};base64,{base64_data}"

# 使用示例
# image_base64 = encode_image("question.jpg")  # 本地图片
# image_base64 = encode_image("https://example.com/question.png")  # 网络图片
```

**原生 HTTP 调用示例（不使用 LangChain）**
```python
import requests
import base64

API_KEY = "sk-wgffeealqezrbzdcycwqimxffvhypuqjzqfirmdpndmdcstl"
API_URL = "https://api.siliconflow.cn/v1/chat/completions"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# 准备图片（base64 编码）
with open("question.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()
    image_url = f"data:image/jpeg;base64,{image_data}"

# 构建请求
data = {
    "model": "Qwen/Qwen2.5-VL-72B-Instruct",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "请解答这道题目"},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        }
    ],
    "temperature": 0.7,
    "max_tokens": 2048
}

# 发送请求
response = requests.post(API_URL, headers=headers, json=data)
result = response.json()

# 解析结果
if result.get("choices"):
    content = result["choices"][0]["message"]["content"]
    print(content)  # AI 的回答
```

---

### 3.2 获取题目详情

**接口**: `GET /api/v1/questions/:question_id`

**响应**
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "original_text": "...",
    "question_type": "解答题",
    "subject": "数学",
    "images": [...],
    "solution": "...",
    "answer": "...",
    "knowledge_points": [...],
    "similar_questions": [
      {
        "id": "uuid",
        "question": "已知函数 g(x) = 2x² + 3x + 1，求 g(2) 的值。",
        "answer": "g(2) = 15",
        "difficulty": "基础"
      }
    ],
    "follow_up_count": 3,
    "max_follow_ups": 10,
    "follow_up_history": [
      {
        "id": "uuid",
        "message": "为什么要把 x=3 代入？",
        "response": "因为题目要求计算 f(3)，所以需要将 x=3 代入函数表达式...",
        "created_at": "2026-03-17T10:35:00Z"
      }
    ],
    "created_at": "2026-03-17T10:30:00Z",
    "completed_at": "2026-03-17T10:30:05Z"
  }
}
```

**错误码**
- `QUESTION_003` - 题目不存在

---

### 3.3 获取题目列表

**接口**: `GET /api/v1/questions`

**查询参数**
```
page: 1
limit: 20
subject: "math"  (可选)
start_date: "2026-01-01"  (可选)
end_date: "2026-03-17"  (可选)
```

**响应**
```json
{
  "status": "success",
  "data": [
    {
      "id": "uuid",
      "original_text": "...",
      "subject": "数学",
      "question_type": "解答题",
      "thumbnail": "https://...",
      "follow_up_count": 3,
      "created_at": "2026-03-17T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

---

### 3.4 追问功能（Agent 对话模式）

**接口信息**
- **路径**: `/api/v1/questions/:question_id/follow-up`
- **方法**: `POST`
- **权限**: 需认证
- **限流**: 每道题目每分钟最多 5 次追问
- **硬性限制**: 每道题目最多 10 次追问

**路径参数**
```
question_id: uuid
```

**请求参数**
```json
{
  "message": "为什么第二步要这样计算？",
  "parent_message_id": "msg-uuid"  // 可选，回复某条特定消息
}
```

**响应示例**
```json
{
  "status": "success",
  "data": {
    "follow_up_id": "uuid",
    "question_id": "uuid",
    "user_message": "为什么第二步要这样计算？",
    "agent_response": "很好的问题！在第二步中，我们将 x = 3 代入函数表达式，需要计算三项：\n\n1. **3²** = 9（3 的平方）\n2. **2×3** = 6（2 乘以 3）\n3. **常数项** = 1\n\n然后将这三项相加：9 + 6 + 1 = 16\n\n这样做的依据是**函数求值的基本规则**：将自变量的值代入函数表达式的每一个位置。",
    "follow_up_count": 1,
    "max_follow_ups": 10,
    "remaining_count": 9,
    "messages": [
      {
        "id": "msg-1",
        "role": "user",
        "content": "为什么第二步要这样计算？",
        "created_at": "2026-03-17T10:35:00Z"
      },
      {
        "id": "msg-2",
        "role": "assistant",
        "content": "很好的问题！...",
        "created_at": "2026-03-17T10:35:02Z"
      }
    ],
    "created_at": "2026-03-17T10:35:00Z"
  },
  "timestamp": "2026-03-17T10:35:00Z"
}
```

**错误响应（达到限制）**
```json
{
  "status": "error",
  "message": "追问次数已达上限",
  "code": "QUESTION_002",
  "details": {
    "follow_up_count": 10,
    "max_follow_ups": 10,
    "remaining_count": 0,
    "suggestion": "您可以重新上传新题目继续提问"
  },
  "timestamp": "2026-03-17T10:35:00Z"
}
```

**Agent 对话实现**
```python
# 追问 Agent 实现
async def handle_follow_up(question_id: str, user_id: str, message: str):
    # 1. 检查追问次数（硬性限制 10 次）
    count = await get_follow_up_count(question_id, user_id)
    if count >= 10:
        raise FollowUpLimitExceeded("追问次数已达上限")
    
    # 2. 获取历史对话
    history = await get_conversation_history(question_id, user_id)
    
    # 3. 创建 Agent 会话
    agent = create_question_agent()
    config = {
        "configurable": {
            "thread_id": f"{user_id}:{question_id}"
        },
        "recursion_limit": 15  # 防止无限循环
    }
    
    # 4. 构建对话消息
    messages = history + [{"role": "user", "content": message}]
    
    # 5. 调用 Agent
    result = await agent.ainvoke({
        "messages": messages
    }, config=config)
    
    # 6. 提取 Agent 回复
    agent_response = result["messages"][-1].content
    
    # 7. 保存对话记录
    await save_follow_up_message(question_id, user_id, {
        "user_message": message,
        "agent_response": agent_response
    })
    
    return {
        "follow_up_id": generate_id(),
        "agent_response": agent_response,
        "follow_up_count": count + 1,
        "remaining_count": 10 - (count + 1)
    }
```

**移动端 UI 设计**
```typescript
// 追问聊天界面组件
const FollowUpChat: React.FC<{ questionId: string }> = ({ questionId }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [remaining, setRemaining] = useState(10);
  
  const handleSend = async () => {
    if (!input.trim() || remaining <= 0) return;
    
    // 发送追问
    const response = await api.post(`/api/v1/questions/${questionId}/follow-up`, {
      message: input
    });
    
    // 更新消息列表
    setMessages([...messages, {
      role: 'user',
      content: input
    }, {
      role: 'assistant',
      content: response.data.agent_response
    }]);
    
    // 更新剩余次数
    setRemaining(response.data.remaining_count);
    setInput('');
  };
  
  if (remaining <= 0) {
    return (
      <EmptyState
        icon="chat-bubble-outline"
        title="追问次数已用完"
        description="每道题目最多支持 10 次追问，您可以重新上传新题目"
      />
    );
  }
  
  return (
    <View style={styles.chatContainer}>
      {/* 消息列表 - 使用 FlashList */}
      <FlashList
        data={messages}
        renderItem={({ item }) => (
          <ChatMessage
            role={item.role}
            content={item.content}
          />
        )}
        estimatedItemSize={80}
      />
      
      {/* 输入框 */}
      <View style={styles.inputArea}>
        <TextInput
          value={input}
          onChangeText={setInput}
          placeholder={`还剩${remaining}次追问机会`}
          multiline
        />
        <Button onPress={handleSend} disabled={!input.trim()}>
          发送
        </Button>
      </View>
      
      {/* 次数提示 */}
      <Text style={styles.counter}>
        已用 {10 - remaining}/10 次追问
      </Text>
    </View>
  );
};
```

**错误码**
- `QUESTION_002` - 追问次数已达上限
- `QUESTION_003` - 题目不存在

---

### 3.5 生成类似题目

**接口**: `POST /api/v1/questions/:question_id/similar`

**请求**
```json
{
  "count": 3,
  "difficulty": "same"  (same, easier, harder)
}
```

**响应**
```json
{
  "status": "success",
  "data": {
    "similar_questions": [
      {
        "id": "uuid",
        "question": "已知函数 g(x) = 2x² + 3x + 1，求 g(2) 的值。",
        "answer": "g(2) = 15",
        "solution": "...",
        "difficulty": "基础"
      }
    ]
  }
}
```

---

### 3.6 删除题目

**接口**: `DELETE /api/v1/questions/:question_id`

**响应**
```json
{
  "status": "success",
  "message": "题目已删除"
}
```

---

## 4. 课件接口

### 4.1 上传课件

**接口**: `POST /api/v1/coursewares/upload`

**请求类型**: `multipart/form-data`

**请求参数**
```
file: [file]  (PDF/PPT/PPTX/DOC/DOCX/MD)
```

**响应**
```json
{
  "status": "success",
  "message": "课件上传成功，开始解析",
  "data": {
    "courseware_id": "uuid",
    "original_filename": "高等数学课件.pdf",
    "file_type": "pdf",
    "file_size": 5242880,
    "task_id": "uuid",
    "parse_status": "pending",
    "parse_progress": 0,
    "estimated_time": 30
  },
  "timestamp": "2026-03-17T10:30:00Z"
}
```

**错误码**
- `COURSEWARE_002` - 不支持的文件格式
- `COURSEWARE_003` - 文件过大

---

### 4.2 查询解析进度

**接口**: `GET /api/v1/coursewares/:courseware_id/progress`

**响应**
```json
{
  "status": "success",
  "data": {
    "courseware_id": "uuid",
    "parse_status": "processing",
    "parse_progress": 60,
    "current_step": "正在生成笔记...",
    "estimated_remaining": 15
  }
}
```

---

### 4.3 获取课件详情

**接口**: `GET /api/v1/coursewares/:courseware_id`

**响应**
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "original_filename": "高等数学课件.pdf",
    "file_type": "pdf",
    "file_size": 5242880,
    "file_url": "https://...",
    "page_count": 50,
    "word_count": 10000,
    "parse_status": "completed",
    "notes": "# 高等数学课件笔记\n\n## 一、核心概念\n\n### 1.1 极限\n- 定义：...\n- 性质：...\n\n## 二、重要定理\n...",
    "notes_format": "markdown",
    "created_at": "2026-03-17T10:30:00Z",
    "completed_at": "2026-03-17T10:30:30Z"
  }
}
```

**错误码**
- `COURSEWARE_001` - 课件解析失败

---

### 4.4 获取课件列表

**接口**: `GET /api/v1/coursewares`

**查询参数**
```
page: 1
limit: 20
file_type: "pdf"  (可选)
status: "completed"  (可选)
```

**响应**
```json
{
  "status": "success",
  "data": [
    {
      "id": "uuid",
      "original_filename": "高等数学课件.pdf",
      "file_type": "pdf",
      "file_size": 5242880,
      "thumbnail": "https://...",
      "parse_status": "completed",
      "page_count": 50,
      "created_at": "2026-03-17T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 50,
    "total_pages": 3
  }
}
```

---

### 4.5 导出笔记

**接口**: `POST /api/v1/coursewares/:courseware_id/export`

**请求**
```json
{
  "format": "pdf"  (pdf, word, markdown)
}
```

**响应**
```json
{
  "status": "success",
  "data": {
    "download_url": "https://...",
    "expire_in": 3600
  }
}
```

---

### 4.6 删除课件

**接口**: `DELETE /api/v1/coursewares/:courseware_id`

**响应**
```json
{
  "status": "success",
  "message": "课件已删除"
}
```

---

## 5. 错题接口

### 5.1 获取错题列表

**接口**: `GET /api/v1/mistakes`

**查询参数**
```
page: 1
limit: 20
subject: "math"  (可选)
status: "new"  (可选：new, reviewing, mastered, archived)
error_type: "concept"  (可选)
tags: ["tag1", "tag2"]  (可选)
keyword: "函数"  (可选，搜索)
```

**响应**
```json
{
  "status": "success",
  "data": [
    {
      "id": "uuid",
      "original_text": "已知函数 f(x) = x² + 2x + 1，求 f(3) 的值。",
      "subject": "数学",
      "question_type": "解答题",
      "thumbnail": "https://...",
      "correct_answer": "16",
      "user_answer": "15",
      "error_type": "计算错误",
      "mastery_level": 0,
      "status": "new",
      "tags": ["函数", "二次函数"],
      "created_at": "2026-03-17T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

---

### 5.2 获取错题详情

**接口**: `GET /api/v1/mistakes/:mistake_id`

**响应**
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "original_text": "...",
    "images": [...],
    "subject": "数学",
    "question_type": "解答题",
    "correct_answer": "16",
    "user_answer": "15",
    "solution": "...",
    "knowledge_points": [...],
    "error_type": "计算错误",
    "error_analysis": "在计算 3² 时出错，应该是 9 而不是 8",
    "difficulty_level": "基础",
    "status": "new",
    "mastery_level": 0,
    "review_count": 0,
    "tags": ["函数", "二次函数"],
    "notes": "",
    "review_history": [],
    "created_at": "2026-03-17T10:30:00Z"
  }
}
```

---

### 5.3 更新错题

**接口**: `PUT /api/v1/mistakes/:mistake_id`

**请求**
```json
{
  "status": "reviewing",
  "mastery_level": 50,
  "tags": ["函数", "重要"],
  "notes": "这道题要注意计算准确性"
}
```

**响应**
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "status": "reviewing",
    "mastery_level": 50,
    ...
  }
}
```

---

### 5.4 删除错题

**接口**: `DELETE /api/v1/mistakes/:mistake_id`

**响应**
```json
{
  "status": "success",
  "message": "错题已删除"
}
```

---

### 5.5 批量更新错题状态

**接口**: `POST /api/v1/mistakes/batch-update`

**请求**
```json
{
  "mistake_ids": ["uuid1", "uuid2", "uuid3"],
  "status": "mastered"
}
```

**响应**
```json
{
  "status": "success",
  "message": "已更新 3 道错题的状态"
}
```

---

### 5.6 添加错题备注

**接口**: `POST /api/v1/mistakes/:mistake_id/notes`

**请求**
```json
{
  "notes": "这道题的关键是要注意..."
}
```

**响应**
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "notes": "这道题的关键是要注意..."
  }
}
```

---

### 5.7 添加错题标签

**接口**: `POST /api/v1/mistakes/:mistake_id/tags`

**请求**
```json
{
  "tags": ["重要", "易错"]
}
```

**响应**
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "tags": ["函数", "重要", "易错"]
  }
}
```

---

### 5.8 生成错题练习

**接口**: `POST /api/v1/mistakes/generate-practice`

**请求**
```json
{
  "mistake_ids": ["uuid1", "uuid2", "uuid3"],
  "count": 5
}
```

**响应**
```json
{
  "status": "success",
  "data": {
    "practice_id": "uuid",
    "questions": [
      {
        "question": "类似题目 1...",
        "answer": "...",
        "solution": "..."
      }
    ]
  }
}
```

---

### 5.9 创建错题整理

**接口**: `POST /api/v1/mistakes/create-collection`

**请求**
```json
{
  "name": "二次函数错题整理",
  "description": "整理二次函数相关错题",
  "mistake_ids": ["uuid1", "uuid2", "uuid3"],
  "format_template": {
    "include_original": true,
    "include_solution": true,
    "include_analysis": true,
    "format": "pdf"
  }
}
```

**响应**
```json
{
  "status": "success",
  "data": {
    "collection_id": "uuid",
    "status": "draft"
  }
}
```

---

### 5.10 导出错题整理

**接口**: `POST /api/v1/mistakes/collections/:collection_id/export`

**请求**
```json
{
  "format": "pdf"
}
```

**响应**
```json
{
  "status": "success",
  "data": {
    "download_url": "https://...",
    "expire_in": 3600
  }
}
```

---

## 6. 统计接口

### 6.1 获取学习统计

**接口**: `GET /api/v1/statistics/overview`

**查询参数**
```
start_date: "2026-01-01"
end_date: "2026-03-17"
```

**响应**
```json
{
  "status": "success",
  "data": {
    "summary": {
      "total_questions": 100,
      "total_correct": 80,
      "total_wrong": 20,
      "accuracy_rate": 0.8,
      "total_coursewares": 5,
      "total_mistakes": 20,
      "mastered_mistakes": 5,
      "total_study_time": 36000,
      "total_follow_ups": 50
    },
    "daily_stats": [
      {
        "date": "2026-03-17",
        "questions_solved": 10,
        "questions_correct": 8,
        "mistakes_added": 2,
        "study_time": 3600
      }
    ],
    "subject_distribution": [
      {
        "subject": "数学",
        "count": 50,
        "accuracy": 0.85
      },
      {
        "subject": "物理",
        "count": 30,
        "accuracy": 0.75
      }
    ]
  }
}
```

---

### 6.2 获取知识点掌握情况

**接口**: `GET /api/v1/statistics/knowledge`

**查询参数**
```
subject: "math"  (可选)
```

**响应**
```json
{
  "status": "success",
  "data": {
    "knowledge_points": [
      {
        "name": "二次函数",
        "subject": "数学",
        "mastery_level": 80,
        "question_count": 20,
        "correct_count": 16,
        "last_practiced": "2026-03-17T10:30:00Z"
      }
    ]
  }
}
```

---

### 6.3 获取学习趋势

**接口**: `GET /api/v1/statistics/trend`

**查询参数**
```
metric: "accuracy"  (accuracy, count, time)
period: "week"  (week, month, year)
```

**响应**
```json
{
  "status": "success",
  "data": {
    "trend_data": [
      {
        "date": "2026-03-11",
        "value": 0.75
      },
      {
        "date": "2026-03-12",
        "value": 0.78
      }
    ]
  }
}
```

---

## 7. 文件上传接口

### 7.1 获取上传凭证

**接口**: `POST /api/v1/upload/presigned-url`

**请求**
```json
{
  "file_type": "image",
  "file_size": 1048576,
  "content_type": "image/jpeg"
}
```

**响应**
```json
{
  "status": "success",
  "data": {
    "upload_url": "https://...",
    "file_url": "https://...",
    "expire_in": 3600
  }
}
```

---

## 8. WebSocket 接口

### 8.1 连接 WebSocket

**URL**: `wss://api.studyhelper.com/ws/v1`

**连接参数**
```
token: {jwt_token}
```

### 8.2 消息格式

**客户端发送**
```json
{
  "type": "subscribe",
  "channel": "courseware_progress",
  "data": {
    "courseware_id": "uuid"
  }
}
```

**服务端推送**
```json
{
  "type": "courseware_progress",
  "data": {
    "courseware_id": "uuid",
    "parse_status": "processing",
    "parse_progress": 60,
    "current_step": "正在生成笔记..."
  }
}
```

---

## 9. 限流策略

### 9.1 限流配置

```
全局限流：100 次/分钟/IP
登录接口：10 次/分钟
短信接口：5 次/分钟
上传题目：20 次/分钟
上传课件：10 次/分钟
追问接口：10 次/分钟
```

### 9.2 限流响应

**HTTP 429**
```json
{
  "status": "error",
  "message": "请求过于频繁，请稍后再试",
  "code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 60
}
```

---

## 10. 错误处理

### 10.1 通用错误响应

```json
{
  "status": "error",
  "message": "错误描述",
  "code": "ERROR_CODE",
  "details": [...],
  "timestamp": "2026-03-17T10:30:00Z",
  "path": "/api/v1/..."
}
```

### 10.2 验证错误

```json
{
  "status": "error",
  "message": "参数验证失败",
  "code": "VALIDATION_ERROR",
  "details": [
    {
      "field": "phone",
      "message": "手机号格式不正确"
    },
    {
      "field": "code",
      "message": "验证码必须是 6 位数字"
    }
  ]
}
```

---

## 11. 文档修订记录

| 版本 | 日期 | 修订内容 | 修订人 |
|-----|------|---------|--------|
| v1.0 | 2026-03-17 | 初始版本 | - |

---

## 12. 下一步

继续编写以下文档：

1. ✅ 需求分析文档
2. ✅ 系统架构设计
3. ✅ 数据库设计
4. ✅ API 接口设计（本文档）
5. ✅ 前端设计
6. ✅ 部署和运维设计

📋 **所有设计文档已完成，可以开始实现阶段！**
