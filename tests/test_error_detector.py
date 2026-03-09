"""ErrorDetector 单元测试（纯解析逻辑，不调用外部 API）"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault("NVIDIA_API_KEY", "test-key")

import pytest
from services.error_detector import ErrorDetector


class TestErrorDetectorParse:
    """测试 ErrorDetector._parse 静态方法"""

    def test_parse_json_array(self):
        raw = '[{"type":"短路","severity":"critical","description":"VCC-GND短路","suggestion":"检查"}]'
        result = ErrorDetector._parse(raw)
        assert len(result) == 1
        assert result[0]["type"] == "短路"

    def test_parse_json_in_code_block(self):
        raw = '一些说明文字\n```json\n[{"type":"悬空","severity":"info","description":"U1 pin5","suggestion":"加下拉"}]\n```\n后续文字'
        result = ErrorDetector._parse(raw)
        assert len(result) == 1
        assert result[0]["severity"] == "info"

    def test_parse_empty_array(self):
        assert ErrorDetector._parse("[]") == []

    def test_parse_garbage(self):
        assert ErrorDetector._parse("这不是JSON") == []

    def test_parse_none(self):
        assert ErrorDetector._parse("") == []

    def test_parse_mixed_text_with_json(self):
        raw = '分析结果如下：\n[{"type":"去耦电容缺失","severity":"warning","description":"缺少去耦","suggestion":"添加100nF"}]\n以上。'
        result = ErrorDetector._parse(raw)
        assert len(result) == 1
        assert "去耦" in result[0]["type"]
