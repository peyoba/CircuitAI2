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

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Any

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

import csv
import io
import uuid
import threading
import time
import logging
import fitz  # PyMuPDF — PDF to image conversion

logger = logging.getLogger("circuitai")

# 文件大小限制：10MB
MAX_FILE_SIZE = 10 * 1024 * 1024

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


# ==================== 文件校验工具 ====================

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif", "pdf"}
EXT_MIME_MAP = {
    "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
    "webp": "image/webp", "gif": "image/gif", "pdf": "application/pdf",
}
ALLOWED_MIMES = set(EXT_MIME_MAP.values()) | {"application/octet-stream"}


def pdf_to_png(pdf_bytes: bytes, dpi: int = 200) -> bytes:
    """将 PDF 第一页转换为 PNG 图片（使用 PyMuPDF）。
    
    电路原理图通常只有一页，取第一页即可。
    dpi=200 在清晰度和文件大小之间取平衡。
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    if len(doc) == 0:
        raise ValueError("PDF 文件无页面")
    page = doc[0]
    zoom = dpi / 72  # 72 is PDF default DPI
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    png_bytes = pix.tobytes("png")
    doc.close()
    return png_bytes


async def validate_and_read(file: UploadFile) -> tuple[bytes, str]:
    """校验上传文件并返回 (内容, content_type)。
    
    PDF 文件会自动转换为 PNG 图片，因为视觉模型只接受图片格式。
    不合规时抛 HTTPException。
    """
    content_type = file.content_type or "application/octet-stream"
    ext = (file.filename or "").rsplit(".", 1)[-1].lower() if file.filename else ""

    # 从扩展名修正 MIME
    if content_type in ("application/octet-stream", "") and ext in EXT_MIME_MAP:
        content_type = EXT_MIME_MAP[ext]

    if content_type not in ALLOWED_MIMES:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file.content_type}。支持: PNG, JPG, WebP, PDF")

    file_content = await file.read()

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"文件过大: {len(file_content)/(1024*1024):.1f}MB，上限 10MB")

    if len(file_content) == 0:
        raise HTTPException(status_code=400, detail="文件为空")

    # PDF → PNG 转换：视觉模型需要图片格式
    if content_type == "application/pdf":
        try:
            file_content = pdf_to_png(file_content)
            content_type = "image/png"
            logger.info("PDF 已转换为 PNG (%d bytes)", len(file_content))
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"PDF 转换失败: {str(e)}")

    return file_content, content_type


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
    file_content, content_type = await validate_and_read(file)
    
    analyzer = NVIDIAAnalyzer()
    result = await analyzer.analyze(file_content, content_type)
    
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
    file_content, content_type = await validate_and_read(file)
    
    bom_gen = BOMGenerator()
    bom_list = await bom_gen.generate(file_content, content_type)
    
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
    file_content, content_type = await validate_and_read(file)
    
    detector = ErrorDetector()
    errors = await detector.detect(file_content, content_type)
    
    return errors


@app.post("/api/v1/full-analysis", response_model=AnalysisResult)
async def full_analysis(file: UploadFile = File(...)):
    """
    完整分析（识别 + BOM + 错误检测）
    """
    logger.info(f"收到文件: {file.filename}, 类型: {file.content_type}, 大小: {file.size}")
    
    file_content, content_type = await validate_and_read(file)
    logger.info(f"文件校验通过, 大小: {len(file_content)} bytes")
    
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
    file_content, content_type = await validate_and_read(file)
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


# ==================== BOM 导出 ====================

@app.get("/api/v1/task/{task_id}/export-bom")
async def export_bom_csv(task_id: str, filename: str = Query("bom.csv")):
    """将已完成任务的 BOM 表导出为 CSV 文件"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks[task_id]
    if task["status"] != "done":
        raise HTTPException(status_code=400, detail="任务尚未完成")
    
    bom = (task.get("result") or {}).get("bom") or []
    if not bom:
        raise HTTPException(status_code=404, detail="无 BOM 数据")
    
    # 生成 CSV（带 BOM 头以便 Excel 正确识别 UTF-8）
    buf = io.StringIO()
    buf.write('\ufeff')  # UTF-8 BOM for Excel
    writer = csv.writer(buf)
    writer.writerow(["序号", "元件名称", "型号/参数", "数量", "备注"])
    for i, item in enumerate(bom, 1):
        writer.writerow([
            item.get("index", i),
            item.get("name", ""),
            item.get("model", item.get("value", "")),
            item.get("quantity", ""),
            item.get("remarks", ""),
        ])
    
    content = buf.getvalue().encode("utf-8")
    return StreamingResponse(
        io.BytesIO(content),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ==================== Markdown 导出 ====================

@app.get("/api/v1/task/{task_id}/export-markdown")
async def export_markdown(task_id: str, filename: str = Query("circuit_analysis.md")):
    """将已完成任务的完整分析结果导出为 Markdown 文件"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = tasks[task_id]
    if task["status"] != "done":
        raise HTTPException(status_code=400, detail="任务尚未完成")

    result = task.get("result") or {}
    lines = ["# CircuitAI 电路分析报告\n"]

    # 电路功能
    func = result.get("function")
    if func:
        lines.append("## ⚡ 电路功能\n")
        if isinstance(func, str):
            lines.append(func + "\n")
        else:
            if func.get("circuit_type"):
                lines.append(f"**电路类型**: {func['circuit_type']}\n")
            if func.get("description"):
                lines.append(f"{func['description']}\n")
            if func.get("applications"):
                lines.append(f"**典型应用**: {func['applications']}\n")

    # 元件列表
    components = result.get("components") or []
    if components:
        lines.append("## 📋 元件列表\n")
        lines.append("| 编号 | 类型 | 参数/型号 | 数量 | 说明 |")
        lines.append("|------|------|-----------|------|------|")
        for c in components:
            ref = c.get("ref") or c.get("name") or "-"
            ctype = c.get("type") or "-"
            value = c.get("value") or c.get("model") or "-"
            qty = c.get("quantity", 1)
            desc = c.get("pins") or c.get("remarks") or "-"
            lines.append(f"| {ref} | {ctype} | {value} | {qty} | {desc} |")
        lines.append("")

    # 拓扑结构
    topology = result.get("topology")
    if topology:
        lines.append("## 🔌 拓扑结构\n")
        if isinstance(topology, str):
            lines.append(topology + "\n")
        else:
            labels = {
                "power_path": "电源路径", "signal_path": "信号路径",
                "grounding": "接地方式", "ground_method": "接地方式",
                "modules": "模块划分", "module_division": "模块划分",
            }
            for k, v in topology.items():
                label = labels.get(k, k)
                lines.append(f"- **{label}**: {v}\n")

    # 关键节点
    key_nodes = result.get("key_nodes") or []
    if key_nodes:
        lines.append("## 📍 关键节点\n")
        for node in key_nodes:
            text = node.get("name") if isinstance(node, dict) else str(node)
            lines.append(f"- {text}")
        lines.append("")

    # BOM
    bom = result.get("bom") or []
    if bom:
        lines.append("## 📦 BOM 物料清单\n")
        lines.append("| # | 元件名称 | 型号/参数 | 数量 | 备注 |")
        lines.append("|---|----------|-----------|------|------|")
        for i, item in enumerate(bom, 1):
            lines.append(f"| {item.get('index', i)} | {item.get('name', '-')} | {item.get('model', item.get('value', '-'))} | {item.get('quantity', '-')} | {item.get('remarks', '-')} |")
        lines.append("")

    # 错误检测
    errors = result.get("errors") or []
    if errors:
        lines.append("## ⚠️ 潜在问题\n")
        for err in errors:
            severity = err.get("severity", "Medium")
            lines.append(f"### [{severity}] {err.get('type', '未知问题')}\n")
            if err.get("description"):
                lines.append(f"{err['description']}\n")
            if err.get("suggestion"):
                lines.append(f"**建议**: {err['suggestion']}\n")

    lines.append("\n---\n*Generated by CircuitAI*\n")

    content = "\n".join(lines).encode("utf-8")
    return StreamingResponse(
        io.BytesIO(content),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
