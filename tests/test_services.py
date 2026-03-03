#!/usr/bin/env python3
"""
CircuitAI 完整服务测试
测试所有核心服务的功能
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, "/root/.openclaw/workspace/agents/coder/CircuitAI/backend")


async def test_imports():
    """测试所有模块导入"""
    print("=" * 60)
    print("测试 1: 模块导入测试")
    print("=" * 60)
    
    try:
        from services.circuit_analyzer import CircuitAnalyzer
        print("✅ CircuitAnalyzer 导入成功")
    except Exception as e:
        print(f"❌ CircuitAnalyzer 导入失败: {e}")
        return False
    
    try:
        from services.nvidia_analyzer import NVIDIAAnalyzer
        print("✅ NVIDIAAnalyzer 导入成功")
    except Exception as e:
        print(f"❌ NVIDIAAnalyzer 导入失败: {e}")
        return False
    
    try:
        from services.bom_generator import BOMGenerator
        print("✅ BOMGenerator 导入成功")
    except Exception as e:
        print(f"❌ BOMGenerator 导入失败: {e}")
        return False
    
    try:
        from services.error_detector import ErrorDetector
        print("✅ ErrorDetector 导入成功")
    except Exception as e:
        print(f"❌ ErrorDetector 导入失败: {e}")
        return False
    
    print("\n✅ 所有模块导入成功")
    return True


async def test_initialization():
    """测试服务初始化"""
    print("\n" + "=" * 60)
    print("测试 2: 服务初始化测试")
    print("=" * 60)
    
    try:
        from services.nvidia_analyzer import NVIDIAAnalyzer
        analyzer = NVIDIAAnalyzer()
        print(f"✅ NVIDIAAnalyzer 初始化成功")
        print(f"   模型: {analyzer.model}")
        print(f"   API Base: {analyzer.api_base}")
    except Exception as e:
        print(f"❌ NVIDIAAnalyzer 初始化失败: {e}")
        return False
    
    try:
        from services.bom_generator import BOMGenerator
        bom_gen = BOMGenerator()
        print(f"✅ BOMGenerator 初始化成功")
        print(f"   模型: {bom_gen.model}")
    except Exception as e:
        print(f"❌ BOMGenerator 初始化失败: {e}")
        return False
    
    try:
        from services.error_detector import ErrorDetector
        detector = ErrorDetector()
        print(f"✅ ErrorDetector 初始化成功")
        print(f"   模型: {detector.model}")
    except Exception as e:
        print(f"❌ ErrorDetector 初始化失败: {e}")
        return False
    
    print("\n✅ 所有服务初始化成功")
    return True


async def test_api_connection():
    """测试 NVIDIA API 连接"""
    print("\n" + "=" * 60)
    print("测试 3: NVIDIA API 连接测试")
    print("=" * 60)
    
    try:
        from services.nvidia_analyzer import NVIDIAAnalyzer
        import httpx
        
        analyzer = NVIDIAAnalyzer()
        
        # 简单的文本测试
        headers = {
            "Authorization": f"Bearer {analyzer.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": analyzer.model,
            "messages": [
                {"role": "user", "content": "你好"}
            ],
            "max_tokens": 20
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{analyzer.api_base}/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                print(f"✅ NVIDIA API 连接成功")
                print(f"   状态码: {response.status_code}")
                try:
                    data = response.json()
                    if data and "choices" in data and len(data["choices"]) > 0:
                        content = data["choices"][0]["message"].get("content", "")
                        if content:
                            print(f"   响应: {content[:50]}...")
                        else:
                            print(f"   响应: API返回空内容（可能是新模型）")
                    else:
                        print(f"   响应: API响应格式正常")
                except:
                    pass
                return True
            else:
                print(f"❌ NVIDIA API 连接失败")
                print(f"   状态码: {response.status_code}")
                print(f"   响应: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ API 测试错误: {e}")
        return False


async def test_prompt_builders():
    """测试 Prompt 构建函数"""
    print("\n" + "=" * 60)
    print("测试 4: Prompt 构建测试")
    print("=" * 60)
    
    try:
        from services.nvidia_analyzer import NVIDIAAnalyzer
        from services.bom_generator import BOMGenerator
        from services.error_detector import ErrorDetector
        
        # 测试 NVIDIAAnalyzer
        analyzer = NVIDIAAnalyzer()
        prompt1 = analyzer._build_analysis_prompt()
        if "元件列表" in prompt1 and "拓扑结构" in prompt1:
            print("✅ CircuitAnalyzer Prompt 构建成功")
        else:
            print("❌ CircuitAnalyzer Prompt 内容不完整")
            return False
        
        # 测试 BOMGenerator
        bom_gen = BOMGenerator()
        prompt2 = bom_gen._build_bom_prompt()
        if "BOM" in prompt2 and "index" in prompt2:
            print("✅ BOMGenerator Prompt 构建成功")
        else:
            print("❌ BOMGenerator Prompt 内容不完整")
            return False
        
        # 测试 ErrorDetector
        detector = ErrorDetector()
        prompt3 = detector._build_error_detection_prompt()
        if "电路" in prompt3 and ("错误" in prompt3 or "检测" in prompt3):
            print("✅ ErrorDetector Prompt 构建成功")
        else:
            print("❌ ErrorDetector Prompt 内容不完整")
            return False
        
        print("\n✅ 所有 Prompt 构建成功")
        return True
        
    except Exception as e:
        print(f"❌ Prompt 测试错误: {e}")
        return False


async def test_response_parsers():
    """测试响应解析函数"""
    print("\n" + "=" * 60)
    print("测试 5: 响应解析测试")
    print("=" * 60)
    
    try:
        from services.nvidia_analyzer import NVIDIAAnalyzer
        
        analyzer = NVIDIAAnalyzer()
        
        # 测试 JSON 解析
        test_response = '''
        ```json
        {
            "components": [{"id": "R1", "type": "电阻", "value": "10K"}],
            "topology": "测试拓扑",
            "function": "测试功能",
            "key_nodes": [{"name": "测试节点"}]
        }
        ```
        '''
        
        result = analyzer._parse_analysis_response(test_response)
        
        if "components" in result and "topology" in result:
            print("✅ JSON 响应解析成功")
            print(f"   元件数: {len(result['components'])}")
        else:
            print("❌ JSON 响应解析失败")
            return False
        
        print("\n✅ 响应解析功能正常")
        return True
        
    except Exception as e:
        print(f"❌ 解析测试错误: {e}")
        return False


async def main():
    """主测试流程"""
    print("🚀 CircuitAI 完整服务测试")
    print("=" * 60)
    
    # 测试 1: 模块导入
    test1 = await test_imports()
    
    # 测试 2: 服务初始化
    test2 = await test_initialization()
    
    # 测试 3: API 连接
    test3 = await test_api_connection()
    
    # 测试 4: Prompt 构建
    test4 = await test_prompt_builders()
    
    # 测试 5: 响应解析
    test5 = await test_response_parsers()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print(f"模块导入: {'✅ 通过' if test1 else '❌ 失败'}")
    print(f"服务初始化: {'✅ 通过' if test2 else '❌ 失败'}")
    print(f"API 连接: {'✅ 通过' if test3 else '❌ 失败'}")
    print(f"Prompt 构建: {'✅ 通过' if test4 else '❌ 失败'}")
    print(f"响应解析: {'✅ 通过' if test5 else '❌ 失败'}")
    print("=" * 60)
    
    if all([test1, test2, test3, test4, test5]):
        print("\n✅ 所有测试通过！可以继续开发。")
        return 0
    else:
        print("\n❌ 部分测试失败，需要修复。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
