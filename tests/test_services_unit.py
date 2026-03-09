"""
CircuitAI 服务单元测试（pytest-asyncio 版本）
不依赖外部 API 调用，纯本地逻辑验证。
"""

import sys
import pytest

sys.path.insert(0, "/root/.openclaw/workspace/agents/coder/CircuitAI/backend")


# ==================== 模块导入测试 ====================

def test_import_nvidia_analyzer():
    from services.nvidia_analyzer import NVIDIAAnalyzer
    assert NVIDIAAnalyzer is not None


def test_import_bom_generator():
    from services.bom_generator import BOMGenerator
    assert BOMGenerator is not None


def test_import_error_detector():
    from services.error_detector import ErrorDetector
    assert ErrorDetector is not None


# ==================== 初始化测试 ====================

def test_nvidia_analyzer_init():
    from services.nvidia_analyzer import NVIDIAAnalyzer
    analyzer = NVIDIAAnalyzer()
    assert hasattr(analyzer, "model")
    assert hasattr(analyzer, "api_base")


def test_bom_generator_init():
    from services.bom_generator import BOMGenerator
    gen = BOMGenerator()
    assert hasattr(gen, "model")


def test_error_detector_init():
    from services.error_detector import ErrorDetector
    det = ErrorDetector()
    assert hasattr(det, "_analyzer")
    assert det.PROMPT is not None


# ==================== Prompt 构建测试 ====================

def test_analysis_prompt():
    from services.nvidia_analyzer import NVIDIAAnalyzer
    analyzer = NVIDIAAnalyzer()
    prompt = analyzer._build_analysis_prompt()
    assert "元件" in prompt or "component" in prompt.lower()


def test_bom_prompt():
    from services.bom_generator import BOMGenerator
    gen = BOMGenerator()
    prompt = gen._build_bom_prompt()
    assert "BOM" in prompt or "bom" in prompt.lower()


def test_error_detection_prompt():
    from services.error_detector import ErrorDetector
    det = ErrorDetector()
    assert "电路" in det.PROMPT or "circuit" in det.PROMPT.lower()


# ==================== 响应解析测试 ====================

def test_parse_analysis_json():
    from services.nvidia_analyzer import NVIDIAAnalyzer
    analyzer = NVIDIAAnalyzer()

    raw = '''```json
    {
        "components": [{"id": "R1", "type": "电阻", "value": "10K"}],
        "topology": "测试拓扑",
        "function": "测试功能",
        "key_nodes": [{"name": "VCC"}]
    }
    ```'''

    result = analyzer._parse_analysis_response(raw)
    assert "components" in result
    assert len(result["components"]) == 1
    assert result["components"][0]["id"] == "R1"


def test_parse_analysis_plain_json():
    from services.nvidia_analyzer import NVIDIAAnalyzer
    analyzer = NVIDIAAnalyzer()

    raw = '{"components": [], "topology": "none", "function": "none", "key_nodes": []}'
    result = analyzer._parse_analysis_response(raw)
    assert "components" in result


# ==================== FastAPI 端点测试 ====================

def test_health_endpoint():
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_root_endpoint():
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["service"] == "CircuitAI API"


def test_analyze_rejects_bad_type():
    from fastapi.testclient import TestClient
    from main import app, limiter
    limiter.reset()
    client = TestClient(app)
    resp = client.post("/api/v1/analyze", files={"file": ("test.txt", b"hello", "text/plain")})
    assert resp.status_code == 400
