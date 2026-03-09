"""
文件上传校验测试 — 大小限制、空文件、类型校验
"""

import sys
import pytest

sys.path.insert(0, "/root/.openclaw/workspace/agents/coder/CircuitAI/backend")

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# 1x1 白色 PNG（最小合法 PNG）
TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
    b"\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00"
    b"\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_reject_empty_file():
    """空文件应返回 400"""
    resp = client.post("/api/v1/analyze", files={"file": ("empty.png", b"", "image/png")})
    assert resp.status_code == 400
    assert "为空" in resp.json()["detail"]


def test_reject_oversized_file():
    """超过 10MB 的文件应返回 413"""
    big = b"\x00" * (10 * 1024 * 1024 + 1)
    resp = client.post("/api/v1/analyze", files={"file": ("big.png", big, "image/png")})
    assert resp.status_code == 413
    assert "过大" in resp.json()["detail"]


def test_reject_bad_mime():
    """不支持的 MIME 类型应返回 400"""
    resp = client.post("/api/v1/analyze", files={"file": ("test.txt", b"hello", "text/plain")})
    assert resp.status_code == 400
    assert "不支持" in resp.json()["detail"]


def test_accept_octet_stream_with_png_ext():
    """application/octet-stream + .png 扩展名应被接受（不被类型校验拒绝）"""
    from unittest.mock import patch, AsyncMock

    mock_result = {
        "components": [], "topology": {}, "function": {},
        "key_nodes": [], "bom": [], "errors": []
    }
    with patch("main.NVIDIAAnalyzer.analyze", new_callable=AsyncMock, return_value=mock_result):
        resp = client.post("/api/v1/analyze", files={"file": ("circuit.png", TINY_PNG, "application/octet-stream")})
        # 只要不是 400 "不支持的文件类型" 就说明类型校验通过
        if resp.status_code == 400:
            assert "不支持" not in resp.json().get("detail", "")


def test_bom_rejects_empty():
    resp = client.post("/api/v1/bom", files={"file": ("e.png", b"", "image/png")})
    assert resp.status_code == 400


def test_detect_errors_rejects_oversized():
    big = b"\x00" * (10 * 1024 * 1024 + 1)
    resp = client.post("/api/v1/detect-errors", files={"file": ("big.jpg", big, "image/jpeg")})
    assert resp.status_code == 413
