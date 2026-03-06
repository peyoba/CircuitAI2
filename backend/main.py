"""
CircuitAI 后端主入口
AI 电路图辅助工具 - FastAPI 后端服务

功能：
1. 电路图识别与解释
2. BOM 表自动生成
3. 电路错误检测

作者: 码农 (stone的编程助手)
创建时间: 2026-03-02
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Any

import uuid
import threading
import time

# 任务存储
tasks = {}

import os
from datetime import datetime

# 导入内部模块
from services.nvidia_analyzer import NVIDIAAnalyzer
from services.bom_generator import BOMGenerator
from services.error_detector import ErrorDetector

# 创建 FastAPI 应用
app = FastAPI(
    title="CircuitAI API",
    description="AI 电路图辅助工具 - 识别、解释、检测电路图",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置 CORS（跨域支持）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需要限制域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 数据模型 ====================

class AnalysisResult(BaseModel):
    """电路图分析结果模型"""
    components: Any = None  # 元件列表
    topology: Any = None  # 拓扑结构
    function: Any = None  # 电路功能
    key_nodes: Any = None  # 关键节点
    errors: Any = None  # 错误列表
    bom: Any = None  # BOM 表


class BOMItem(BaseModel):
    """BOM 表项模型"""
    index: int  # 编号
    name: str  # 名称
    model: str  # 型号
    parameters: str  # 参数
    quantity: int  # 数量
    remarks: str  # 备注


class ErrorItem(BaseModel):
    """错误项模型"""
    type: str  # 错误类型
    severity: str  # 严重程度 (critical/warning/info)
    description: str  # 错误描述
    suggestion: str  # 修复建议


# ==================== API 端点 ====================

@app.get("/")
async def root():
    """根路径 - API 状态检查"""
    return {
        "service": "CircuitAI API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/analyze", response_model=AnalysisResult)
async def analyze_circuit(file: UploadFile = File(...)):
    """
    电路图识别与解释
    
    功能：
    - 识别电路图中的所有元件
    - 分析电路拓扑结构
    - 解释电路功能
    
    参数：
    - file: 上传的电路图文件 (PNG/JPG/PDF)
    
    返回：
    - AnalysisResult: 分析结果对象
    """
    # 验证文件类型
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file.content_type}。支持: PNG, JPG, PDF"
        )
    
    # 读取文件内容
    file_content = await file.read()
    
    # 调用分析服务
    analyzer = NVIDIAAnalyzer()
    result = await analyzer.analyze(file_content, file.content_type)
    
    return result


@app.post("/api/v1/bom", response_model=List[BOMItem])
async def generate_bom(file: UploadFile = File(...)):
    """
    生成 BOM 表（物料清单）
    
    功能：
    - 从电路图中提取所有元件
    - 生成标准 BOM 表格式
    
    参数：
    - file: 上传的电路图文件 (PNG/JPG/PDF)
    
    返回：
    - List[BOMItem]: BOM 表列表
    """
    # 验证文件类型
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file.content_type}"
        )
    
    # 读取文件内容
    file_content = await file.read()
    
    # 调用 BOM 生成服务
    bom_gen = BOMGenerator()
    bom_list = await bom_gen.generate(file_content, file.content_type)
    
    return bom_list


@app.post("/api/v1/detect-errors", response_model=List[ErrorItem])
async def detect_errors(file: UploadFile = File(...)):
    """
    电路错误检测
    
    功能：
    - 检测电源是否接地
    - 检测芯片是否反向连接
    - 检测去耦电容是否缺失
    - 检测信号路径是否完整
    - 检测悬空引脚
    
    参数：
    - file: 上传的电路图文件 (PNG/JPG/PDF)
    
    返回：
    - List[ErrorItem]: 错误列表
    """
    # 验证文件类型
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file.content_type}"
        )
    
    # 读取文件内容
    file_content = await file.read()
    
    # 调用错误检测服务
    detector = ErrorDetector()
    errors = await detector.detect(file_content, file.content_type)
    
    return errors


@app.post("/api/v1/full-analysis", response_model=AnalysisResult)
async def full_analysis(file: UploadFile = File(...)):
    """
    完整分析（识别 + BOM + 错误检测）
    """
    import logging
    logger = logging.getLogger("circuitai")
    
    logger.info(f"收到文件: {file.filename}, 类型: {file.content_type}, 大小: {file.size}")
    
    # 验证文件类型（放宽限制）
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif", "application/pdf", "application/octet-stream"]
    content_type = file.content_type or "application/octet-stream"
    
    # 如果content_type不在列表中，尝试从文件名推断
    if content_type not in allowed_types:
        ext = (file.filename or "").lower().split(".")[-1] if file.filename else ""
        ext_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp", "pdf": "application/pdf"}
        content_type = ext_map.get(ext, content_type)
    
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file.content_type}。支持: PNG, JPG, WebP, PDF"
        )
    
    # 读取文件内容
    file_content = await file.read()
    logger.info(f"文件读取完成, 大小: {len(file_content)} bytes")
    
    try:
        # 调用完整分析服务
        analyzer = NVIDIAAnalyzer()
        result = await analyzer.full_analysis(file_content, content_type)
        logger.info(f"分析完成: {list(result.keys()) if isinstance(result, dict) else type(result)}")
        return result
    except Exception as e:
        logger.error(f"分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")




# ==================== 异步分析 API ====================

@app.post("/api/v1/analyze-async")
async def analyze_async(file: UploadFile = File(...)):
    """异步分析：立即返回任务ID，后台处理"""
    import logging
    logger = logging.getLogger("circuitai")
    
    content_type = file.content_type or "application/octet-stream"
    ext = (file.filename or "").lower().split(".")[-1] if file.filename else ""
    ext_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}
    if content_type == "application/octet-stream" and ext in ext_map:
        content_type = ext_map[ext]
    
    file_content = await file.read()
    task_id = str(uuid.uuid4())[:8]
    tasks[task_id] = {"status": "processing", "progress": "AI 正在分析电路图...", "result": None, "created": time.time()}
    
    def run_analysis():
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            analyzer = NVIDIAAnalyzer()
            result = loop.run_until_complete(analyzer.full_analysis(file_content, content_type))
            tasks[task_id] = {"status": "done", "result": result, "created": tasks[task_id]["created"]}
        except Exception as e:
            logger.error(f"分析失败: {e}")
            tasks[task_id] = {"status": "error", "error": str(e), "created": tasks[task_id]["created"]}
        finally:
            loop.close()
    
    thread = threading.Thread(target=run_analysis, daemon=True)
    thread.start()
    
    return {"task_id": task_id, "status": "processing"}


@app.get("/api/v1/task/{task_id}")
async def get_task(task_id: str):
    """查询任务状态"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks[task_id]
    
    # 清理超过10分钟的旧任务
    now = time.time()
    expired = [k for k, v in tasks.items() if now - v.get("created", 0) > 600]
    for k in expired:
        del tasks[k]
    
    return task


# ==================== 启动配置 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
