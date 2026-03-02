"""
CircuitAI 电路错误检测服务

检测电路图中的常见错误

作者: 码农 (stone的编程助手)
创建时间: 2026-03-02
"""

import base64
import httpx
import os
import json
import re
from typing import List, Dict, Any
from pathlib import Path


class ErrorDetector:
    """
    电路错误检测器
    
    功能：
    - 检测电源是否接地
    - 检测芯片是否反向连接
    - 检测去耦电容是否缺失
    - 检测信号路径是否完整
    - 检测悬空引脚
    """
    
    def __init__(self):
        """初始化错误检测器"""
        self.api_key = self._load_api_key()
        self.api_base = os.getenv("ANTHROPIC_API_BASE", "https://api.anthropic.com")
        self.model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
    
    def _load_api_key(self) -> str:
        """加载 Claude API Key"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            return api_key
        
        config_paths = [
            Path(__file__).parent.parent.parent / ".claude-api.env",
            Path.home() / ".openclaw" / "workspace" / "agents" / "main" / ".secrets" / "third-party-claude.env",
        ]
        
        for path in config_paths:
            if path.exists():
                with open(path, "r") as f:
                    for line in f:
                        if line.startswith("ANTHROPIC_API_KEY="):
                            return line.split("=", 1)[1].strip().strip('"')
        
        raise ValueError("未找到 Claude API Key")
    
    async def detect(self, file_content: bytes, content_type: str) -> List[Dict[str, Any]]:
        """
        检测电路错误
        
        参数：
        - file_content: 文件二进制内容
        - content_type: 文件类型
        
        返回：
        - 错误列表
        """
        # 将图片转换为 base64
        image_base64 = base64.b64encode(file_content).decode("utf-8")
        
        # 确定媒体类型
        media_type = content_type
        if content_type == "image/jpg":
            media_type = "image/jpeg"
        
        # 构建 Prompt
        prompt = self._build_error_detection_prompt()
        
        # 调用 Claude API
        response = await self._call_claude_api(prompt, image_base64, media_type)
        
        # 解析错误列表
        errors = self._parse_error_response(response)
        
        return errors
    
    def _build_error_detection_prompt(self) -> str:
        """构建错误检测 Prompt"""
        return """你是一个专业的硬件工程师，请仔细检查这张电路图，找出以下常见错误：

## 检查项目

1. **电源接地问题**
   - 电源和地是否直接短路？
   - 电源轨是否正确连接？

2. **芯片连接问题**
   - 芯片电源引脚是否正确连接？
   - 是否有芯片反向连接？
   - 使能引脚是否悬空？

3. **去耦电容问题**
   - 芯片电源引脚附近是否有去耦电容？
   - 去耦电容的容值是否合理？

4. **信号路径问题**
   - 信号路径是否完整？
   - 是否有信号线断开？

5. **悬空引脚问题**
   - 未使用的引脚是否悬空？
   - 输入引脚是否需要上拉/下拉？

## 输出格式

请以 JSON 数组格式输出，每个错误包含：
- type: 错误类型
- severity: 严重程度（critical/warning/info）
- description: 错误描述
- suggestion: 修复建议

示例：
```json
[
  {
    "type": "去耦电容缺失",
    "severity": "warning",
    "description": "U1 的 VCC 引脚附近没有去耦电容",
    "suggestion": "建议在 U1 的 VCC 引脚附近添加 100nF 去耦电容"
  },
  {
    "type": "悬空引脚",
    "severity": "info",
    "description": "U2 的 NC 引脚未连接",
    "suggestion": "NC 引脚可以悬空，但建议查阅数据手册确认"
  }
]
```

如果电路图没有明显错误，输出空数组：[]
只输出 JSON 数组，不要有其他文字。"""

    async def _call_claude_api(self, prompt: str, image_base64: str, media_type: str) -> str:
        """调用 Claude API"""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "max_tokens": 2048,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.api_base}/v1/messages",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"Claude API 调用失败: {response.status_code}")
            
            data = response.json()
            return data["content"][0]["text"]
    
    def _parse_error_response(self, response: str) -> List[Dict[str, Any]]:
        """解析错误响应"""
        # 尝试提取 JSON 数组
        json_match = re.search(r'\[\s*\{.*?\}\s*\]', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        # 尝试直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # 返回空列表（表示没有检测到错误）
        return []
