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
        """构建电路图分析 Prompt（优化版）"""
        return """你是一个专业的硬件工程师，擅长分析电路原理图。请仔细分析这张电路图。

**输出要求**：
1. 必须输出有效的 JSON 格式
2. 使用英文键名（components, topology, function, key_nodes）
3. 确保所有字段都有值

**分析内容**：

## 1. 元件列表 (components)
识别所有元件，每个元件包含：
- ref: 编号（如 R1, C1, U1）
- type: 类型（Resistor, Capacitor, Inductor, Diode, Transistor, IC, LED）
- value: 参数值（如 10K, 100nF, LM7805）
- pins: 引脚连接描述

## 2. 拓扑结构 (topology)
简明描述：
- 电源路径：从输入到各模块的供电路线
- 信号路径：主要信号流向
- 接地方式
- 模块划分

## 3. 电路功能 (function)
- circuit_type: 电路类型（如 Power Supply, Amplifier, Filter）
- description: 功能描述（50字以内）
- applications: 典型应用

## 4. 关键节点 (key_nodes)
列出重要测试点：
- name: 节点名称
- description: 功能描述

请严格按照以下 JSON 格式输出：
```json
{
  "components": [{"ref": "R1", "type": "Resistor", "value": "10K", "pins": "VCC to GPIO1"}],
  "topology": "电源路径描述...",
  "function": {"circuit_type": "Power Supply", "description": "...", "applications": "..."},
  "key_nodes": [{"name": "VIN", "description": "电源输入"}]
}
```"""

    def _build_full_analysis_prompt(self) -> str:
        """构建完整分析 Prompt（中英双语版）"""
        return """你是一个专业的硬件工程师，擅长分析电路原理图。请仔细分析这张电路图。

**重要要求**：
1. 必须输出有效的 JSON 格式
2. 所有描述性文字使用**中英双语**格式："中文 / English"
3. 确保所有字段都有值

**分析内容**：

## 1. 元件列表 (components)
每个元件包含：
- ref: 编号（如 R1, C1, U1）
- type: 类型，中英双语（如 "电阻 / Resistor"）
- value: 参数值（如 10K, 100nF）
- quantity: 数量
- pins: 引脚连接描述，中英双语

## 2. 拓扑结构 (topology)
用对象描述，每个值中英双语：
- power_path: 电源路径
- signal_path: 信号路径
- grounding: 接地方式
- modules: 模块划分

## 3. 电路功能 (function)
- circuit_type: 电路类型，中英双语（如 "稳压电源 / Voltage Regulator"）
- description: 功能描述，中英双语
- applications: 典型应用，中英双语

## 4. 关键节点 (key_nodes)
列表，每个节点为对象：
- name: 节点名称
- description: 功能描述，中英双语

## 5. BOM 表 (bom)
物料清单：
- index: 序号
- name: 元件名称，中英双语（如 "电阻 / Resistor"）
- model: 型号/参数
- quantity: 数量
- remarks: 备注，中英双语

## 6. 错误检测 (errors)
检查常见错误：电源接地、芯片反接、去耦电容缺失、悬空引脚
每个错误包含：
- type: 错误类型
- severity: 严重程度（High/Medium/Low）
- description: 描述，中英双语
- suggestion: 建议，中英双语

**输出示例**：
```json
{
  "components": [{"ref": "R1", "type": "电阻 / Resistor", "value": "10K", "quantity": 1, "pins": "连接VCC到GPIO1 / Connects VCC to GPIO1"}],
  "topology": {"power_path": "直流输入经滤波后到稳压器 / DC input through filter to regulator", "signal_path": "无信号路径 / No signal path", "grounding": "共地配置 / Common ground", "modules": "输入滤波、稳压、输出滤波 / Input filter, regulation, output filter"},
  "function": {"circuit_type": "线性稳压电源 / Linear Voltage Regulator", "description": "将输入电压转换为稳定的输出电压 / Converts input voltage to stable output", "applications": "为微控制器供电 / Powering microcontrollers"},
  "key_nodes": [{"name": "VIN", "description": "电源输入 / Power input"}],
  "bom": [{"index": 1, "name": "电阻 / Resistor", "model": "10K 0603", "quantity": 1, "remarks": "上拉电阻 / Pull-up resistor"}],
  "errors": [{"type": "bypass_capacitor_missing", "severity": "Medium", "description": "芯片旁缺少去耦电容 / Missing bypass capacitor near IC", "suggestion": "在电源引脚旁放置0.1μF电容 / Place 0.1μF cap near power pins"}]
}
```

请严格按照 JSON 格式输出，不要输出其他内容。"""

    async def _call_nvidia_api(self, prompt: str, image_base64: str, media_type: str) -> str:
        """调用 API（自动检测 OpenAI 或 Anthropic 格式）"""
        
        # 检测是否使用 Anthropic Messages 格式
        use_anthropic = os.getenv("API_FORMAT", "").lower() == "anthropic" or "anyrouter" in self.api_base
        
        if use_anthropic:
            return await self._call_anthropic_api(prompt, image_base64, media_type)
        else:
            return await self._call_openai_api(prompt, image_base64, media_type)
    
    async def _call_anthropic_api(self, prompt: str, image_base64: str, media_type: str) -> str:
        """调用 Anthropic Messages API"""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "max_tokens": 4096,
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
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
        }
        
        max_retries = 3
        async with httpx.AsyncClient(timeout=180.0) as client:
            for attempt in range(max_retries):
                try:
                    response = await client.post(
                        f"{self.api_base}/v1/messages",
                        headers=headers,
                        json=payload
                    )
                    if response.status_code == 200:
                        data = response.json()
                        # Anthropic 格式: data.content[0].text
                        content = data.get("content", [])
                        for block in content:
                            if block.get("type") == "text":
                                return block.get("text", "")
                        return str(content)
                    elif response.status_code >= 500 and attempt < max_retries - 1:
                        await asyncio.sleep(5)
                        continue
                    else:
                        raise Exception(f"Anthropic API 调用失败: {response.status_code} - {response.text[:200]}")
                except httpx.ReadTimeout:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(10)
                        continue
                    raise Exception(f"Anthropic API 超时，已重试 {max_retries} 次")
    
    async def _call_openai_api(self, prompt: str, image_base64: str, media_type: str) -> str:
        """调用 OpenAI 兼容 API"""
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
                        msg = data["choices"][0]["message"]
                        # 有些模型把内容放在 reasoning_content 里
                        content = msg.get("content") or msg.get("reasoning_content") or ""
                        return content
                    elif response.status_code >= 500 and attempt < max_retries - 1:
                        await asyncio.sleep(5)
                        continue
                    else:
                        raise Exception(f"API 调用失败: {response.status_code} - {response.text[:200]}")
                except httpx.ReadTimeout:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(10)
                        continue
                    raise Exception(f"API 超时，已重试 {max_retries} 次")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(5)
                        continue
                    raise Exception(f"NVIDIA API 调用失败: {str(e)}")
        
        raise Exception("NVIDIA API 调用失败")
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """解析分析响应"""
        if response is None:
            return {
                "components": [],
                "topology": "API 返回为空",
                "function": "无法解析",
                "key_nodes": []
            }
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
        if response is None:
            return {
                "components": [],
                "topology": "API 返回为空",
                "function": "",
                "key_nodes": [],
                "bom": [],
                "errors": []
            }
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
