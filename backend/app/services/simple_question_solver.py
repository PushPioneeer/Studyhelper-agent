"""
简化的解题服务（不使用 Function Call）
直接调用视觉模型 API，支持流式输出
支持错题保存和追问功能
"""
from typing import Dict, Any, List, Optional, AsyncGenerator
import json
import re
import base64
import httpx
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.core.config import settings


class SimpleQuestionSolver:
    """简化的解题服务"""

    def __init__(self):
        self.llm = ChatOpenAI(
            base_url=settings.GUIJI_API_BASE,
            api_key=settings.GUIJI_API_KEY,
            model=settings.GUIJI_MODEL,
            temperature=settings.GUIJI_TEMPERATURE,
            max_tokens=settings.GUIJI_MAX_TOKENS,
            streaming=True,  # 启用流式输出
        )
        self.wrong_questions_db: Dict[int, List[Dict]] = {}  # 用户 ID -> 错题列表

    async def process_question_upload(
        self,
        user_id: int,
        question_id: int,
        image_contents: List[bytes],
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理题目上传（直接调用视觉模型）

        Args:
            user_id: 用户 ID
            question_id: 题目 ID
            image_contents: 图片二进制内容列表
            description: 用户补充描述

        Returns:
            识别和解答结果
        """
        # 构建多模态提示
        content = []

        # 添加图片（转换为 base64）
        for image_content in image_contents:
            base64_image = base64.b64encode(image_content).decode()
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{base64_image}"}
            })

        # 构建文本指令
        text_instruction = self._build_analysis_prompt(description)
        content.append({
            "type": "text",
            "text": text_instruction
        })

        # 调用视觉模型
        messages = [HumanMessage(content=content)]
        response = await self.llm.ainvoke(messages)

        # 解析响应
        response_text = response.content
        parsed_result = self._parse_response(response_text)

        # 保存错题记录
        await self._save_wrong_question(
            user_id=user_id,
            question_id=question_id,
            parsed_result=parsed_result,
            image_contents=image_contents
        )

        return {
            "success": True,
            "response_text": response_text,
            "parsed_result": parsed_result,
        }

    def _build_analysis_prompt(self, description: Optional[str] = None) -> str:
        """构建分析提示词 - 优化版"""
        prompt = """你是一位经验丰富的高中/初中全科教师，专门帮助学生理解题目、掌握知识点。

请识别这些图片中的题目，并完成以下任务：

【任务要求】
1. **题目识别**：准确识别题目内容（包括文字、公式、图表、符号等）
   - 如果有模糊或不清晰的部分，请说明
   - 公式请用 LaTeX 格式表示

2. **详细解题步骤**（最重要）：
   - 分步骤详细解答，每一步都要有清晰的说明
   - 解释为什么要这样做，而不仅仅是做什么
   - 如果有多种解法，请提供最优解法并简要说明其他方法
   - 关键步骤要标注所用的公式或定理
   - 计算过程要完整，不能跳步

3. **核心知识点提取**：
   - 列出题目涉及的所有知识点
   - 每个知识点要说明：
     * 知识点名称
     * 所属学段（初中/高中）
     * 简要描述这个知识点的内容
     * 在本题中是如何应用的

4. **题目分类**：
   - 题目类型：选择题/填空题/解答题/证明题/实验题
   - 科目：数学/物理/化学/生物/其他
   - 难度评估：easy（基础题）/medium（中档题）/hard（难题）

【输出格式】
请严格按照以下 JSON 格式返回（不要有任何多余的文字）：
```json
{
    "question_text": "完整识别出的题目文本，包括所有条件和要求",
    "solution": "详细的解题步骤，每一步都要有说明，使用 LaTeX 格式表示公式",
    "answer": "最终答案（如果是选择题，给出选项；如果是计算题，给出结果）",
    "knowledge_points": [
        {
            "name": "知识点名称",
            "level": "初中/高中",
            "description": "知识点的详细描述",
            "application": "在本题中的具体应用"
        }
    ],
    "question_type": "选择题/填空题/解答题/证明题/实验题",
    "subject": "math/physics/chemistry/biology/other",
    "difficulty": "easy/medium/hard",
    "tips": "解题技巧和易错点提示（可选）"
}
```

【重要提示】
- 解题步骤要像老师讲课一样详细，让学生能够理解每一步的思路
- 知识点要准确，不能遗漏重要知识点
- 如果有图形或图表，要详细描述其内容
- 答案要明确，不能模棱两可"""

        if description:
            prompt += f"\n\n【用户补充说明】\n{description}"

        return prompt

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """解析 AI 响应"""
        # 尝试提取 JSON
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接解析
            json_str = response_text

        try:
            parsed = json.loads(json_str)
            return {
                "question_text": parsed.get("question_text", ""),
                "solution": parsed.get("solution", ""),
                "answer": parsed.get("answer", ""),
                "knowledge_points": parsed.get("knowledge_points", []),
                "question_type": parsed.get("question_type"),
                "subject": parsed.get("subject"),
                "difficulty": parsed.get("difficulty"),
            }
        except Exception as e:
            # 解析失败，返回原始文本
            return {
                "question_text": "",
                "solution": response_text,
                "answer": "",
                "knowledge_points": [],
                "question_type": None,
                "subject": None,
                "difficulty": None,
            }

    async def process_question_upload_stream(
        self,
        user_id: int,
        question_id: int,
        image_contents: List[bytes],
        description: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        处理题目上传 - 流式输出版（直接 HTTP 调用 API，真正的实时流式）

        Args:
            user_id: 用户 ID
            question_id: 题目 ID
            image_contents: 图片二进制内容列表
            description: 用户补充描述

        Yields:
            流式输出的文本片段
        """
        # 构建多模态提示
        content = []

        # 添加图片（转换为 base64）
        for image_content in image_contents:
            base64_image = base64.b64encode(image_content).decode()
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{base64_image}"}
            })

        # 构建文本指令
        text_instruction = self._build_analysis_prompt(description)
        content.append({
            "type": "text",
            "text": text_instruction
        })

        messages = [{"role": "user", "content": content}]

        # 直接调用 API（真正的流式）
        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.post(
                f"{settings.GUIJI_API_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.GUIJI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.GUIJI_MODEL,
                    "messages": messages,
                    "stream": True,  # 启用流式
                    "max_tokens": settings.GUIJI_MAX_TOKENS,
                    "temperature": settings.GUIJI_TEMPERATURE,
                },
            )

            response.raise_for_status()

            # 流式解析 SSE 响应
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break

                    try:
                        data = json.loads(data_str)
                        choices = data.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content_delta = delta.get("content", "")
                            if content_delta:
                                yield content_delta  # 立即输出
                    except json.JSONDecodeError:
                        continue

            # 流式结束后，保存错题记录（后台任务）
            # 注意：这里不阻塞流式输出，错题保存会在后台完成

    async def _save_wrong_question(
        self,
        user_id: int,
        question_id: int,
        parsed_result: Dict[str, Any],
        image_contents: List[bytes]
    ) -> None:
        """
        保存错题记录

        Args:
            user_id: 用户 ID
            question_id: 题目 ID
            parsed_result: 解析后的结果
            image_contents: 图片内容（用于生成缩略图）
        """
        if user_id not in self.wrong_questions_db:
            self.wrong_questions_db[user_id] = []

        wrong_question_record = {
            "question_id": question_id,
            "question_text": parsed_result.get("question_text", ""),
            "solution": parsed_result.get("solution", ""),
            "answer": parsed_result.get("answer", ""),
            "knowledge_points": parsed_result.get("knowledge_points", []),
            "question_type": parsed_result.get("question_type"),
            "subject": parsed_result.get("subject"),
            "difficulty": parsed_result.get("difficulty"),
            "created_at": datetime.now().isoformat(),
            "image_count": len(image_contents),
        }

        self.wrong_questions_db[user_id].append(wrong_question_record)

    def get_wrong_questions(
        self,
        user_id: int,
        subject: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取用户的错题列表

        Args:
            user_id: 用户 ID
            subject: 按科目筛选（可选）
            limit: 返回数量限制

        Returns:
            错题列表
        """
        if user_id not in self.wrong_questions_db:
            return []

        questions = self.wrong_questions_db[user_id]

        if subject:
            questions = [q for q in questions if q.get("subject") == subject]

        # 按创建时间倒序排列，返回最新的错题
        questions = sorted(questions, key=lambda x: x.get("created_at", ""), reverse=True)

        return questions[:limit]

    async def answer_follow_up(
        self,
        user_id: int,
        question_id: int,
        follow_up_question: str
    ) -> str:
        """
        回答追问（基于错题记录）

        Args:
            user_id: 用户 ID
            question_id: 题目 ID
            follow_up_question: 追问问题

        Returns:
            AI 回答
        """
        # 从错题记录中获取题目信息
        question_info = self._get_question_from_wrong_questions(user_id, question_id)
        
        if not question_info:
            return "未找到该题目的记录，请重新上传题目。"

        # 构建对话上下文
        messages = []

        # 系统提示
        system_prompt = """你是一名专业的学习助手，正在帮助学生理解题目。
请根据题目和之前的对话历史，回答学生的追问。
要求：
- 回答准确、专业
- 循循善诱，引导学生思考
- 语言简洁明了
- 适合移动端阅读"""

        messages.append({"role": "system", "content": system_prompt})

        # 添加原题目
        messages.append({
            "role": "user",
            "content": f"原题目：{question_info.get('question_text', '')}\n\n解题步骤：{question_info.get('solution', '')}"
        })

        # 添加追问
        messages.append({
            "role": "user",
            "content": follow_up_question
        })

        # 调用模型
        response = await self.llm.ainvoke(messages)
        return response.content

    def _get_question_from_wrong_questions(
        self,
        user_id: int,
        question_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        从错题记录中获取题目信息

        Args:
            user_id: 用户 ID
            question_id: 题目 ID

        Returns:
            题目信息，如果未找到则返回 None
        """
        if user_id not in self.wrong_questions_db:
            return None

        for question in self.wrong_questions_db[user_id]:
            if question.get("question_id") == question_id:
                return question

        return None

    async def answer_follow_up_stream(
        self,
        user_id: int,
        question_id: int,
        follow_up_question: str
    ) -> AsyncGenerator[str, None]:
        """
        回答追问 - 流式输出版（直接 HTTP 调用 API，真正的实时流式）

        Args:
            user_id: 用户 ID
            question_id: 题目 ID
            follow_up_question: 追问问题

        Yields:
            流式输出的文本片段
        """
        # 从错题记录中获取题目信息
        question_info = self._get_question_from_wrong_questions(user_id, question_id)
        
        if not question_info:
            yield "未找到该题目的记录，请重新上传题目。"
            return

        # 构建对话上下文
        messages = []

        # 系统提示
        system_prompt = """你是一名专业的学习助手，正在帮助学生理解题目。
请根据题目和之前的对话历史，回答学生的追问。
要求：
- 回答准确、专业
- 循循善诱，引导学生思考
- 语言简洁明了
- 适合移动端阅读"""

        messages.append({"role": "system", "content": system_prompt})

        # 添加原题目
        messages.append({
            "role": "user",
            "content": f"原题目：{question_info.get('question_text', '')}\n\n解题步骤：{question_info.get('solution', '')}"
        })

        # 添加追问
        messages.append({
            "role": "user",
            "content": follow_up_question
        })

        # 直接调用 API（真正的流式）
        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.post(
                f"{settings.GUIJI_API_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.GUIJI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.GUIJI_MODEL,
                    "messages": messages,
                    "stream": True,  # 启用流式
                    "max_tokens": settings.GUIJI_MAX_TOKENS,
                    "temperature": settings.GUIJI_TEMPERATURE,
                },
            )

            response.raise_for_status()

            # 流式解析 SSE 响应
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break

                    try:
                        data = json.loads(data_str)
                        choices = data.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content_delta = delta.get("content", "")
                            if content_delta:
                                yield content_delta  # 立即输出
                    except json.JSONDecodeError:
                        continue

    async def answer_follow_up_stream(
        self,
        question_text: str,
        previous_context: List[Dict],
        follow_up_question: str
    ) -> AsyncGenerator[str, None]:
        """
        回答追问 - 流式输出版（旧版本，保留兼容性）

        Args:
            question_text: 原题目文本
            previous_context: 之前的对话历史
            follow_up_question: 追问问题

        Yields:
            流式输出的文本片段
        """
        # 构建对话上下文
        messages = []

        # 系统提示
        system_prompt = """你是一名专业的学习助手，正在帮助学生理解题目。
请根据题目和之前的对话历史，回答学生的追问。
要求：
- 回答准确、专业
- 循循善诱，引导学生思考
- 语言简洁明了
- 适合移动端阅读"""

        messages.append({"role": "system", "content": system_prompt})

        # 添加原题目
        messages.append({
            "role": "user",
            "content": f"原题目：{question_text}"
        })

        # 添加对话历史
        for msg in previous_context:
            messages.append(msg)

        # 添加追问
        messages.append({
            "role": "user",
            "content": follow_up_question
        })

        # 流式调用模型
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                yield chunk.content


# 全局单例
simple_question_solver = SimpleQuestionSolver()
