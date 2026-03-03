import React, { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function CircuitUploader({ onAnalysisComplete, onAnalysisError, onStartAnalysis, isLoading }) {
  const [selectedFile, setSelectedFile] = useState(null)
  const [preview, setPreview] = useState(null)

  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0]
    if (file) {
      setSelectedFile(file)
      // 创建预览
      const reader = new FileReader()
      reader.onload = () => {
        setPreview(reader.result)
      }
      reader.readAsDataURL(file)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg'],
      'application/pdf': ['.pdf']
    },
    maxFiles: 1,
    disabled: isLoading
  })

  const handleAnalyze = async () => {
    if (!selectedFile) {
      onAnalysisError({ message: '请先选择电路图文件' })
      return
    }

    onStartAnalysis()

    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      // 调用完整分析 API
      const response = await axios.post(`${API_BASE_URL}/api/v1/full-analysis`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      onAnalysisComplete({
        topology: { analysis: response.data.topology },
        bom: { components: response.data.bom || [], raw_analysis: response.data.function },
        errors: { errors: response.data.errors || [], raw_analysis: null }
      })
    } catch (err) {
      console.error('Analysis error:', err)
      onAnalysisError({
        message: err.response?.data?.detail || err.message || '分析失败，请检查后端服务'
      })
    }
  }

  const handleClear = () => {
    setSelectedFile(null)
    setPreview(null)
  }

  return (
    <div className="uploader-container">
      <div className="upload-section" {...getRootProps()}>
        <input {...getInputProps()} />
        <div className="upload-content">
          <div className="upload-icon">
            {isDragActive ? '📤' : '📁'}
          </div>
          {isDragActive ? (
            <p className="upload-text">松开鼠标上传文件...</p>
          ) : (
            <>
              <p className="upload-text">拖拽电路图到此处，或点击选择文件</p>
              <p className="upload-hint">支持 PNG、JPG、PDF 格式</p>
            </>
          )}
        </div>
      </div>

      {preview && (
        <div className="preview-section">
          <h3>📋 已选择文件</h3>
          <div className="preview-image">
            {selectedFile?.type === 'application/pdf' ? (
              <div className="pdf-preview">
                <span>📄</span>
                <p>{selectedFile.name}</p>
              </div>
            ) : (
              <img src={preview} alt="预览" style={{ maxWidth: '100%', maxHeight: '300px' }} />
            )}
          </div>
          <div className="preview-actions">
            <button 
              className="btn btn-secondary" 
              onClick={handleClear}
              disabled={isLoading}
            >
              清除
            </button>
            <button 
              className="btn btn-primary" 
              onClick={handleAnalyze}
              disabled={isLoading}
            >
              {isLoading ? '分析中...' : '开始分析'}
            </button>
          </div>
        </div>
      )}

      {isLoading && (
        <div className="loading">
          <div className="loading-spinner"></div>
          <p style={{ marginLeft: '15px' }}>AI 正在分析电路图...</p>
        </div>
      )}
    </div>
  )
}

export default CircuitUploader
