"""
CircuitAI 电路错误检测服务

复用 NVIDIAAnalyzer 的 API 调用逻辑，支持 OpenAI / Anthropic 双格式

作者: 码农 (stone的编程助手)
创建时间: 2026-03-02
更新时间: 2026-03-09 — 重构为复用 NVIDIAAnalyzer._call_nvidia_api
"""

import json
import re
from typing import List, Dict, Any

from services.nvidia_analyzer import NVIDIAAnalyzer


class ErrorDetector:
    """
    电路错误检测器
    
    委托 NVIDIAAnalyzer 完成 API 调用，自身只负责 prompt 构造与结果解析。
    """

    PROMPT = """你是一个专业的硬件工程师，请仔细检查这张电路图，找出以下常见错误：

## 检查项目

1. **电源接地问题** — 电源和地是否短路？电源轨是否正确连接？
2. **芯片连接问题** — 电源引脚是否正确？是否反向连接？使能引脚是否悬空？
3. **去耦电容问题** — 芯片电源引脚附近是否有去耦电容？容值是否合理？
4. **信号路径问题** — 信号路径是否完整？是否有断线？
5. **悬空引脚问题** — 未使用的引脚是否悬空？输入是否需要上拉/下拉？

## 输出格式

只输出 JSON 数组，不要有其他文字。每个错误：
```json
[
  {
    "type": "去耦电容缺失",
    "severity": "warning",
    "description": "U1 的 VCC 引脚附近没有去耦电容",
    "suggestion": "建议在 U1 的 VCC 引脚附近添加 100nF 去耦电容"
  }
]
```
severity 取值：critical / warning / info
如果没有明显错误，输出空数组 []。"""

    def __init__(self):
        self._analyzer = NVIDIAAnalyzer()

    async def detect(self, file_content: bytes, content_type: str) -> List[Dict[str, Any]]:
        """检测电路错误"""
        import base64

        image_base64 = base64.b64encode(file_content).decode("utf-8")
        media_type = "image/jpeg" if content_type == "image/jpg" else content_type

        response = await self._analyzer._call_nvidia_api(self.PROMPT, image_base64, media_type)
        return self._parse(response)

    @staticmethod
    def _parse(response: str) -> List[Dict[str, Any]]:
        """解析错误响应"""
        if not response:
            return []

        # 尝试 ```json ... ```
        m = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试裸 JSON 数组
        m = re.search(r'\[\s*\{.*?\}\s*\]', response, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass

        # 直接解析
        try:
            result = json.loads(response)
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

        return []
