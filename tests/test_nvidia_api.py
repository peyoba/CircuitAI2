#!/usr/bin/env python3
"""
CircuitAI NVIDIA API 单元测试（mock，不依赖真实 API）

原集成测试已移至 tests/integration/test_nvidia_live.py（需手动运行）
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key-123")
    monkeypatch.setenv("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1")


@pytest.mark.asyncio
async def test_nvidia_text_api(mock_env):
    """测试 NVIDIAAnalyzer 文本 API 调用（mock httpx）"""
    from services.nvidia_analyzer import NVIDIAAnalyzer

    analyzer = NVIDIAAnalyzer()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"components":[],"topology":null,"function":null,"key_nodes":[]}'}}]
    }

    with patch("httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.post.return_value = mock_response
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

        # analyze 只需要返回一个 dict
        result = await analyzer.analyze(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100, "image/png")
        assert isinstance(result, dict)
        instance.post.assert_called_once()


@pytest.mark.asyncio
async def test_nvidia_vision_api(mock_env):
    """测试 NVIDIAAnalyzer 完整分析（mock httpx）"""
    from services.nvidia_analyzer import NVIDIAAnalyzer

    analyzer = NVIDIAAnalyzer()

    full_result = {
        "components": [{"ref": "R1", "type": "电阻", "value": "10kΩ", "quantity": 1}],
        "topology": {"power_path": "VCC -> R1 -> GND"},
        "function": {"circuit_type": "分压器", "description": "简单分压电路"},
        "key_nodes": ["VCC", "GND"],
        "errors": [],
        "bom": [{"index": 1, "name": "电阻", "model": "10kΩ", "quantity": 1, "remarks": ""}],
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": json.dumps(full_result, ensure_ascii=False)}}]
    }

    with patch("httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.post.return_value = mock_response
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

        result = await analyzer.full_analysis(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100, "image/png")
        assert isinstance(result, dict)
        assert "components" in result or "function" in result


@pytest.mark.asyncio
async def test_nvidia_api_error_handling(mock_env):
    """测试 API 返回错误时的处理"""
    from services.nvidia_analyzer import NVIDIAAnalyzer

    analyzer = NVIDIAAnalyzer()

    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.text = "Rate limit exceeded"
    mock_response.json.side_effect = Exception("not json")

    with patch("httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.post.return_value = mock_response
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

        with pytest.raises(Exception):
            await analyzer.analyze(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100, "image/png")
