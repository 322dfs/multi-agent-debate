import React, { useEffect, useRef, useState } from 'react'
import axios from 'axios'

function ResumeEvaluation({ onBack }) {
  const [positions, setPositions] = useState([])
  const [selectedPosition, setSelectedPosition] = useState('')
  const [selectedPositionDetail, setSelectedPositionDetail] = useState(null)
  const [useCustomPosition, setUseCustomPosition] = useState(false)
  const [customTitle, setCustomTitle] = useState('')
  const [customCompany, setCustomCompany] = useState('上海孛璞半导体技术有限公司')
  const [customResponsibilities, setCustomResponsibilities] = useState('')
  const [customMustHave, setCustomMustHave] = useState('')
  const [customPlus, setCustomPlus] = useState('')
  const [autoSaveCustom, setAutoSaveCustom] = useState(true)
  const [resumeFile, setResumeFile] = useState(null)
  const [errorMessage, setErrorMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [evaluation, setEvaluation] = useState(null)
  const [visibleReviews, setVisibleReviews] = useState([])
  const [history, setHistory] = useState([])
  const [parseResult, setParseResult] = useState(null)
  const [isDragActive, setIsDragActive] = useState(false)
  const fileInputRef = useRef(null)

  useEffect(() => {
    fetchPositions()
    fetchHistory()
  }, [])

  const fetchPositions = async () => {
    try {
      const response = await axios.get('/api/recruit/positions')
      const all = response.data.positions || []
      setPositions(all)
      if (all.length) {
        const currentId = selectedPosition || all[0].id
        const found = all.find((x) => x.id === currentId) || all[0]
        setSelectedPosition(found.id)
        setSelectedPositionDetail(found)
      }
    } catch (error) {
      setErrorMessage('加载岗位列表失败，请检查后端服务。')
    }
  }

  const fetchHistory = async () => {
    try {
      const response = await axios.get('/api/recruit/evaluations')
      setHistory(response.data.evaluations || [])
    } catch (error) {
      // Ignore history load failures to keep upload flow available.
    }
  }

  const formatDateTime = (value) => {
    if (!value) return ''
    return new Date(value).toLocaleString()
  }

  const revealReviewsSequentially = async (reviews) => {
    setVisibleReviews([])
    for (const item of reviews || []) {
      setVisibleReviews((prev) => [...prev, item])
      await new Promise((resolve) => setTimeout(resolve, 800))
    }
  }

  const handleEvaluate = async () => {
    if (!useCustomPosition && !selectedPosition) {
      setErrorMessage('请选择岗位。')
      return
    }
    if (useCustomPosition && !customMustHave.trim()) {
      setErrorMessage('自定义岗位至少填写 1 条核心要求。')
      return
    }
    if (!resumeFile) {
      setErrorMessage('请先上传简历文件。')
      return
    }
    setErrorMessage('')
    setIsLoading(true)
    setParseResult(null)
    try {
      const formData = new FormData()
      if (useCustomPosition) {
        formData.append('custom_position_title', customTitle)
        formData.append('custom_position_company', customCompany)
        formData.append('custom_position_responsibilities', customResponsibilities)
        formData.append('custom_position_must_have', customMustHave)
        formData.append('custom_position_plus', customPlus)
        formData.append('custom_position_save', autoSaveCustom ? '1' : '0')
      } else {
        formData.append('position_id', selectedPosition)
      }
      formData.append('resume_file', resumeFile)
      const response = await axios.post('/api/recruit/evaluate', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setEvaluation(response.data)
      await revealReviewsSequentially(response.data.reviews || [])
      fetchHistory()
      fetchPositions()
      if (useCustomPosition && autoSaveCustom) {
        setUseCustomPosition(false)
        setSelectedPosition(response.data.position_id)
      }
    } catch (error) {
      setErrorMessage(error.response?.data?.detail || '简历评审失败，请稍后重试。')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSaveCustomPosition = async () => {
    if (!customTitle.trim()) {
      setErrorMessage('请填写岗位名称。')
      return
    }
    const mustHave = customMustHave
      .split('\n')
      .map((x) => x.trim())
      .filter(Boolean)
    const plus = customPlus
      .split('\n')
      .map((x) => x.trim())
      .filter(Boolean)
    const responsibilities = customResponsibilities
      .split('\n')
      .map((x) => x.trim())
      .filter(Boolean)
    if (!mustHave.length) {
      setErrorMessage('至少填写 1 条核心要求后再保存岗位模板。')
      return
    }
    setErrorMessage('')
    try {
      const response = await axios.post('/api/recruit/positions', {
        title: customTitle.trim(),
        company: customCompany.trim() || '自定义岗位',
        responsibilities,
        must_have: mustHave,
        plus,
      })
      setUseCustomPosition(false)
      setSelectedPosition(response.data.id)
      fetchPositions()
    } catch (error) {
      setErrorMessage(error.response?.data?.detail || '保存岗位模板失败。')
    }
  }

  const loadHistoryDetail = async (evaluationId) => {
    setIsLoading(true)
    setErrorMessage('')
    try {
      const response = await axios.get(`/api/recruit/evaluations/${evaluationId}`)
      setEvaluation(response.data)
      await revealReviewsSequentially(response.data.reviews || [])
    } catch (error) {
      setErrorMessage(error.response?.data?.detail || '加载历史评审详情失败。')
    } finally {
      setIsLoading(false)
    }
  }

  const onFilePicked = (file) => {
    if (!file) return
    setResumeFile(file)
    setErrorMessage('')
  }

  const handleParseOnly = async () => {
    if (!resumeFile) {
      setErrorMessage('请先选择或拖拽简历文件。')
      return
    }
    setErrorMessage('')
    setIsLoading(true)
    try {
      const formData = new FormData()
      formData.append('resume_file', resumeFile)
      const response = await axios.post('/api/recruit/parse', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setParseResult(response.data)
      setEvaluation(null)
      setVisibleReviews([])
    } catch (error) {
      setErrorMessage(error.response?.data?.detail || '简历解析失败，请稍后重试。')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-light to-secondary/10 p-4 md:p-6">
      <div className="mx-auto max-w-6xl">
        <div className="mb-4 flex flex-col gap-3 rounded-3xl bg-white p-5 shadow-cute md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-dark md:text-3xl">📄 简历多Agent评审</h1>
            <p className="mt-1 text-sm text-gray-600">上传 PDF / DOCX 简历，按孛璞半导体岗位画像自动评估。</p>
          </div>
          <button
            onClick={onBack}
            className="rounded-2xl bg-dark px-5 py-3 text-sm font-medium text-white hover:bg-dark/90"
          >
            返回主页
          </button>
        </div>

        {errorMessage ? (
          <div className="mb-4 rounded-2xl border border-error/30 bg-error/10 px-4 py-3 text-sm text-error">{errorMessage}</div>
        ) : null}

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[330px_1fr]">
          <aside className="rounded-3xl bg-white p-5 shadow-cute">
            <h2 className="text-base font-semibold text-dark">评审配置</h2>
            <div className="mt-3 space-y-3">
              <label className="block text-sm font-medium text-gray-700">目标岗位</label>
              <div className="flex items-center gap-2 text-xs">
                <button
                  type="button"
                  onClick={() => setUseCustomPosition(false)}
                  className={`rounded-lg px-3 py-1 ${!useCustomPosition ? 'bg-primary text-white' : 'bg-gray-100 text-gray-700'}`}
                >
                  选择已有岗位
                </button>
                <button
                  type="button"
                  onClick={() => setUseCustomPosition(true)}
                  className={`rounded-lg px-3 py-1 ${useCustomPosition ? 'bg-primary text-white' : 'bg-gray-100 text-gray-700'}`}
                >
                  自定义岗位/JD
                </button>
              </div>
              {!useCustomPosition ? (
                <select
                  value={selectedPosition}
                  onChange={(e) => {
                    const id = e.target.value
                    setSelectedPosition(id)
                    const found = positions.find((x) => x.id === id) || null
                    setSelectedPositionDetail(found)
                  }}
                  className="w-full rounded-xl border border-gray-300 px-3 py-2 text-sm"
                >
                  {positions.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.title}
                    </option>
                  ))}
                </select>
              ) : (
                <div className="space-y-2">
                  <input
                    type="text"
                    value={customTitle}
                    onChange={(e) => setCustomTitle(e.target.value)}
                    placeholder="岗位名称（如：IT系统运维工程师）"
                    className="w-full rounded-xl border border-gray-300 px-3 py-2 text-sm"
                  />
                  <input
                    type="text"
                    value={customCompany}
                    onChange={(e) => setCustomCompany(e.target.value)}
                    placeholder="公司名称"
                    className="w-full rounded-xl border border-gray-300 px-3 py-2 text-sm"
                  />
                  <textarea
                    value={customResponsibilities}
                    onChange={(e) => setCustomResponsibilities(e.target.value)}
                    placeholder={'岗位职责（每行一条，可选）\n例如：\n负责IT基础设施稳定运行'}
                    rows={3}
                    className="w-full rounded-xl border border-gray-300 px-3 py-2 text-sm"
                  />
                  <textarea
                    value={customMustHave}
                    onChange={(e) => setCustomMustHave(e.target.value)}
                    placeholder={'核心要求（每行一条）\n例如：\n精通Linux运维\n掌握Python脚本'}
                    rows={5}
                    className="w-full rounded-xl border border-gray-300 px-3 py-2 text-sm"
                  />
                  <textarea
                    value={customPlus}
                    onChange={(e) => setCustomPlus(e.target.value)}
                    placeholder={'加分项（每行一条）\n例如：\n有大型企业IT治理经验'}
                    rows={4}
                    className="w-full rounded-xl border border-gray-300 px-3 py-2 text-sm"
                  />
                  <button
                    type="button"
                    onClick={handleSaveCustomPosition}
                    className="w-full rounded-xl bg-gray-100 px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-200"
                  >
                    保存为岗位模板（下次可直接选择）
                  </button>
                  <label className="flex items-center gap-2 text-xs text-gray-600">
                    <input
                      type="checkbox"
                      checked={autoSaveCustom}
                      onChange={(e) => setAutoSaveCustom(e.target.checked)}
                    />
                    评审时自动保存该岗位模板（默认开启）
                  </label>
                </div>
              )}
              {!useCustomPosition && selectedPositionDetail ? (
                <div className="rounded-xl border border-blue-100 bg-blue-50/60 p-3 text-xs text-gray-700">
                  <p className="font-semibold text-gray-800">{selectedPositionDetail.title}</p>
                  <p className="mt-1">公司：{selectedPositionDetail.company}</p>
                  {selectedPositionDetail.responsibilities?.length ? (
                    <div className="mt-2">
                      <p className="font-medium text-gray-800">岗位职责</p>
                      <ul className="list-disc pl-4">
                        {selectedPositionDetail.responsibilities.map((x, i) => <li key={i}>{x}</li>)}
                      </ul>
                    </div>
                  ) : null}
                  <div className="mt-2">
                    <p className="font-medium text-gray-800">核心要求</p>
                    <ul className="list-disc pl-4">
                      {(selectedPositionDetail.must_have || []).map((x, i) => <li key={i}>{x}</li>)}
                    </ul>
                  </div>
                </div>
              ) : null}
              <label className="block text-sm font-medium text-gray-700">上传简历（支持拖拽 PDF / DOCX）</label>
              <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs leading-5 text-emerald-800">
                隐私说明：简历解析与评审在你本机环境处理，不会上传到第三方服务平台。
                若仅想临时查看文本，请使用“仅解析简历（先看内容）”；如点击“开始评审”，会在本机保存评审历史，便于后续回看。
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.txt,.md,.doc"
                onChange={(e) => onFilePicked(e.target.files?.[0] || null)}
                className="hidden"
              />
              <div
                onDragOver={(e) => {
                  e.preventDefault()
                  setIsDragActive(true)
                }}
                onDragLeave={(e) => {
                  e.preventDefault()
                  setIsDragActive(false)
                }}
                onDrop={(e) => {
                  e.preventDefault()
                  setIsDragActive(false)
                  onFilePicked(e.dataTransfer.files?.[0] || null)
                }}
                onClick={() => fileInputRef.current?.click()}
                className={`cursor-pointer rounded-xl border-2 border-dashed px-3 py-4 text-center text-sm ${
                  isDragActive ? 'border-primary bg-primary/5' : 'border-gray-300 bg-gray-50'
                }`}
              >
                {resumeFile ? `已选择：${resumeFile.name}` : '将简历拖到这里，或点击选择文件'}
              </div>
              <button
                onClick={handleEvaluate}
                disabled={isLoading}
                className="w-full rounded-2xl bg-gradient-to-r from-primary to-pink px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
              >
                {isLoading ? '评审进行中...' : '开始评审'}
              </button>
              <button
                onClick={handleParseOnly}
                disabled={isLoading}
                className="w-full rounded-2xl bg-gradient-to-r from-secondary to-blue px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
              >
                {isLoading ? '解析中...' : '仅解析简历（先看内容）'}
              </button>
            </div>

            <h3 className="mt-6 text-base font-semibold text-dark">历史评审</h3>
            <div className="mt-2 max-h-80 space-y-2 overflow-y-auto">
              {history.map((item) => (
                <button
                  key={item.evaluation_id}
                  type="button"
                  onClick={() => loadHistoryDetail(item.evaluation_id)}
                  className="w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2 text-left text-xs hover:bg-gray-100"
                >
                  <p className="line-clamp-1 font-medium text-gray-700">{item.position?.title}</p>
                  <p className="mt-1 text-gray-500">{item.resume_file}</p>
                  <p className="text-gray-500">
                    字符数：{item.char_count || 0} · 行数：{item.line_count || 0}
                  </p>
                  <p className="text-gray-500">{formatDateTime(item.created_at)}</p>
                </button>
              ))}
            </div>
          </aside>

          <section className="rounded-3xl bg-white p-5 shadow-cute">
            {!evaluation && !parseResult ? (
              <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 p-8 text-center text-sm text-gray-500">
                上传/拖拽简历后，可先“仅解析简历”，也可直接“开始评审”。
              </div>
            ) : parseResult && !evaluation ? (
              <div className="space-y-3">
                <div className="rounded-2xl border border-secondary/40 bg-secondary/10 p-4">
                  <h3 className="text-base font-semibold text-dark">简历解析结果</h3>
                  <p className="mt-1 text-sm text-gray-700">文件：{parseResult.file_name}</p>
                  <p className="mt-1 text-sm text-gray-700">
                    字符数：{parseResult.char_count} · 行数：{parseResult.line_count}
                  </p>
                </div>
                <div className="rounded-2xl border border-gray-200 bg-gray-50 p-4">
                  <p className="text-sm font-semibold text-dark">完整解析文本</p>
                  <pre className="mt-2 whitespace-pre-wrap text-xs leading-6 text-gray-700">
                    {parseResult.parsed_text || '未提取到文本内容'}
                  </pre>
                </div>
              </div>
            ) : (
              <div>
                <div className="rounded-2xl border border-info/40 bg-info/10 p-4">
                  <h3 className="text-base font-semibold text-dark">{evaluation.position?.title}</h3>
                  <p className="mt-1 text-sm text-gray-700">公司：{evaluation.position?.company}</p>
                  <p className="mt-1 text-sm text-gray-700">
                    最终结论：{evaluation.summary?.final_decision} · 平均分：{evaluation.summary?.average_score}
                  </p>
                </div>

                <div className="mt-4 rounded-2xl border border-gray-200 bg-gray-50 p-4">
                  <p className="text-sm font-semibold text-dark">历史简历原文</p>
                  <p className="mt-1 text-xs text-gray-500">
                    字符数：{evaluation.char_count || 0} · 行数：{evaluation.line_count || 0}
                  </p>
                  <pre className="mt-2 whitespace-pre-wrap text-xs leading-6 text-gray-700">
                    {evaluation.parsed_text || '该历史记录创建时未保存简历文本（旧版本数据）。'}
                  </pre>
                </div>

                <div className="mt-4 space-y-3">
                  {visibleReviews.map((item, idx) => (
                    <div key={`${item.reviewer?.id}_${idx}`} className="rounded-2xl border border-gray-200 bg-gray-50 p-4">
                      <p className="text-sm font-semibold text-dark">{item.reviewer?.name}</p>
                      <p className="mt-1 text-sm text-gray-700">
                        评分：{item.result?.score} · 结论：{item.result?.decision}
                      </p>
                      <p className="mt-2 text-sm leading-6 text-gray-700">{item.result?.summary}</p>
                      <div className="mt-3 grid grid-cols-1 gap-2 md:grid-cols-2">
                        <div>
                          <p className="text-xs font-semibold text-gray-700">亮点</p>
                          <ul className="list-disc pl-5 text-xs text-gray-600">
                            {(item.result?.strengths || []).map((x, i) => <li key={i}>{x}</li>)}
                          </ul>
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-gray-700">风险</p>
                          <ul className="list-disc pl-5 text-xs text-gray-600">
                            {(item.result?.risks || []).map((x, i) => <li key={i}>{x}</li>)}
                          </ul>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  )
}

export default ResumeEvaluation

