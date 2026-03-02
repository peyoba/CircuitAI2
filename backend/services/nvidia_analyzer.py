"""
CircuitAI NVIDIA GLM 分析服务
使用 NVIDIA GLM-4.7 进行电路图识别和分析
作者: 码农 (stone的编程助手)
创建时间: 2026-03-02
"""

import base64
import httpx
import os
import json
import re
from typing import Dict, Any, List
from pathlib import Path


class NVIDIAAnalyzer:
    """
    NVIDIA GLM 电路图分析器
    
    功能：
    - 调用 NVIDIA GLM-4.7 API 进行电路图识别
    - 提取元件信息
    - 分析拓扑结构
    - 生成电路功能解释
    """
    
    def __init__(self):
        """初始化分析器，加载配置"""
        self.api_key = self._load_api_key()
        self.api_base = os.getenv("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1")
        self.model = os.getenv("NVIDIA_MODEL", "z-ai/glm4.7")
        # 注：GLM-4.7 可能需要确认正确的模型名称
    
    def _load_api_key(self) -> str:
        """从环境变量加载 API Key"""
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            raise ValueError("未找到 NVIDIA API Key，请配置 NVIDIA_API_KEY 环境变量")
        return api_key
    
    async def analyze(self, file_content: bytes, content_type: str) -> Dict[str, Any]:
        """
        分析电路图
        
        参数：
        - file_content: 文件二进制内容
        - content_type: 文件类型 (image/png, image/jpeg, application/pdf)
        
        返回：
        - 分析结果字典
        """
        # 将图片转换为 base64
        image_base64 = base64.b64encode(file_content).decode("utf-8")
        
        # 确定媒体类型
        media_type = content_type
        if content_type == "image/jpg":
            media_type = "image/jpeg"
        
        # 构建 Prompt
        prompt = self._build_analysis_prompt()
        
        # 调用 NVIDIA API
        response = await self._call_nvidia_api(prompt, image_base64, media_type)
        
        # 解析响应
        result = self._parse_analysis_response(response)
        
        return result
    
    async def full_analysis(self, file_content: bytes, content_type: str) -> Dict[str, Any]:
        """
        完整分析（识别 + BOM + 错误检测）
        
        参数：
        - file_content: 文件二进制内容
        - content_type: 文件类型
        
        返回：
        - 完整分析结果
        """
        image_base64 = base64.b64encode(file_content).decode("utf-8")
        
        media_type = content_type
        if content_type == "image/jpg":
            media_type = "image/jpeg"
        
        prompt = self._build_full_analysis_prompt()
        
        response = await self._call_nvidia_api(prompt, image_base64, media_type)
        
        result = self._parse_full_response(response)
        
        return result
    
    def _build_analysis_prompt(self) -> str:
        """构建电路图分析 Prompt"""
        return """你是一个专业的硬件工程师，擅长分析电路原理图。

请仔细分析这张电路图，提取以下信息：

## 1. 元件列表
识别所有元件，包括：
- 电阻（R1, R2, ...）
- 电容（C1, C2, ...）
- 电感（L1, L2, ...）
- 二极管（D1, D2, ...）
- 三极管（Q1, Q2, ...）
- 芯片（U1, U2, ...）
- 电源、接地符号

每个元件请标注：
- 编号（如 R1）
- 型号或参数（如 10K, 100nF）
- 引脚连接

## 2. 拓扑结构
描述电路的拓扑结构：
- 电源路径（从电源到各模块）
- 信号路径（主要信号流向）
- 接地方式（单点接地/多点接地）
- 模块划分（电源模块、信号处理模块等）

## 3. 电路功能
用简洁的语言描述这个电路的功能：
- 这是什么类型的电路？（电源、放大器、滤波器、控制电路等）
- 主要作用是什么？
- 典型应用场景？

## 4. 关键节点
标注电路中的关键节点：
- 电源输入点
- 信号输入/输出点
- 关键测试点
- 反馈节点

请以 JSON 格式输出结果，格式如下：
```json
{
    "components": [
        {"id": "R1", "type": "电阻", "value": "10K", "pins": ["VCC", "GPIO1"]}
    ],
    "topology": "电源从左侧输入，经过滤波后供给主芯片...",
    "function": "这是一个5V转3.3V的降压电路...",
    "key_nodes": [
        {"name": "电源输入", "description": "5V输入端"}
    ]
}
```"""
    
    def _build_full_analysis_prompt(self) -> str:
        """构建完整分析 Prompt（包含 BOM 和错误检测）"""
        return """你是一个专业的硬件工程师，擅长分析电路原理图。

请仔细分析这张电路图，提供完整的分析报告：

## 1. 元件列表
识别所有元件，包括编号、型号、参数、数量。

## 2. 拓扑结构
描述电路的拓扑结构和信号流向。

## 3. 电路功能
描述电路的功能和应用场景。

## 4. 关键节点
标注电路中的关键节点。

## 5. BOM 表
生成物料清单，包含：
- 编号（序号）
- 名称
- 型号/参数
- 数量
- 备注（如封装类型）

## 6. 错误检测
检查以下常见错误：
- 电源是否接地？
- 芯片是否反向连接？
- 去耦电容是否缺失？
- 信号路径是否完整？
- 是否有悬空引脚？

对每个错误，标注严重程度和修复建议。

请以 JSON 格式输出结果，格式如下：
```json
{
    "components": [...],
    "topology": "...",
    "function": "...",
    "key_nodes": [...],
    "bom": [
        {"index": 1, "name": "电阻", "model": "10K 0603", "quantity": 2, "remarks": "上拉电阻"}
    ],
    "errors": [
        {
            "type": "去耦电容缺失",
            "severity": "warning",
            "description": "U1电源引脚附近缺少去耦电容",
            "suggestion": "在U1的VCC引脚附近添加100nF去耦电容"
        }
    ]
}
```"""
    
    async def _call_nvidia_api(self, prompt: str, image_base64: str, media_type: str) -> str:
        """
        调用 NVIDIA API
        
        参数：
        - prompt: 提示词
        - image_base64: 图片的 base64 编码
        - media_type: 图片媒体类型
        
        返回：
        - NVIDIA API 的响应文本
        """
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
            "max_tokens": 4096,
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
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """
        解析分析响应
        
        参数：
        - response: API 的响应文本
        
        返回：
        - 解析后的字典
        """
        # 尝试从响应中提取 JSON
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(1)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # 如果没有 JSON 块，尝试直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # 如果都失败，返回原始文本
        return {
            "components": [],
            "topology": response,
            "function": "无法解析，请查看拓扑结构说明",
            "key_nodes": []
        }
    
    def _parse_full_response(self, response: str) -> Dict[str, Any]:
        """
        解析完整分析响应
        
        参数：
        - response: API 的响应文本
        
        返回：
        - 解析后的字典
        """
        result = self._parse_analysis_response(response)
        
        # 确保所有字段都存在
        if "bom" not in result:
            result["bom"] = []
        
        if "errors" not in result:
            result["errors"] = []
        
        return result
