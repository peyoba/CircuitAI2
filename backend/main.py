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
    
    功能：
    - 电路图识别与解释
    - BOM 表生成
    - 错误检测
    
    参数：
    - file: 上传的电路图文件 (PNG/JPG/PDF)
    
    返回：
    - AnalysisResult: 完整分析结果
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
    
    # 调用完整分析服务
    analyzer = NVIDIAAnalyzer()
    result = await analyzer.full_analysis(file_content, file.content_type)
    
    return result


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
