/**
 * CircuitAI 国际化 (i18n) 模块
 * 支持中文/英文切换，默认根据浏览器语言自动选择
 */

const zh = {
  title: '⚡ CircuitAI',
  subtitle: 'AI 智能电路图分析工具',
  history: '📜 历史记录',
  historyTitle: '📜 分析历史',
  noHistory: '暂无历史记录',
  loading: '加载中...',
  dropHint: '拖拽电路图到这里 / Ctrl+V 粘贴截图 / 点击选择文件',
  selectFile: '选择文件',
  startAnalysis: '🔍 开始分析',
  reselect: '重新选择',
  retry: '🔄 重试',
  selectFirst: '请先选择图片',
  exportMarkdown: '📄 导出完整报告 (Markdown)',
  exportBOM: '📥 导出 BOM (CSV)',
  exportCSV: '📥 导出 CSV',
  exportMd: '📄 导出 Markdown',
  components: '📋 元件列表',
  topology: '🔌 拓扑结构',
  function: '⚡ 电路功能',
  keyNodes: '📍 关键节点',
  bom: '📦 BOM 物料清单',
  errors: '⚠️ 潜在问题',
  noComponents: '未识别到元件',
  componentId: '编号',
  componentType: '类型',
  componentParam: '参数/型号',
  componentQty: '数量',
  componentPins: '引脚/说明',
  bomIndex: '#',
  bomName: '元件名称',
  bomModel: '型号/参数',
  bomQty: '数量',
  bomRemarks: '备注',
  statComponents: '元件识别',
  statBOM: 'BOM 物料',
  statErrors: '潜在问题',
  statOk: '无问题',
  suggestion: '💡 建议：',
  typicalApp: '💡 典型应用：',
  footer: 'CircuitAI © 2026 · Powered by AI',
  pdfFile: 'PDF 文件',
  unnamed: '未命名',
  componentUnit: '元件',
  issueUnit: '问题',
  unknownIssue: '未知问题',
  // Loading stages
  stage_upload: '📤 上传文件中...',
  stage_recognize: '🤖 AI 正在识别元件...',
  stage_topology: '🔍 分析拓扑结构...',
  stage_bom: '📦 生成 BOM 物料清单...',
  stage_detect: '⚠️ 检测潜在问题...',
  stage_report: '📝 整理分析报告...',
  // Topology labels
  topo_power_path: '⚡ 电源路径',
  topo_signal_path: '📡 信号路径',
  topo_grounding: '🔌 接地方式',
  topo_ground_method: '🔌 接地方式',
  topo_modules: '📦 模块划分',
  topo_module_division: '📦 模块划分',
  timeout: '分析超时，请稍后重试',
  errorBoundaryTitle: '页面出错了',
  fileTooLarge: '文件过大（最大 10MB），请压缩后重试',
  rateLimited: '请求过于频繁，请稍后再试',
  invalidFileType: '不支持的文件类型，请上传 PNG/JPG/JPEG/WEBP/PDF',
}

const en = {
  title: '⚡ CircuitAI',
  subtitle: 'AI-Powered Circuit Diagram Analyzer',
  history: '📜 History',
  historyTitle: '📜 Analysis History',
  noHistory: 'No history yet',
  loading: 'Loading...',
  dropHint: 'Drop circuit diagram here / Ctrl+V to paste / Click to select file',
  selectFile: 'Select File',
  startAnalysis: '🔍 Analyze',
  reselect: 'Reselect',
  retry: '🔄 Retry',
  selectFirst: 'Please select a file first',
  exportMarkdown: '📄 Export Report (Markdown)',
  exportBOM: '📥 Export BOM (CSV)',
  exportCSV: '📥 Export CSV',
  exportMd: '📄 Export Markdown',
  components: '📋 Components',
  topology: '🔌 Topology',
  function: '⚡ Circuit Function',
  keyNodes: '📍 Key Nodes',
  bom: '📦 BOM (Bill of Materials)',
  errors: '⚠️ Potential Issues',
  noComponents: 'No components detected',
  componentId: 'Ref',
  componentType: 'Type',
  componentParam: 'Value/Model',
  componentQty: 'Qty',
  componentPins: 'Pins/Notes',
  bomIndex: '#',
  bomName: 'Component',
  bomModel: 'Model/Value',
  bomQty: 'Qty',
  bomRemarks: 'Notes',
  statComponents: 'Components',
  statBOM: 'BOM Items',
  statErrors: 'Issues',
  statOk: 'No Issues',
  suggestion: '💡 Suggestion: ',
  typicalApp: '💡 Applications: ',
  footer: 'CircuitAI © 2026 · Powered by AI',
  pdfFile: 'PDF File',
  unnamed: 'Unnamed',
  componentUnit: 'components',
  issueUnit: 'issues',
  unknownIssue: 'Unknown Issue',
  // Loading stages
  stage_upload: '📤 Uploading...',
  stage_recognize: '🤖 Recognizing components...',
  stage_topology: '🔍 Analyzing topology...',
  stage_bom: '📦 Generating BOM...',
  stage_detect: '⚠️ Detecting issues...',
  stage_report: '📝 Preparing report...',
  // Topology labels
  topo_power_path: '⚡ Power Path',
  topo_signal_path: '📡 Signal Path',
  topo_grounding: '🔌 Grounding',
  topo_ground_method: '🔌 Grounding',
  topo_modules: '📦 Modules',
  topo_module_division: '📦 Modules',
  timeout: 'Analysis timed out, please try again later',
  errorBoundaryTitle: 'Something went wrong',
  fileTooLarge: 'File too large (max 10MB), please compress and retry',
  rateLimited: 'Too many requests, please try again later',
  invalidFileType: 'Unsupported file type. Please upload PNG/JPG/JPEG/WEBP/PDF',
}

const translations = { zh, en }

/**
 * 检测默认语言
 */
function detectLang() {
  // 优先 localStorage
  const saved = localStorage.getItem('circuitai_lang')
  if (saved && translations[saved]) return saved
  // 浏览器语言
  const nav = navigator.language || ''
  if (nav.startsWith('zh')) return 'zh'
  return 'en'
}

let currentLang = detectLang()

/**
 * 获取翻译文本
 * @param {string} key
 * @returns {string}
 */
export function t(key) {
  return (translations[currentLang] || translations.en)[key] || key
}

/**
 * 获取当前语言
 */
export function getLang() {
  return currentLang
}

/**
 * 切换语言
 * @param {string} lang - 'zh' | 'en'
 */
export function setLang(lang) {
  if (translations[lang]) {
    currentLang = lang
    localStorage.setItem('circuitai_lang', lang)
  }
}

export default { t, getLang, setLang }
