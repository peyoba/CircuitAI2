"""CircuitAI NVIDIA GLM 分析服务

使用 NVIDIA GLM-4.7 进行电路图识别和分析

作者: 码农 (stone的编程助手)
创建时间: 2026-03-02
"""

import base64
import httpx
import os
import json
import re
import asyncio
from typing import Dict, Any, List
from pathlib import Path


class NVIDIAAnalyzer:
    """NVIDIA GLM 电路图分析器
    
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
    
    def _load_api_key(self) -> str:
        """从环境变量加载 API Key"""
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            raise ValueError("未找到 NVIDIA API Key，请配置 NVIDIA_API_KEY 环境变量")
        return api_key
    
    async def analyze(self, file_content: bytes, content_type: str) -> Dict[str, Any]:
        """分析电路图
        
        参数：
        - file_content: 文件二进制内容
        - content_type: 文件类型 (image/png, image/jpeg, application/pdf)
        
        返回：
        - 分析结果字典
        """
        image_base64 = base64.b64encode(file_content).decode("utf-8")
        media_type = content_type
        if content_type == "image/jpg":
            media_type = "image/jpeg"
        
        prompt = self._build_analysis_prompt()
        response = await self._call_nvidia_api(prompt, image_base64, media_type)
        result = self._parse_analysis_response(response)
        return result
    
    async def full_analysis(self, file_content: bytes, content_type: str) -> Dict[str, Any]:
        """完整分析（识别 + BOM + 错误检测）"""
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

请以 JSON 格式输出结果。"""

    def _build_full_analysis_prompt(self) -> str:
        """构建完整分析 Prompt"""
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
生成物料清单。

## 6. 错误检测
检查常见错误：电源接地、芯片反接、去耦电容缺失等。

请以 JSON 格式输出结果。"""

    async def _call_nvidia_api(self, prompt: str, image_base64: str, media_type: str) -> str:
        """调用 NVIDIA API（带重试机制）"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
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
        
        max_retries = 3
        async with httpx.AsyncClient(timeout=180.0) as client:
            for attempt in range(max_retries):
                try:
                    response = await client.post(
                        f"{self.api_base}/chat/completions",
                        headers=headers,
                        json=payload
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return data["choices"][0]["message"]["content"]
                    elif response.status_code >= 500 and attempt < max_retries - 1:
                        await asyncio.sleep(5)
                        continue
                    else:
                        raise Exception(f"NVIDIA API 调用失败: {response.status_code}")
                except httpx.ReadTimeout:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(10)
                        continue
                    raise Exception(f"NVIDIA API 超时，已重试 {max_retries} 次")
                except Exception as e:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(5)
                        continue
                    raise Exception(f"NVIDIA API 调用失败: {str(e)}")
        
        raise Exception("NVIDIA API 调用失败")
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """解析分析响应"""
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        return {
            "components": [],
            "topology": response,
            "function": "无法解析，请查看拓扑结构说明",
            "key_nodes": []
        }
    
    def _parse_full_response(self, response: str) -> Dict[str, Any]:
        """解析完整分析响应"""
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        return {
            "components": [],
            "topology": response,
            "function": "",
            "key_nodes": [],
            "bom": [],
            "errors": []
        }
