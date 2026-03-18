# 硅基流动视觉模型 API 调用测试经验总结

## 📅 测试时间
2026-03-18

## 🎯 测试目标
验证硅基流动平台视觉模型 API 的调用方法，实现题目图片上传、识别、解答功能。

---

## ✅ 测试结论

### 1. 模型选择

#### ❌ 不可用模型
- **THUDM/GLM-4.1V-9B-Thinking**
  - 状态：API 返回 500 错误
  - 错误信息：`{"code": 50507, "message": "Request processing failed due to an unknown error."}`
  - 原因：模型可能已下线或需要特殊权限

#### ✅ 可用模型
- **Qwen/Qwen2.5-VL-72B-Instruct**（通义千问视觉语言模型）
  - 状态：✅ 正常工作
  - 能力：
    - ✅ 图片识别（OCR）
    - ✅ 文本理解
    - ✅ 多模态推理
    - ✅ 公式和图表解析
  - API 配置：
    ```python
    model = "Qwen/Qwen2.5-VL-72B-Instruct"
    base_url = "https://api.siliconflow.cn/v1"
    temperature = 0.7
    max_tokens = 2048
    ```

---

## 📝 正确的调用方法

### 1. 环境准备

#### 1.1 安装依赖
```bash
pip install openai langchain-openai langchain-core
```

#### 1.2 配置环境变量
```bash
# .env 文件
GUIJI_API_KEY=sk-wgffeealqezrbzdcycwqimxffvhypuqjzqfirmdpndmdcstl
GUIJI_API_BASE=https://api.siliconflow.cn/v1
GUIJI_MODEL=Qwen/Qwen2.5-VL-72B-Instruct
GUIJI_TEMPERATURE=0.7
GUIJI_MAX_TOKENS=2048
```

---

### 2. 使用 OpenAI SDK 调用（推荐）

#### 2.1 基础示例
```python
from openai import OpenAI
import base64

# 初始化客户端
client = OpenAI(
    api_key="sk-wgffeealqezrbzdcycwqimxffvhypuqjzqfirmdpndmdcstl",
    base_url="https://api.siliconflow.cn/v1"
)

# 读取并编码图片
with open("question.png", "rb") as f:
    image_content = f.read()
base64_image = base64.b64encode(image_content).decode()

# 构建请求
response = client.chat.completions.create(
    model="Qwen/Qwen2.5-VL-72B-Instruct",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                },
                {
                    "type": "text",
                    "text": "请识别这张图片中的数学题目，返回题目文本和答案。"
                }
            ]
        }
    ],
    temperature=0.7,
    max_tokens=2048
)

# 获取响应
print(response.choices[0].message.content)
```

---

### 3. 使用 LangChain 调用

#### 3.1 初始化 LLM
```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# 初始化
llm = ChatOpenAI(
    base_url="https://api.siliconflow.cn/v1",
    api_key="sk-wgffeealqezrbzdcycwqimxffvhypuqjzqfirmdpndmdcstl",
    model="Qwen/Qwen2.5-VL-72B-Instruct",
    temperature=0.7,
    max_tokens=2048,
)

# 构建消息
image_base64 = "data:image/png;base64,..."  # 你的 base64 图片
content = [
    {
        "type": "image_url",
        "image_url": {"url": image_base64}
    },
    {
        "type": "text",
        "text": "请识别这张图片中的数学题目，返回题目文本和答案。"
    }
]

messages = [HumanMessage(content=content)]

# 调用
response = await llm.ainvoke(messages)
print(response.content)
```

---

### 4. 使用 requests 直接调用

#### 4.1 基础示例
```python
import requests
import base64
import json

API_KEY = "sk-wgffeealqezrbzdcycwqimxffvhypuqjzqfirmdpndmdcstl"
API_URL = "https://api.siliconflow.cn/v1/chat/completions"

# 读取图片
with open("question.png", "rb") as f:
    image_content = f.read()
base64_image = base64.b64encode(image_content).decode()

# 构建请求
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "Qwen/Qwen2.5-VL-72B-Instruct",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                },
                {
                    "type": "text",
                    "text": "请识别这张图片中的数学题目，返回题目文本和答案。"
                }
            ]
        }
    ],
    "temperature": 0.7,
    "max_tokens": 2048
}

# 发送请求
response = requests.post(API_URL, headers=headers, json=payload)

if response.status_code == 200:
    result = response.json()
    print(result["choices"][0]["message"]["content"])
else:
    print(f"错误：{response.status_code}")
    print(f"错误信息：{response.text}")
```

