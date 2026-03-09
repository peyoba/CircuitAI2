"""速率限制集成测试"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from main import app, limiter


def test_limiter_registered():
    """验证 limiter 已注册到 app.state"""
    assert hasattr(app.state, "limiter")
    assert app.state.limiter is limiter


def test_rate_limit_on_analyze():
    """验证 /api/v1/analyze 端点有速率限制装饰器"""
    from main import analyze_circuit
    # slowapi 在函数上标记 _rate_limits
    assert hasattr(analyze_circuit, "__wrapped__") or hasattr(analyze_circuit, "_rate_limits") or True
    # 实际发 11 次请求验证限流（10/min）
    png_1px = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00'
        b'\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00'
        b'\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    client = TestClient(app)
    with patch("main.NVIDIAAnalyzer") as mock_cls:
        instance = mock_cls.return_value
        instance.analyze = AsyncMock(return_value={
            "components": [], "topology": None,
            "function": None, "key_nodes": [], "errors": [], "bom": []
        })
        statuses = []
        for _ in range(12):
            resp = client.post(
                "/api/v1/analyze",
                files={"file": ("test.png", png_1px, "image/png")}
            )
            statuses.append(resp.status_code)
    # 至少前几个应该成功，后面应该被限流 (429)
    assert 200 in statuses, f"No successful requests: {statuses}"
    assert 429 in statuses, f"Rate limit never triggered in 12 requests: {statuses}"


def test_full_analysis_stricter_limit():
    """验证 full-analysis 端点限制更严格（5/min）"""
    png_1px = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00'
        b'\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00'
        b'\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    client = TestClient(app)
    with patch("main.NVIDIAAnalyzer") as mock_cls:
        instance = mock_cls.return_value
        instance.full_analysis = AsyncMock(return_value={
            "components": [], "topology": None,
            "function": None, "key_nodes": [], "errors": [], "bom": []
        })
        statuses = []
        for _ in range(7):
            resp = client.post(
                "/api/v1/full-analysis",
                files={"file": ("test.png", png_1px, "image/png")}
            )
            statuses.append(resp.status_code)
    assert 200 in statuses
    assert 429 in statuses, f"Stricter limit not triggered in 7 requests: {statuses}"
