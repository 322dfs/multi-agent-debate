import React, { useEffect, useState } from 'react'
import axios from 'axios'

function ResumeEvaluation({ onBack }) {
  const [positions, setPositions] = useState([])
  const [selectedPosition, setSelectedPosition] = useState('')
  const [resumeFile, setResumeFile] = useState(null)
  const [errorMessage, setErrorMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [evaluation, setEvaluation] = useState(null)
  const [visibleReviews, setVisibleReviews] = useState([])
  const [history, setHistory] = useState([])

  useEffect(() => {
    fetchPositions()
    fetchHistory()
  }, [])

  const fetchPositions = async () => {
    try {
      const response = await axios.get('/api/recruit/positions')
      setPositions(response.data.positions || [])
      if (response.data.positions?.length) {
        setSelectedPosition(response.data.positions[0].id)
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
    if (!selectedPosition) {
      setErrorMessage('请选择岗位。')
      return
    }
    if (!resumeFile) {
      setErrorMessage('请先上传简历文件。')
      return
    }
    setErrorMessage('')
    setIsLoading(true)
    try {
      const formData = new FormData()
      formData.append('position_id', selectedPosition)
      formData.append('resume_file', resumeFile)
      const response = await axios.post('/api/recruit/evaluate', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setEvaluation(response.data)
      await revealReviewsSequentially(response.data.reviews || [])
      fetchHistory()
    } catch (error) {
      setErrorMessage(error.response?.data?.detail || '简历评审失败，请稍后重试。')
    } finally {
      setIsLoading(false)
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
              <select
                value={selectedPosition}
                onChange={(e) => setSelectedPosition(e.target.value)}
                className="w-full rounded-xl border border-gray-300 px-3 py-2 text-sm"
              >
                {positions.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.title}
                  </option>
                ))}
              </select>
              <label className="block text-sm font-medium text-gray-700">上传简历（PDF / DOCX）</label>
              <input
                type="file"
                accept=".pdf,.docx,.txt,.md,.doc"
                onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
                className="w-full rounded-xl border border-gray-300 px-3 py-2 text-sm"
              />
              <button
                onClick={handleEvaluate}
                disabled={isLoading}
                className="w-full rounded-2xl bg-gradient-to-r from-primary to-pink px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
              >
                {isLoading ? '评审进行中...' : '开始评审'}
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
                  <p className="text-gray-500">{formatDateTime(item.created_at)}</p>
                </button>
              ))}
            </div>
          </aside>

          <section className="rounded-3xl bg-white p-5 shadow-cute">
            {!evaluation ? (
              <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 p-8 text-center text-sm text-gray-500">
                上传简历并点击“开始评审”后，这里会按顺序展示各评审 Agent 的意见。
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

