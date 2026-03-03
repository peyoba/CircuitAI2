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
    - 使用 NVIDIA GLM-4.7 API
    """
    
    def __init__(self):
        """初始化 BOM 生成器"""
        self.api_key = self._load_api_key()
        self.api_base = os.getenv("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1")
        self.model = os.getenv("NVIDIA_MODEL", "z-ai/glm4.7")
    
    def _load_api_key(self) -> str:
        """加载 NVIDIA API Key"""
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            raise ValueError("未找到 NVIDIA API Key，请配置 NVIDIA_API_KEY 环境变量")
        return api_key
    
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
        
        # 调用 NVIDIA API
        response = await self._call_nvidia_api(prompt, image_base64, media_type)
        
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

    async def _call_nvidia_api(self, prompt: str, image_base64: str, media_type: str) -> str:
        """调用 NVIDIA API（OpenAI 兼容格式）"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # NVIDIA API 使用 OpenAI 兼容格式
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 2048,
            "temperature": 0.7
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"NVIDIA API 调用失败: {response.status_code} - {response.text}")
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
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
