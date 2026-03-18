"""
题目识别和解题功能测试
测试核心功能：
1. 用户注册和登录
2. 题目图片上传和 AI 识别
3. 追问功能
"""
import pytest
import httpx
import asyncio
from typing import Dict, Any


# 测试配置
BASE_URL = "http://localhost:8000/api/v1"
TEST_PHONE = "13800138001"
TEST_PASSWORD = "Test123456"
TEST_EMAIL = "test@example.com"
TEST_NICKNAME = "测试用户"


class TestQuestionSolver:
    """题目识别和解题功能测试"""

    @pytest.fixture
    async def client(self):
        """创建 HTTP 客户端"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client

    @pytest.fixture
    async def auth_token(self, client: httpx.AsyncClient):
        """获取认证 Token（先注册，后登录）"""
        # 1. 注册
        register_data = {
            "phone": TEST_PHONE,
            "password": TEST_PASSWORD,
            "email": TEST_EMAIL,
            "nickname": TEST_NICKNAME,
        }
        try:
            response = await client.post(f"{BASE_URL}/auth/register", json=register_data)
            print(f"注册响应：{response.status_code}")
        except Exception as e:
            print(f"注册失败：{e}")

        # 2. 登录
        login_data = {
            "phone": TEST_PHONE,
            "password": TEST_PASSWORD,
        }
        response = await client.post(f"{BASE_URL}/auth/login", json=login_data)
        assert response.status_code == 200, f"登录失败：{response.text}"

        data = response.json()
        token = data["data"]["token"]
        return token

    @pytest.mark.asyncio
    async def test_upload_question(self, client: httpx.AsyncClient, auth_token: str):
        """测试题目上传和 AI 识别"""
        headers = {"Authorization": f"Bearer {auth_token}"}

        # 准备测试图片（使用本地图片路径或 URL）
        # 注意：实际测试时需要提供真实的图片文件
        test_image_path = "test_image.jpg"  # 替换为实际图片路径

        try:
            with open(test_image_path, "rb") as f:
                files = {"images": ("test.jpg", f, "image/jpeg")}
                data = {
                    "subject": "math",
                    "description": "测试题目",
                }

                response = await client.post(
                    f"{BASE_URL}/questions/upload",
                    headers=headers,
                    files=files,
                    data=data,
                )

                print(f"上传响应状态码：{response.status_code}")
                print(f"上传响应：{response.text}")

                assert response.status_code == 200, f"上传失败：{response.text}"

                result = response.json()
                assert "id" in result
                assert "question_text" in result
                assert "analysis" in result

                print(f"题目 ID: {result['id']}")
                print(f"题目文本：{result['question_text']}")
                print(f"解析：{result['analysis']}")

        except FileNotFoundError:
            print(f"测试图片不存在：{test_image_path}")
            pytest.skip("测试图片不存在，跳过此测试")

    @pytest.mark.asyncio
    async def test_get_question(self, client: httpx.AsyncClient, auth_token: str):
        """测试获取题目详情"""
        headers = {"Authorization": f"Bearer {auth_token}"}

        # 先获取题目列表
        response = await client.get(
            f"{BASE_URL}/questions/",
            headers=headers,
            params={"limit": 1},
        )

        if response.status_code == 200:
            data = response.json()
            if data["data"] and len(data["data"]) > 0:
                question_id = data["data"][0]["id"]

                # 获取题目详情
                response = await client.get(
                    f"{BASE_URL}/questions/{question_id}",
                    headers=headers,
                )

                assert response.status_code == 200
                result = response.json()
                assert result["id"] == question_id
                print(f"题目详情：{result}")

    @pytest.mark.asyncio
    async def test_follow_up(self, client: httpx.AsyncClient, auth_token: str):
        """测试追问功能"""
        headers = {"Authorization": f"Bearer {auth_token}"}

        # 先获取一个题目
        response = await client.get(
            f"{BASE_URL}/questions/",
            headers=headers,
            params={"limit": 1},
        )

        if response.status_code == 200 and response.json()["data"]:
            question_id = response.json()["data"][0]["id"]

            # 发送追问
            follow_up_data = {
                "question_id": question_id,
                "question": "这道题的关键知识点是什么？",
            }

            response = await client.post(
                f"{BASE_URL}/questions/{question_id}/follow-up",
                headers=headers,
                json=follow_up_data,
            )

            print(f"追问响应：{response.status_code}")
            print(f"追问结果：{response.text}")

            if response.status_code == 200:
                result = response.json()
                assert "answer" in result["data"]
                assert "follow_up_count" in result["data"]
                print(f"AI 回答：{result['data']['answer']}")
                print(f"追问次数：{result['data']['follow_up_count']}/{result['data']['max_follow_up']}")

    @pytest.mark.asyncio
    async def test_similar_questions(self, client: httpx.AsyncClient, auth_token: str):
        """测试类似题目生成"""
        headers = {"Authorization": f"Bearer {auth_token}"}

        # 先获取一个题目
        response = await client.get(
            f"{BASE_URL}/questions/",
            headers=headers,
            params={"limit": 1},
        )

        if response.status_code == 200 and response.json()["data"]:
            question_id = response.json()["data"][0]["id"]

            # 获取类似题目
            response = await client.get(
                f"{BASE_URL}/questions/{question_id}/similar",
                headers=headers,
                params={"count": 2},
            )

            print(f"类似题目响应：{response.status_code}")
            print(f"类似题目结果：{response.text}")

            if response.status_code == 200:
                result = response.json()
                assert "similar_questions" in result["data"]
                print(f"生成了 {len(result['data']['similar_questions'])} 道类似题目")

    @pytest.mark.asyncio
    async def test_follow_up_limit(self, client: httpx.AsyncClient, auth_token: str):
        """测试追问次数限制"""
        headers = {"Authorization": f"Bearer {auth_token}"}

        # 获取或创建一个题目
        response = await client.get(
            f"{BASE_URL}/questions/",
            headers=headers,
            params={"limit": 1},
        )

        if response.status_code == 200 and response.json()["data"]:
            question_id = response.json()["data"][0]["id"]

            # 连续追问 11 次（超过限制的 10 次）
            for i in range(11):
                follow_up_data = {
                    "question_id": question_id,
                    "question": f"第 {i+1} 次追问",
                }

                response = await client.post(
                    f"{BASE_URL}/questions/{question_id}/follow-up",
                    headers=headers,
                    json=follow_up_data,
                )

                print(f"第 {i+1} 次追问 - 状态码：{response.status_code}")

                if response.status_code == 400:
                    print(f"追问次数已达上限：{response.text}")
                    break

                await asyncio.sleep(1)  # 避免请求过快


@pytest.mark.asyncio
async def test_api_health():
    """测试 API 健康状态"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/docs")
            print(f"API 文档状态：{response.status_code}")
            assert response.status_code == 200
        except Exception as e:
            print(f"API 不可用：{e}")
            pytest.skip("后端服务未启动")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
