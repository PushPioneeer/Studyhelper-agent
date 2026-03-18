"""
题目接口 - 支持图片上传、AI 识别、解题、追问
"""
import os
import uuid
import json
from typing import List, Optional, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.question import QuestionCreate, QuestionResponse, FollowUpRequest, QuestionAnalysisRequest
from app.api.dependencies import get_current_user
from app.schemas.user import UserResponse
from app.repositories.question_repository import question_repository
from app.services.simple_question_solver import simple_question_solver
from app.core.config import settings

router = APIRouter()


@router.post("/upload", response_model=QuestionResponse)
async def upload_question(
    images: List[UploadFile] = File(..., description="题目图片（1-5 张，JPG/PNG，单张≤10MB）"),
    subject: Optional[str] = Form(None, description="科目"),
    grade_level: Optional[str] = Form(None, description="年级"),
    description: Optional[str] = Form(None, description="题目描述"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    上传题目图片并调用 AI 识别解答

    - **images**: 题目图片文件列表（1-5 张）
    - **subject**: 科目（可选）
    - **grade_level**: 年级（可选）
    - **description**: 用户补充描述（可选）

    返回：
    - 题目识别结果
    - 详细解题步骤
    - 知识点清单
    """
    # 验证图片数量
    if len(images) < 1 or len(images) > 5:
        raise HTTPException(status_code=400, detail="图片数量必须在 1-5 张之间")

    # 验证图片格式和大小
    allowed_types = ["image/jpeg", "image/jpg", "image/png"]
    max_size = 10 * 1024 * 1024  # 10MB

    image_contents = []
    image_urls = []
    for image in images:
        # 检查文件类型
        if image.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail=f"不支持的图片格式：{image.content_type}")

        # 检查文件大小
        content = await image.read()
        if len(content) > max_size:
            raise HTTPException(status_code=400, detail=f"图片 {image.filename} 超过 10MB 限制")

        # 保存图片到本地（实际项目中应该上传到云存储）
        filename = f"{uuid.uuid4()}_{image.filename}"
        upload_dir = "uploads/questions"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)

        with open(file_path, "wb") as f:
            f.write(content)

        # 生成访问 URL（实际项目中应该是云存储 URL）
        image_url = f"http://localhost:8000/{file_path}"
        image_urls.append(image_url)
        image_contents.append(content)

    try:
        # 1. 创建题目记录（初始状态）
        question = await question_repository.create(
            db=db,
            user_id=current_user.id,
            image_url=image_urls[0],  # 主图
        )

        # 2. 调用 AI 识别和解答
        result = await simple_question_solver.process_question_upload(
            user_id=current_user.id,
            question_id=question.id,
            image_contents=image_contents,
            description=description,
        )

        # 3. 解析结果
        parsed = result["parsed_result"]

        # 4. 更新题目记录
        await question_repository.update_analysis(
            db=db,
            question_id=question.id,
            question_text=parsed.get("question_text", ""),
            analysis=parsed.get("solution", ""),
            knowledge_points=parsed.get("knowledge_points", []),
            question_type=parsed.get("question_type"),
            subject=parsed.get("subject") or subject,
            difficulty=parsed.get("difficulty"),
        )

        # 5. 刷新题目数据
        await db.refresh(question)

        return question

    except Exception as e:
        # 如果处理失败，删除创建的图片文件
        for image_url in image_urls:
            file_path = image_url.replace("http://localhost:8000/", "")
            if os.path.exists(file_path):
                os.remove(file_path)

        raise HTTPException(status_code=500, detail=f"题目识别失败：{str(e)}")


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    获取题目详情

    - **question_id**: 题目 ID
    """
    # 获取题目
    question = await question_repository.get_by_id(
        db=db,
        question_id=question_id,
        user_id=current_user.id
    )

    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")

    return question


@router.post("/{question_id}/follow-up")
async def follow_up_question(
    question_id: int,
    request: FollowUpRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    追问题目（对话式交互）

    - **question_id**: 题目 ID
    - **question**: 追问内容

    返回：
    - AI 回答
    - 剩余追问次数
    """
    # 1. 获取题目
    question = await question_repository.get_by_id(
        db=db,
        question_id=question_id,
        user_id=current_user.id
    )

    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")

    # 2. 检查追问次数
    if question.follow_up_count >= question.max_follow_up:
        raise HTTPException(
            status_code=400,
            detail=f"追问次数已达上限（{question.max_follow_up}次）",
        )

    try:
        # 3. 调用 Agent 回答追问
        result = await question_solver_agent.process_follow_up(
            user_id=current_user.id,
            question_id=question_id,
            question_text=question.question_text or "",
            follow_up_question=request.question,
            current_follow_up_count=question.follow_up_count,
        )

        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "追问失败"),
            )

        # 4. 增加追问次数
        new_count = await question_repository.increment_follow_up_count(
            db=db,
            question_id=question_id,
        )

        return JSONResponse(content={
            "status": "success",
            "message": "追问成功",
            "data": {
                "answer": result["answer"],
                "follow_up_count": new_count,
                "max_follow_up": question.max_follow_up,
                "remaining": question.max_follow_up - new_count,
            },
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"追问失败：{str(e)}")


@router.get("/wrong-questions/")
async def get_wrong_questions(
    subject: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    获取错题集列表

    - **subject**: 科目筛选（可选）
    - **limit**: 返回数量限制（默认 20）
    - **offset**: 偏移量（默认 0）

    返回：
    - 错题列表（包含题目、答案、解析、知识点）
    """
    try:
        # 从服务层获取错题
        wrong_questions = simple_question_solver.get_wrong_questions(
            user_id=current_user.id,
            subject=subject,
            limit=limit
        )

        return JSONResponse(content={
            "status": "success",
            "data": wrong_questions,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": len(wrong_questions),
            },
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取错题失败：{str(e)}")


@router.get("/wrong-questions/{question_id}")
async def get_wrong_question_detail(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    获取错题详情

    - **question_id**: 题目 ID
    """
    try:
        # 获取题目
        question = await question_repository.get_by_id(
            db=db,
            question_id=question_id,
            user_id=current_user.id
        )

        if not question:
            raise HTTPException(status_code=404, detail="题目不存在")

        # 从服务层获取错题详细信息
        wrong_questions = simple_question_solver.get_wrong_questions(
            user_id=current_user.id,
            limit=100
        )

        wrong_question = None
        for wq in wrong_questions:
            if wq.get("question_id") == question_id:
                wrong_question = wq
                break

        if not wrong_question:
            raise HTTPException(status_code=404, detail="错题记录不存在")

        return JSONResponse(content={
            "status": "success",
            "data": wrong_question,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取错题详情失败：{str(e)}")


@router.post("/{question_id}/follow-up/new")
async def follow_up_question_new(
    question_id: int,
    request: FollowUpRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    追问功能（新版本，基于错题记录）

    - **question_id**: 题目 ID
    - **question**: 追问内容

    返回：
    - AI 回答
    - 剩余追问次数
    """
    try:
        # 获取题目
        question = await question_repository.get_by_id(
            db=db,
            question_id=question_id,
            user_id=current_user.id
        )

        if not question:
            raise HTTPException(status_code=404, detail="题目不存在")

        # 检查追问次数
        if question.follow_up_count >= question.max_follow_up:
            raise HTTPException(
                status_code=400,
                detail=f"追问次数已达上限（{question.max_follow_up}次）",
            )

        # 调用服务层回答追问
        answer = await simple_question_solver.answer_follow_up(
            user_id=current_user.id,
            question_id=question_id,
            follow_up_question=request.question,
        )

        # 增加追问次数
        new_count = await question_repository.increment_follow_up_count(
            db=db,
            question_id=question_id,
        )

        return JSONResponse(content={
            "status": "success",
            "message": "追问成功",
            "data": {
                "answer": answer,
                "follow_up_count": new_count,
                "max_follow_up": question.max_follow_up,
                "remaining": question.max_follow_up - new_count,
            },
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"追问失败：{str(e)}")


@router.post("/{question_id}/follow-up/new/stream")
async def follow_up_question_stream_new(
    question_id: int,
    request: FollowUpRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    流式输出追问回答（新版本，基于错题记录）

    - **question_id**: 题目 ID
    - **question**: 追问问题
    """
    try:
        # 获取题目
        question = await question_repository.get_by_id(
            db=db,
            question_id=question_id,
            user_id=current_user.id
        )

        if not question:
            raise HTTPException(status_code=404, detail="题目不存在")

        # 检查追问次数
        if question.follow_up_count >= question.max_follow_up:
            raise HTTPException(
                status_code=400,
                detail=f"已达到最大追问次数限制（{question.max_follow_up}次）",
            )

        # 流式输出回答
        async def generate_stream():
            full_answer = ""
            try:
                async for chunk in simple_question_solver.answer_follow_up_stream(
                    user_id=current_user.id,
                    question_id=question_id,
                    follow_up_question=request.question,
                ):
                    full_answer += chunk
                    yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"
                
                # 更新追问记录
                new_count = question.follow_up_count + 1
                await question_repository.add_follow_up(
                    db=db,
                    question_id=question_id,
                    question=request.question,
                    answer=full_answer,
                )
                
                # 发送完成信号
                yield f"data: {json.dumps({'done': True, 'follow_up_count': new_count}, ensure_ascii=False)}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"追问失败：{str(e)}")


@router.post("/follow-up/new")
async def follow_up_question_direct(
    request: FollowUpRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    追问功能（直接通过 request 传递 question_id）

    - **question_id**: 题目 ID（在 request body 中）
    - **question**: 追问内容

    返回：
    - AI 回答
    - 剩余追问次数
    """
    try:
        question_id = request.question_id
        
        # 获取题目
        question = await question_repository.get_by_id(
            db=db,
            question_id=question_id,
            user_id=current_user.id
        )

        if not question:
            raise HTTPException(status_code=404, detail="题目不存在")

        # 检查追问次数
        if question.follow_up_count >= question.max_follow_up:
            raise HTTPException(
                status_code=400,
                detail=f"追问次数已达上限（{question.max_follow_up}次）",
            )

        # 调用服务层回答追问
        answer = await simple_question_solver.answer_follow_up(
            user_id=current_user.id,
            question_id=question_id,
            follow_up_question=request.question,
        )

        # 增加追问次数
        new_count = await question_repository.increment_follow_up_count(
            db=db,
            question_id=question_id,
        )

        return JSONResponse(content={
            "status": "success",
            "message": "追问成功",
            "data": {
                "answer": answer,
                "follow_up_count": new_count,
                "max_follow_up": question.max_follow_up,
                "remaining": question.max_follow_up - new_count,
            },
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"追问失败：{str(e)}")


@router.get("/{question_id}/similar")
async def get_similar_questions(
    question_id: int,
    count: int = 3,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    获取类似题目

    - **question_id**: 题目 ID
    - **count**: 生成数量（默认 3 道）
    """
    # 获取原题目
    question = await question_repository.get_by_id(
        db=db,
        question_id=question_id,
        user_id=current_user.id
    )

    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")

    if not question.knowledge_points:
        raise HTTPException(status_code=400, detail="原题目没有知识点信息")

    try:
        # 调用工具生成类似题目
        from app.services.agent_tools import generate_similar_questions

        result = await generate_similar_questions.ainvoke({
            "question_text": question.question_text or "",
            "knowledge_points": question.knowledge_points,
            "count": count,
        })

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "生成失败"))

        return JSONResponse(content={
            "status": "success",
            "data": {
                "original_question": {
                    "id": question.id,
                    "text": question.question_text,
                },
                "similar_questions": result["similar_questions"],
            },
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成类似题目失败：{str(e)}")


@router.get("/")
async def list_questions(
    subject: Optional[str] = None,
    question_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    获取题目列表

    - **subject**: 科目筛选（可选）
    - **question_type**: 题目类型筛选（可选）
    - **limit**: 返回数量限制（默认 20）
    - **offset**: 偏移量（默认 0）
    """
    questions = await question_repository.get_list(
        db=db,
        user_id=current_user.id,
        subject=subject,
        question_type=question_type,
        limit=limit,
        offset=offset,
    )

    return JSONResponse(content={
        "status": "success",
        "data": [QuestionResponse.model_validate(q).model_dump() for q in questions],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": len(questions),
        },
    })


@router.delete("/{question_id}")
async def delete_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    删除题目

    - **question_id**: 题目 ID
    """
    success = await question_repository.delete(
        db=db,
        question_id=question_id,
        user_id=current_user.id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="题目不存在")


@router.post("/upload/stream")
async def upload_question_stream(
    images: List[UploadFile] = File(..., description="题目图片（1-5 张，JPG/PNG，单张≤10MB）"),
    subject: Optional[str] = Form(None, description="科目"),
    grade_level: Optional[str] = Form(None, description="年级"),
    description: Optional[str] = Form(None, description="题目描述"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    上传题目图片并流式输出 AI 识别解答结果

    - **images**: 题目图片文件列表（1-5 张）
    - **subject**: 科目（可选）
    - **grade_level**: 年级（可选）
    - **description**: 用户补充描述（可选）

    返回：
    - 流式输出的 JSON 格式结果
    """
    # 验证图片数量
    if len(images) < 1 or len(images) > 5:
        raise HTTPException(status_code=400, detail="图片数量必须在 1-5 张之间")

    # 验证图片格式和大小
    allowed_types = ["image/jpeg", "image/jpg", "image/png"]
    max_size = 10 * 1024 * 1024  # 10MB

    image_contents = []
    image_urls = []
    for image in images:
        # 检查文件类型
        if image.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail=f"不支持的图片格式：{image.content_type}")

        # 检查文件大小
        content = await image.read()
        if len(content) > max_size:
            raise HTTPException(status_code=400, detail=f"图片 {image.filename} 超过 10MB 限制")

        # 保存图片到本地
        filename = f"{uuid.uuid4()}_{image.filename}"
        upload_dir = "uploads/questions"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)

        with open(file_path, "wb") as f:
            f.write(content)

        # 生成访问 URL
        image_url = f"http://localhost:8000/{file_path}"
        image_urls.append(image_url)
        image_contents.append(content)

    try:
        # 1. 创建题目记录（初始状态）
        question = await question_repository.create(
            db=db,
            user_id=current_user.id,
            image_url=image_urls[0],
        )

        # 2. 流式输出 AI 结果
        async def generate_stream():
            full_response = ""
            try:
                async for chunk in simple_question_solver.process_question_upload_stream(
                    user_id=current_user.id,
                    question_id=question.id,
                    image_contents=image_contents,
                    description=description,
                ):
                    full_response += chunk
                    # 每个 chunk 作为 SSE 事件发送
                    yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"
                
                # 流式输出完成后，解析完整响应并更新数据库
                from app.services.simple_question_solver import simple_question_solver as solver
                parsed_result = solver._parse_response(full_response)
                
                # 更新题目记录
                await question_repository.update_analysis(
                    db=db,
                    question_id=question.id,
                    question_text=parsed_result.get("question_text", ""),
                    analysis=parsed_result.get("solution", ""),
                    knowledge_points=parsed_result.get("knowledge_points", []),
                    question_type=parsed_result.get("question_type"),
                    subject=parsed_result.get("subject") or subject,
                    difficulty=parsed_result.get("difficulty"),
                )
                
                # 发送完成信号
                yield f"data: {json.dumps({'done': True, 'question_id': question.id}, ensure_ascii=False)}\n\n"
                
            except Exception as e:
                # 发送错误信号
                yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
                # 删除创建的图片文件
                for image_url in image_urls:
                    file_path = image_url.replace("http://localhost:8000/", "")
                    if os.path.exists(file_path):
                        os.remove(file_path)

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )

    except Exception as e:
        # 如果处理失败，删除创建的图片文件
        for image_url in image_urls:
            file_path = image_url.replace("http://localhost:8000/", "")
            if os.path.exists(file_path):
                os.remove(file_path)

        raise HTTPException(status_code=500, detail=f"题目识别失败：{str(e)}")


@router.post("/{question_id}/follow-up/stream")
async def follow_up_question_stream(
    question_id: int,
    request: FollowUpRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    流式输出追问回答

    - **question_id**: 题目 ID
    - **question**: 追问问题
    """
    try:
        # 获取题目
        question = await question_repository.get_by_id(
            db=db,
            question_id=question_id,
            user_id=current_user.id
        )

        if not question:
            raise HTTPException(status_code=404, detail="题目不存在")

        # 检查追问次数
        if question.follow_up_count >= question.max_follow_up:
            raise HTTPException(status_code=400, detail=f"已达到最大追问次数限制（{question.max_follow_up}次）")

        # 流式输出回答
        async def generate_stream():
            full_answer = ""
            try:
                async for chunk in simple_question_solver.answer_follow_up_stream(
                    question_text=question.question_text or "",
                    previous_context=question.follow_up_history or [],
                    follow_up_question=request.question,
                ):
                    full_answer += chunk
                    yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"
                
                # 更新追问记录
                new_count = question.follow_up_count + 1
                await question_repository.add_follow_up(
                    db=db,
                    question_id=question_id,
                    question=request.question,
                    answer=full_answer,
                )
                
                # 发送完成信号
                yield f"data: {json.dumps({'done': True, 'follow_up_count': new_count}, ensure_ascii=False)}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"追问失败：{str(e)}")
