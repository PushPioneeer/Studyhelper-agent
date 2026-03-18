"""
解题 Agent 服务
使用 LangChain create_agent 创建专业的解题助手
"""
from typing import Dict, Any, List, Optional
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage
from app.services.agent_tools import (
    recognize_question,
    solve_question,
    extract_knowledge_points,
    generate_similar_questions,
    answer_follow_up,
)
from app.core.config import settings


class QuestionSolverAgent:
    """解题 Agent 服务"""

    def __init__(self):
        self.llm = None  # 延迟初始化
        self.agent = None
        self.checkpointer = MemorySaver()
        self._initialized = False

    async def initialize(self):
        """初始化 Agent（异步）"""
        if self._initialized:
            return

        from langchain_openai import ChatOpenAI

        # 初始化 LLM
        self.llm = ChatOpenAI(
            base_url=settings.GUIJI_API_BASE,
            api_key=settings.GUIJI_API_KEY,
            model=settings.GUIJI_MODEL,
            temperature=settings.GUIJI_TEMPERATURE,
            max_tokens=settings.GUIJI_MAX_TOKENS,
        )

        # 定义工具
        tools = [
            recognize_question,
            solve_question,
            extract_knowledge_points,
            generate_similar_questions,
            answer_follow_up,
        ]

        # 系统提示
        system_prompt = """你是一名专业的移动端学习助手，专门帮助学生解答学习题目。

你的职责：
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
- 保持友好、鼓励的语气"""

        # 创建 Agent
        self.agent = create_agent(
            model=self.llm,
            tools=tools,
            system_prompt=system_prompt,
            checkpointer=self.checkpointer,
        )

        self._initialized = True

    async def process_question_upload(
        self,
        user_id: int,
        question_id: int,
        image_urls: List[str],
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理题目上传

        Args:
            user_id: 用户 ID
            question_id: 题目 ID
            image_urls: 图片 URL 列表
            description: 用户补充描述

        Returns:
            包含题目分析结果的字典
        """
        await self.initialize()

        # 配置会话（移动端需要 thread_id）
        config = {
            "configurable": {"thread_id": f"user:{user_id}:question:{question_id}"},
            "recursion_limit": 15,  # 防止无限循环
        }

        # 构建多模态消息（图片 + 文本）
        image_content = []
        for image_url in image_urls:
            image_content.append({
                "type": "image_url",
                "image_url": {"url": image_url}
            })

        text_instruction = f"""请识别这些图片中的题目，并完成以下任务：

1. 准确识别题目内容（包括公式、图表等）
2. 提供详细的解题步骤
3. 提取所有核心知识点
4. 判断题目类型和科目
5. 评估难度等级

{f'用户补充说明：{description}' if description else ''}

请以清晰的格式返回完整分析结果。"""

        image_content.append({
            "type": "text",
            "text": text_instruction
        })

        messages = [{"role": "user", "content": image_content}]

        # 调用 Agent
        result = await self.agent.ainvoke({"messages": messages}, config=config)

        # 提取结果
        response_text = result["messages"][-1].content

        # 解析响应
        parsed_result = self._parse_upload_response(response_text)

        return {
            "success": True,
            "response_text": response_text,
            "parsed_result": parsed_result,
        }

    async def process_follow_up(
        self,
        user_id: int,
        question_id: int,
        question_text: str,
        follow_up_question: str,
        current_follow_up_count: int
    ) -> Dict[str, Any]:
        """
        处理追问

        Args:
            user_id: 用户 ID
            question_id: 题目 ID
            question_text: 原题目文本
            follow_up_question: 追问内容
            current_follow_up_count: 当前追问次数

        Returns:
            包含追问回答的字典
        """
        await self.initialize()

        # 检查追问次数
        if current_follow_up_count >= settings.MAX_FOLLOW_UP_COUNT:
            return {
                "success": False,
                "error": "追问次数已达上限（10 次）",
                "code": "QUESTION_002",
            }

        # 配置会话
        config = {
            "configurable": {"thread_id": f"user:{user_id}:question:{question_id}"},
            "recursion_limit": 15,
        }

        # 构建追问消息
        prompt = f"""原题目：{question_text}

当前追问次数：{current_follow_up_count + 1}/{settings.MAX_FOLLOW_UP_COUNT}

学生追问：{follow_up_question}

请详细、耐心地回答学生的追问，帮助他理解题目。"""

        messages = [{"role": "user", "content": prompt}]

        # 调用 Agent
        result = await self.agent.ainvoke({"messages": messages}, config=config)

        # 提取回答
        answer = result["messages"][-1].content

        return {
            "success": True,
            "answer": answer,
            "new_follow_up_count": current_follow_up_count + 1,
        }

    def _parse_upload_response(self, response_text: str) -> Dict[str, Any]:
        """
        解析上传响应

        Args:
            response_text: Agent 返回的文本

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
            json_str = response_text

        try:
            result = json.loads(json_str)
            return {
                "question_text": result.get("question_text", ""),
                "question_type": result.get("question_type", "解答题"),
                "subject": result.get("subject", "未知"),
                "difficulty": result.get("difficulty", "基础"),
                "solution": result.get("solution", ""),
                "answer": result.get("answer", ""),
                "knowledge_points": result.get("knowledge_points", []),
            }
        except json.JSONDecodeError:
            # 解析失败，返回原始响应
            return {
                "question_text": "",
                "question_type": "解答题",
                "subject": "未知",
                "difficulty": "基础",
                "solution": response_text,
                "answer": "",
                "knowledge_points": [],
            }


# 全局单例
question_solver_agent = QuestionSolverAgent()
