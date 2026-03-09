"""
CircuitAI 后端 API 单元测试
使用 pytest + httpx 测试 FastAPI 端点（不依赖外部 AI API）
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# 设置 dummy key 以避免初始化报错
os.environ.setdefault("NVIDIA_API_KEY", "test-key")

import pytest
from httpx import AsyncClient, ASGITransport
from main import app, tasks


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.anyio
async def test_root(client):
    r = await client.get("/")
    assert r.status_code == 200
    assert "CircuitAI" in r.json().get("service", "")


@pytest.mark.anyio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


@pytest.mark.anyio
async def test_task_not_found(client):
    r = await client.get("/api/v1/task/nonexistent")
    assert r.status_code == 404


@pytest.mark.anyio
async def test_export_bom_csv(client):
    """测试 BOM CSV 导出（注入 mock 任务数据）"""
    tid = "test-bom-1"
    tasks[tid] = {
        "status": "done",
        "result": {
            "bom": [
                {"index": 1, "name": "电阻", "model": "10K 0603", "quantity": 5, "remarks": "上拉"},
                {"index": 2, "name": "电容", "model": "100nF", "quantity": 3, "remarks": "去耦"},
            ]
        },
        "created": __import__("time").time(),
    }
    r = await client.get(f"/api/v1/task/{tid}/export-bom")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    body = r.text
    assert "电阻" in body
    assert "10K 0603" in body
    assert "电容" in body
    # cleanup
    del tasks[tid]


@pytest.mark.anyio
async def test_export_bom_no_data(client):
    tid = "test-bom-empty"
    tasks[tid] = {"status": "done", "result": {"bom": []}, "created": __import__("time").time()}
    r = await client.get(f"/api/v1/task/{tid}/export-bom")
    assert r.status_code == 404
    del tasks[tid]


@pytest.mark.anyio
async def test_export_bom_not_done(client):
    tid = "test-bom-pending"
    tasks[tid] = {"status": "processing", "result": None, "created": __import__("time").time()}
    r = await client.get(f"/api/v1/task/{tid}/export-bom")
    assert r.status_code == 400
    del tasks[tid]
