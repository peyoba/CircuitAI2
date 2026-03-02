"""
CircuitAI BOM 表生成服务

从电路图中提取元件信息，生成标准 BOM 表

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


class BOMGenerator:
    """
    BOM 表生成器
    
    功能：
    - 从电路图中提取元件信息
    - 生成标准 BOM 表格式
    - 支持导出 Excel/CSV
    """
    
    def __init__(self):
        """初始化 BOM 生成器"""
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
    
    async def generate(self, file_content: bytes, content_type: str) -> List[Dict[str, Any]]:
        """
        生成 BOM 表
        
        参数：
        - file_content: 文件二进制内容
        - content_type: 文件类型
        
        返回：
        - BOM 表列表
        """
        # 将图片转换为 base64
        image_base64 = base64.b64encode(file_content).decode("utf-8")
        
        # 确定媒体类型
        media_type = content_type
        if content_type == "image/jpg":
            media_type = "image/jpeg"
        
        # 构建 Prompt
        prompt = self._build_bom_prompt()
        
        # 调用 Claude API
        response = await self._call_claude_api(prompt, image_base64, media_type)
        
        # 解析 BOM 表
        bom_list = self._parse_bom_response(response)
        
        return bom_list
    
    def _build_bom_prompt(self) -> str:
        """构建 BOM 生成 Prompt"""
        return """你是一个专业的硬件工程师，请分析这张电路图并生成 BOM 表（物料清单）。

要求：
1. 识别所有元件（电阻、电容、电感、二极管、三极管、芯片、连接器等）
2. 标注元件参数和封装
3. 统计每种元件的数量
4. 提供采购备注（如精度要求、耐压值等）

请以 JSON 数组格式输出，每个元素包含以下字段：
- index: 序号（整数）
- name: 元件名称（如"电阻"、"电容"）
- model: 型号/参数（如"10K 0603"、"100nF 0402"）
- quantity: 数量
- remarks: 备注（如封装、精度、耐压等）

示例输出格式：
```json
[
  {"index": 1, "name": "电阻", "model": "10K 0603 1%", "quantity": 5, "remarks": "上拉电阻"},
  {"index": 2, "name": "电容", "model": "100nF 0402 16V", "quantity": 3, "remarks": "去耦电容"},
  {"index": 3, "name": "芯片", "model": "AMS1117-3.3", "quantity": 1, "remarks": "LDO稳压器 SOT-223"}
]
```

只输出 JSON 数组，不要有其他文字说明。"""

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
    
    def _parse_bom_response(self, response: str) -> List[Dict[str, Any]]:
        """解析 BOM 响应"""
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
        
        # 返回空列表
        return []