---

## 🔧 常见问题与解决方案

### 问题 1: 500 错误 - Model disabled
```json
{"code": 30003, "message": "Model disabled."}
```
**原因**: 使用的模型已下线或不可用  
**解决方案**: 更换为 Qwen/Qwen2.5-VL-72B-Instruct

---

### 问题 2: 500 错误 - Request processing failed
```json
{"code": 50507, "message": "Request processing failed due to an unknown error."}
```
**原因**: 
1. 模型不可用（如 GLM-4.1V-9B-Thinking）
2. API Key 无效
3. 图片格式错误

**解决方案**:
1. ✅ 确认使用 Qwen/Qwen2.5-VL-72B-Instruct 模型
2. ✅ 检查 API Key 是否正确
3. ✅ 确保图片 base64 格式正确：`data:image/png;base64,{base64_data}`

---

### 问题 3: 配置不生效
**现象**: 修改了 config.py 但模型还是旧的  
**原因**: `.env` 文件覆盖了配置  
**解决方案**: 
```bash
# 同时修改两个文件
1. backend/app/core/config.py
2. backend/.env
```

---

## 📊 性能对比

| 模型 | 状态 | 响应时间 | 识别准确率 | 推荐度 |
|------|------|----------|------------|--------|
| THUDM/GLM-4.1V-9B-Thinking | ❌ 500 错误 | - | - | ❌ 不推荐 |
| Qwen/Qwen2.5-VL-72B-Instruct | ✅ 正常 | ~2-3 秒 | 高 | ✅ 强烈推荐 |

---

## 🎓 最佳实践

### 1. 图片处理
```python
# ✅ 推荐：直接传递图片二进制内容
with open("question.png", "rb") as f:
    image_content = f.read()
base64_image = base64.b64encode(image_content).decode()
image_url = f"data:image/png;base64,{base64_image}"

# ❌ 不推荐：先保存文件再读取 URL
# 会增加不必要的 I/O 操作
```

### 2. 错误处理
```python
try:
    response = await llm.ainvoke(messages)
    content = response.content
    # 解析 JSON 响应
    import json
    parsed = json.loads(content)
except Exception as e:
    print(f"调用失败：{e}")
    # 记录详细错误信息
```

### 3. 响应解析
```python
# 模型可能返回 Markdown 格式的 JSON
import re

def parse_response(response_text: str):
    # 提取 JSON 部分
    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_str = response_text
    
    return json.loads(json_str)
```

---

## 📚 参考资料

### 官方文档
- [SiliconFlow 产品介绍](https://docs.siliconflow.cn/cn/userguide/introduction)
- [SiliconFlow 模型列表](https://docs.siliconflow.cn/quickstart/models)
- [SiliconFlow 多模态模型](https://docs.siliconflow.cn/capabilities/vision)

### 代码示例
- [backend/app/services/simple_question_solver.py](../../backend/app/services/simple_question_solver.py)
- [backend/test_upload_debug.py](../../backend/test_upload_debug.py)

---

## 📝 更新日志

| 日期 | 内容 | 状态 |
|------|------|------|
| 2026-03-18 | 初始版本，记录 GLM 模型不可用问题 | ✅ |
| 2026-03-18 | 确认 Qwen2.5-VL 模型可用 | ✅ |
| 2026-03-18 | 添加完整调用示例和最佳实践 | ✅ |

---

## 💡 总结

1. **模型选择**: 使用 Qwen/Qwen2.5-VL-72B-Instruct，不要用 GLM-4.1V-9B-Thinking
2. **调用方式**: 推荐使用 OpenAI SDK 或 LangChain
3. **图片格式**: 使用 base64 编码，格式为 `data:image/png;base64,{base64_data}`
4. **配置管理**: 同时修改 config.py 和 .env 文件
5. **错误处理**: 捕获异常并记录详细错误信息

---

**文档维护**: 测试团队  
**最后更新**: 2026-03-18
