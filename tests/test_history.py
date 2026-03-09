"""历史记录 API 测试"""
import time
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from services.task_store import TaskStore
import tempfile, os


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def temp_store():
    """使用临时数据库的TaskStore"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    store = TaskStore(db_path=path)
    yield store
    os.unlink(path)


class TestTaskStoreHistory:
    def test_list_completed_empty(self, temp_store):
        assert temp_store.list_completed() == []
        assert temp_store.count_completed() == 0

    def test_list_completed_with_data(self, temp_store):
        # 添加一个完成的任务
        temp_store["t1"] = {
            "status": "done",
            "created": time.time() - 100,
            "result": {
                "function": {"circuit_type": "LDO稳压电路"},
                "components": [{"ref": "U1"}, {"ref": "C1"}],
                "errors": [{"type": "missing_cap"}],
            },
        }
        # 添加一个进行中的任务（不应出现）
        temp_store["t2"] = {"status": "processing", "created": time.time()}

        items = temp_store.list_completed()
        assert len(items) == 1
        assert items[0]["task_id"] == "t1"
        assert items[0]["circuit_type"] == "LDO稳压电路"
        assert items[0]["component_count"] == 2
        assert items[0]["error_count"] == 1
        assert temp_store.count_completed() == 1

    def test_list_completed_order_and_limit(self, temp_store):
        for i in range(5):
            temp_store[f"t{i}"] = {
                "status": "done",
                "created": time.time() - (5 - i) * 10,
                "result": {},
            }
        items = temp_store.list_completed(limit=3)
        assert len(items) == 3
        # 最新的在前
        assert items[0]["task_id"] == "t4"

    def test_list_completed_offset(self, temp_store):
        for i in range(5):
            temp_store[f"t{i}"] = {
                "status": "done",
                "created": time.time() - (5 - i) * 10,
                "result": {},
            }
        items = temp_store.list_completed(limit=2, offset=3)
        assert len(items) == 2


class TestHistoryAPI:
    def test_history_endpoint(self, client):
        resp = client.get("/api/v1/history")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    def test_history_params(self, client):
        resp = client.get("/api/v1/history?limit=5&offset=0")
        assert resp.status_code == 200

    def test_history_invalid_limit(self, client):
        resp = client.get("/api/v1/history?limit=0")
        assert resp.status_code == 422
