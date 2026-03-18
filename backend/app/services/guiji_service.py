"""
硅基流动 API 服务
提供视觉模型调用能力（题目识别、解题、知识点提取）
"""
import base64
import mimetypes
import aiohttp
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.core.config import settings


class GuijiService:
    """硅基流动 API 服务"""

    def __init__(self):
        self.api_key = settings.GUIJI_API_KEY
        self.api_base = settings.GUIJI_API_BASE
        self.model = settings.GUIJI_MODEL
        self.temperature = settings.GUIJI_TEMPERATURE
        self.max_tokens = settings.GUIJI_MAX_TOKENS

        # 初始化 LLM
        self.llm = ChatOpenAI(
            base_url=self.api_base,
            api_key=self.api_key,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

    async def encode_image(self, image_path: str) -> str:
        """
        将图片编码为 base64 字符串

        Args:
            image_path: 图片路径（本地文件路径或网络 URL）

        Returns:
            base64 编码的图片字符串，格式：data:image/jpeg;base64,{base64_data}
        """
        if image_path.startswith("http://") or image_path.startswith("https://"):
            # 下载网络图片
            async with aiohttp.ClientSession() as session:
                async with session.get(image_path) as response:
                    if response.status == 200:
                        image_content = await response.read()
                    else:
                        raise Exception(f"下载图片失败：{response.status}")

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

    async def analyze_question(
        self,
        image_urls: List[str],
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析题目图片

        Args:
            image_urls: 图片 URL 列表（1-5 张）
            description: 用户补充描述（可选）

        Returns:
            包含题目文本、解答、知识点的字典
        """
        # 构建消息内容
        content = []

        # 添加图片
        for image_url in image_urls:
            base64_image = await self.encode_image(image_url)
            content.append({
                "type": "image_url",
                "image_url": {"url": base64_image}
            })

        # 添加文本指令
        text_instruction = self._build_analysis_prompt(description)
        content.append({
            "type": "text",
            "text": text_instruction
        })

        # 调用模型
        messages = [HumanMessage(content=content)]
        response = await self.llm.ainvoke(messages)

        # 解析响应
        result = self._parse_response(response.content)
        return result

    def _build_analysis_prompt(self, description: Optional[str] = None) -> str:
        """
        构建分析提示词

        Args:
            description: 用户补充描述

        Returns:
            提示词字符串
        """
        prompt = """你是一名专业的学习助手。请识别图片中的题目，并完成以下任务：

1. **题目识别**：准确识别图片中的题目内容（包括公式、图表等）
2. **题目解答**：提供详细的解题步骤，每一步都要有清晰的说明
3. **知识点提取**：列出题目涉及的所有知识点，并标注难度（基础/进阶/提高）
4. **题目类型**：判断题目的类型（选择题、填空题、解答题等）
5. **科目分类**：判断题目所属科目（数学、物理、化学等）

请按照以下 JSON 格式返回结果：
```json
{
    "question_text": "识别后的题目文本",
    "question_type": "题目类型",
    "subject": "科目",
    "difficulty": "难度",
    "solution": "详细解题步骤",
    "knowledge_points": [
        {
            "name": "知识点名称",
            "level": "难度等级",
            "description": "知识点描述"
        }
    ]
}
```

注意：
- 解题步骤要详细、清晰
- 知识点要准确、完整
- 如果有多个图片，请综合分析
"""

        if description:
            prompt += f"\n\n用户补充说明：{description}"

        return prompt

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        解析模型响应

        Args:
            response_text: 模型返回的文本

        Returns:
            解析后的字典
        """
        import json
        import re

        # 尝试提取 JSON 内容
        json_pattern = r'```json\s*(.*?)\s*```'
        match = re.search(json_pattern, response_text, re.DOTALL)

        if match:
            json_str = match.group(1)
        else:
            # 如果没有找到 JSON 块，尝试直接解析
            json_str = response_text

        try:
            result = json.loads(json_str)
            return {
                "question_text": result.get("question_text", ""),
                "question_type": result.get("question_type", "解答题"),
                "subject": result.get("subject", "未知"),
                "difficulty": result.get("difficulty", "基础"),
                "solution": result.get("solution", ""),
                "knowledge_points": result.get("knowledge_points", []),
            }
        except json.JSONDecodeError:
            # 解析失败，返回原始响应
            return {
                "question_text": "识别失败",
                "question_type": "未知",
                "subject": "未知",
                "difficulty": "基础",
                "solution": response_text,
                "knowledge_points": [],
            }

    async def answer_follow_up(
        self,
        question_text: str,
        previous_context: List[Dict[str, str]],
        follow_up_question: str
    ) -> str:
        """
        回答追问

        Args:
            question_text: 原题目文本
            previous_context: 之前的对话历史
            follow_up_question: 追问内容

        Returns:
            追问回答
        """
        # 构建对话历史
        messages = []

        # 系统提示
        system_prompt = f"""你是一名专业的学习助手。当前题目：{question_text}

请回答学生的追问，要求：
- 回答准确、详细
- 循循善诱，引导学生思考
- 使用清晰的结构和格式"""

        messages.append({"role": "system", "content": system_prompt})

        # 添加对话历史
        for msg in previous_context:
            messages.append(msg)

        # 添加当前追问
        messages.append({"role": "user", "content": follow_up_question})

        # 调用模型
        response = await self.llm.ainvoke(messages)
        return response.content


# 全局单例
guiji_service = GuijiService()
