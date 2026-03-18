"""
LangChain Agent 工具
提供题目识别、解题、知识点提取等工具
"""
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from app.services.guiji_service import guiji_service


@tool
async def recognize_question(
    image_urls: List[str],
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    识别题目图片

    识别用户上传的题目图片，提取题目文本并初步分析。

    Args:
        image_urls: 题目图片 URL 列表（1-5 张）
        description: 用户补充描述（可选）

    Returns:
        包含题目文本、类型、科目等信息的字典
    """
    try:
        result = await guiji_service.analyze_question(image_urls, description)
        return {
            "success": True,
            "question_text": result["question_text"],
            "question_type": result["question_type"],
            "subject": result["subject"],
            "difficulty": result["difficulty"],
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@tool
async def solve_question(
    question_text: str,
    image_urls: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    解答题目

    根据题目文本和图片提供详细的解题步骤和答案。

    Args:
        question_text: 题目文本
        image_urls: 题目图片 URL 列表（可选，用于辅助解答）

    Returns:
        包含解题步骤、答案、知识点的字典
    """
    try:
        # 如果有图片，使用图片 + 文本分析
        if image_urls:
            result = await guiji_service.analyze_question(image_urls, question_text)
        else:
            # 仅文本解答
            prompt = f"""请解答以下题目，提供详细的解题步骤：

题目：{question_text}

要求：
1. 给出详细的解题步骤，每一步都要有清晰的说明
2. 如果有公式，请清晰展示
3. 最后给出答案
4. 提取题目涉及的知识点

请以 JSON 格式返回：
```json
{{
    "solution": "详细解题步骤",
    "answer": "最终答案",
    "knowledge_points": [
        {{"name": "知识点名称", "level": "难度", "description": "描述"}}
    ]
}}
```"""

            from langchain_core.messages import HumanMessage
            response = await guiji_service.llm.ainvoke([HumanMessage(content=prompt)])
            result = guiji_service._parse_response(response.content)

        return {
            "success": True,
            "solution": result["solution"],
            "answer": result.get("answer", ""),
            "knowledge_points": result["knowledge_points"],
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@tool
async def extract_knowledge_points(
    question_text: str,
    solution: str
) -> Dict[str, Any]:
    """
    提取知识点

    从题目和解答中提取所有涉及的知识点，并标注难度等级。

    Args:
        question_text: 题目文本
        solution: 解题步骤

    Returns:
        包含知识点列表的字典
    """
    try:
        prompt = f"""从以下题目和解答中提取所有涉及的知识点：

题目：{question_text}

解答：{solution}

要求：
1. 列出所有核心知识点
2. 标注每个知识点的难度（基础/进阶/提高）
3. 提供简短的描述
4. 按重要性排序

请以 JSON 格式返回：
```json
{{
    "knowledge_points": [
        {{
            "name": "知识点名称",
            "level": "基础 | 进阶 | 提高",
            "description": "知识点描述",
            "importance": "高 | 中 | 低"
        }}
    ]
}}
```"""

        from langchain_core.messages import HumanMessage
        response = await guiji_service.llm.ainvoke([HumanMessage(content=prompt)])
        result = guiji_service._parse_response(response.content)

        return {
            "success": True,
            "knowledge_points": result.get("knowledge_points", []),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@tool
async def generate_similar_questions(
    question_text: str,
    knowledge_points: List[Dict[str, Any]],
    count: int = 3
) -> Dict[str, Any]:
    """
    生成类似题目

    基于原题的知识点生成类似的练习题。

    Args:
        question_text: 原题目文本
        knowledge_points: 知识点列表
        count: 生成数量（默认 3 道）

    Returns:
        包含类似题目列表的字典
    """
    try:
        kp_text = "\n".join([f"- {kp['name']}: {kp['description']}" for kp in knowledge_points])

        prompt = f"""基于以下题目和知识点，生成{count}道类似的练习题：

原题目：{question_text}

涉及知识点：
{kp_text}

要求：
1. 每道题目都要考察相同的知识点
2. 题目难度相近
3. 提供详细的答案和解析
4. 题目之间要有变化，不要简单重复

请以 JSON 格式返回：
```json
{{
    "similar_questions": [
        {{
            "question": "题目内容",
            "answer": "答案",
            "solution": "解析",
            "difficulty": "基础 | 进阶 | 提高"
        }}
    ]
}}
```"""

        from langchain_core.messages import HumanMessage
        response = await guiji_service.llm.ainvoke([HumanMessage(content=prompt)])
        result = guiji_service._parse_response(response.content)

        return {
            "success": True,
            "similar_questions": result.get("similar_questions", []),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@tool
async def answer_follow_up(
    question_text: str,
    follow_up_question: str,
    conversation_history: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    回答追问

    在对话模式下回答学生关于题目的追问。

    Args:
        question_text: 原题目文本
        follow_up_question: 追问内容
        conversation_history: 对话历史

    Returns:
        包含追问回答的字典
    """
    try:
        answer = await guiji_service.answer_follow_up(
            question_text,
            conversation_history,
            follow_up_question
        )

        return {
            "success": True,
            "answer": answer,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
