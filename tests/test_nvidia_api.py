#!/usr/bin/env python3
"""
CircuitAI NVIDIA API 测试脚本
测试 GLM-4.7 电路图识别功能
"""

import httpx
import base64
import json
import os
import asyncio
from pathlib import Path

# 配置
API_KEY = os.getenv("NVIDIA_API_KEY", "")
API_BASE = os.getenv("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1")
MODEL = os.getenv("NVIDIA_MODEL", "nvidia/llama-3.1-nemotron-70b-instruct")


async def test_nvidia_text_api():
    """测试 NVIDIA API 纯文本连接"""
    print("=" * 60)
    print("测试 1: NVIDIA API 纯文本连接")
    print("=" * 60)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": "你好，请回复'NVIDIA API连接成功'"
            }
        ],
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    try:
        print(f"📡 调用 API: {API_BASE}/chat/completions")
        print(f"📦 模型: {MODEL}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_BASE}/chat/completions",
                headers=headers,
                json=payload
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                print(f"✅ API 连接成功")
                print(f"📝 响应: {content}")
                return True
            else:
                print(f"❌ API 调用失败")
                print(f"响应: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


async def test_nvidia_vision_api():
    """测试 NVIDIA API 图像识别功能"""
    print("\n" + "=" * 60)
    print("测试 2: NVIDIA API 图像识别")
    print("=" * 60)
    
    # 查找测试图片
    test_images = [
        "/tmp/test_circuit.png",
        "/tmp/test_circuit.jpg",
        "/root/.openclaw/workspace/agents/coder/CircuitAI/tests/test_circuit.png"
    ]
    
    image_path = None
    for path in test_images:
        if os.path.exists(path):
            image_path = path
            break
    
    if not image_path:
        print("⚠️  没有找到测试图片")
        print("提示: 请准备一张测试电路图放在 /tmp/test_circuit.png")
        return False
    
    print(f"📸 使用测试图片: {image_path}")
    
    # 读取并编码图片
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    image_base64 = base64.b64encode(image_data).decode("utf-8")
    
    # 确定图片类型
    if image_path.endswith(".png"):
        media_type = "image/png"
    elif image_path.endswith(".jpg") or image_path.endswith(".jpeg"):
        media_type = "image/jpeg"
    else:
        media_type = "image/png"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = """请识别这张电路图，告诉我：
1. 这是什么类型的电路？
2. 有哪些主要元件？
3. 电路的功能是什么？

请用简洁的语言回答。"""

    payload = {
        "model": MODEL,
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
        "max_tokens": 500,
        "temperature": 0.7
    }
    
    try:
        print("📡 正在调用 NVIDIA Vision API...")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{API_BASE}/chat/completions",
                headers=headers,
                json=payload
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                print(f"✅ 图像识别成功")
                print(f"\n识别结果:")
                print("-" * 60)
                print(content)
                print("-" * 60)
                return True
            else:
                print(f"❌ API 调用失败")
                print(f"响应: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


async def main():
    """主测试流程"""
    print("🚀 CircuitAI NVIDIA API 测试")
    print(f"API Base: {API_BASE}")
    print(f"Model: {MODEL}")
    print()
    
    # 测试 1: 纯文本连接
    test1_passed = await test_nvidia_text_api()
    
    # 测试 2: 图像识别
    test2_passed = await test_nvidia_vision_api()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print(f"纯文本连接: {'✅ 通过' if test1_passed else '❌ 失败'}")
    print(f"图像识别: {'✅ 通过' if test2_passed else '⚠️  未测试'}")
    print("=" * 60)
    
    if test1_passed:
        print("\n✅ NVIDIA API 配置正确，可以开始开发！")
    else:
        print("\n❌ NVIDIA API 配置有问题，请检查！")


if __name__ == "__main__":
    asyncio.run(main())
