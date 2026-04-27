import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'

function DebateArena({ topic, debaters, onReset }) {
    const initialDebaters = Array.isArray(debaters) ? debaters : []
    const [messages, setMessages] = useState([])
    const [currentRound, setCurrentRound] = useState(1)
    const [isDebating, setIsDebating] = useState(false)
    const [userInput, setUserInput] = useState('')
    const [sessionId, setSessionId] = useState(null)
    const [activeTopic, setActiveTopic] = useState(topic)
    const [activeDebaters, setActiveDebaters] = useState(initialDebaters)
    const [isLoading, setIsLoading] = useState(false)
    const [latestJudgment, setLatestJudgment] = useState(null)
    const [decisionInput, setDecisionInput] = useState('')
    const [errorMessage, setErrorMessage] = useState('')
    const [historySessions, setHistorySessions] = useState([])
    const [historyPreview, setHistoryPreview] = useState(null)
    const [debaterNameMap, setDebaterNameMap] = useState({})
    const [uiTheme, setUiTheme] = useState('business')
    const messagesEndRef = useRef(null)
    const suppressAutoScrollRef = useRef(false)

    // 角色图标映射
    const roleIcons = {
        'phoenix_riser': '🔥',
        'zhangxuefeng': '🎓',
        '程序员': '💻',
        '产品经理': '📱',
        '主持人': '🎭',
        '裁判': '⚖️',
        '用户': '👤'
    }

    // 角色颜色映射
    const roleColors = {
        'phoenix_riser': 'bg-gradient-to-r from-primary to-pink text-white',
        'zhangxuefeng': 'bg-gradient-to-r from-secondary to-blue text-white',
        '程序员': 'bg-gradient-to-r from-purple to-blue text-white',
        '产品经理': 'bg-gradient-to-r from-accent to-warning text-dark',
        '主持人': 'bg-gradient-to-r from-accent to-warning text-dark',
        '裁判': 'bg-gradient-to-r from-info to-blue text-white',
        '用户': 'bg-gradient-to-r from-success to-secondary text-white'
    }

    // 角色发光效果
    const roleGlows = {
        'phoenix_riser': 'shadow-glow-primary',
        'zhangxuefeng': 'shadow-glow-secondary',
        '程序员': 'shadow-glow-primary',
        '产品经理': 'shadow-glow-accent',
        '主持人': 'shadow-glow-accent',
        '裁判': 'shadow-glow',
        '用户': 'shadow-glow-secondary'
    }

    const getSpeakerKey = (speaker) => {
        if (roleIcons[speaker]) return speaker
        const matchedId = Object.keys(debaterNameMap).find((id) => debaterNameMap[id] === speaker)
        return matchedId || speaker
    }

    const getSpeakerName = (speaker) => {
        if (debaterNameMap[speaker]) return debaterNameMap[speaker]
        return speaker
    }

    // 获取辩手的图标
    const getDebaterIcon = (debater) => {
        const key = getSpeakerKey(debater)
        return roleIcons[key] || '👤'
    }

    // 获取辩手的颜色
    const getDebaterColor = (debater) => {
        const key = getSpeakerKey(debater)
        return roleColors[key] || 'bg-gradient-to-r from-primary to-pink text-white'
    }

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        if (suppressAutoScrollRef.current) {
            suppressAutoScrollRef.current = false
            return
        }
        scrollToBottom()
    }, [messages])

    useEffect(() => {
        if (!sessionId) {
            setActiveTopic(topic)
            setActiveDebaters(initialDebaters)
        }
    }, [topic, debaters, sessionId])

    useEffect(() => {
        fetchSessionHistory()
        fetchDebaterDirectory()
    }, [])

    const formatDateTime = (value) => {
        if (!value) return ''
        return new Date(value).toLocaleString()
    }

    const fetchSessionHistory = async () => {
        try {
            const response = await axios.get('/api/debate/sessions')
            setHistorySessions(response.data.sessions || [])
        } catch (error) {
            console.error('Error loading session history:', error)
        }
    }

    const fetchDebaterDirectory = async () => {
        try {
            const response = await axios.get('/api/debaters')
            const map = {}
            for (const item of response.data.debaters || []) {
                map[item.id] = item.name || item.id
            }
            setDebaterNameMap(map)
        } catch (error) {
            console.error('Error loading debater directory:', error)
        }
    }

    const startDebate = async () => {
        if (isLoading) return
        setIsDebating(true)
        setIsLoading(true)
        setErrorMessage('')
        try {
            const response = await axios.post('/api/debate/start', {
                topic: activeTopic,
                debaters: activeDebaters
            })
            const createdSessionId = response.data.session_id
            setSessionId(createdSessionId)
            setCurrentRound(1)
            setMessages([{
                speaker: '主持人',
                content: `辩论开始！辩题：${activeTopic}`,
                round: 1,
                timestamp: new Date().toISOString()
            }])
            await runRound(createdSessionId, 1)
            await fetchSessionHistory()
        } catch (error) {
            console.error('Error starting debate:', error)
            setErrorMessage(error.response?.data?.detail || '启动辩论失败，请检查后端服务是否运行。')
            setIsDebating(false)
        } finally {
            setIsLoading(false)
        }
    }

    const runRound = async (activeSessionId = sessionId, roundNumber = currentRound) => {
        if (!activeSessionId) return
        
        setIsLoading(true)
        setErrorMessage('')
        try {
            const response = await axios.post('/api/debate/round', {
                session_id: activeSessionId
            })
            
            const newMessages = (response.data.messages || []).map(msg => ({
                speaker: msg.speaker,
                content: msg.content,
                round: roundNumber,
                timestamp: msg.timestamp || new Date().toISOString()
            }))

            // 逐条展示发言，便于边看边等待下一位
            for (const item of newMessages) {
                setMessages((prev) => [...prev, item])
                await new Promise((resolve) => setTimeout(resolve, 900))
            }
            setLatestJudgment(response.data.judgment || null)
            
        } catch (error) {
            console.error('Error running round:', error)
            setErrorMessage(error.response?.data?.detail || '运行辩论轮次失败，请稍后重试。')
        } finally {
            setIsLoading(false)
            fetchSessionHistory()
        }
    }

    const handleSendUserInput = async () => {
        if (userInput.trim() && !isLoading) {
            const userMessage = {
                speaker: '用户',
                content: userInput,
                round: currentRound,
                timestamp: new Date().toISOString()
            }
            setMessages(prev => [...prev, userMessage])
            const messageText = userInput
            setUserInput('')
            
            // 发送用户消息到后端
            if (sessionId) {
                try {
                    const response = await axios.post('/api/debate/user-message', {
                        session_id: sessionId,
                        message: messageText
                    })
                    
                    // 处理辩手回应
                    if (response.data.responses) {
                        const responses = response.data.responses.map(msg => ({
                            speaker: msg.speaker,
                            content: msg.content,
                            round: currentRound,
                            timestamp: msg.timestamp || new Date().toISOString()
                        }))
                        setMessages(prev => [...prev, ...responses])
                    }
                } catch (error) {
                    console.error('Error sending user message:', error)
                    setErrorMessage(error.response?.data?.detail || '发送用户消息失败，请稍后再试。')
                }
            }
        }
    }

    const nextRound = async () => {
        if (!sessionId) return
        
        const nextRoundNumber = currentRound + 1
        setCurrentRound(nextRoundNumber)
        
        try {
            await axios.post('/api/debate/next-round', {
                session_id: sessionId
            })
            await runRound(sessionId, nextRoundNumber)
        } catch (error) {
            console.error('Error starting next round:', error)
            setErrorMessage(error.response?.data?.detail || '开始下一轮失败，请稍后重试。')
        }
    }

    const handleDecision = async (decision) => {
        if (!sessionId || isLoading) return
        setIsLoading(true)
        setErrorMessage('')
        try {
            const response = await axios.post('/api/debate/decision', {
                session_id: sessionId,
                decision,
                user_conclusion: decisionInput.trim() || null,
            })
            const notice = decision === 'accept'
                ? '用户接受本轮结论，辩题结束。'
                : `用户否决结论并要求继续辩论：${decisionInput || '请继续补充论证。'}`
            setMessages((prev) => [
                ...prev,
                {
                    speaker: '用户裁决',
                    content: notice,
                    round: response.data.round,
                    timestamp: new Date().toISOString(),
                },
            ])
            if (decision === 'reject') {
                setCurrentRound(response.data.round)
                setLatestJudgment(null)
            } else {
                setLatestJudgment((prev) => ({
                    ...(prev || {}),
                    proposed_conclusion: response.data.final_conclusion || prev?.proposed_conclusion,
                    continue_debate: false,
                }))
            }
            setDecisionInput('')
        } catch (error) {
            setErrorMessage(error.response?.data?.detail || '提交裁决失败。')
        } finally {
            setIsLoading(false)
            fetchSessionHistory()
        }
    }

    const loadHistorySession = async (targetSessionId) => {
        if (isLoading) return
        setIsLoading(true)
        setErrorMessage('')
        try {
            const response = await axios.get(`/api/debate/history/${targetSessionId}`)
            const data = response.data
            setSessionId(data.session_id)
            setActiveTopic(data.topic || topic)
            setActiveDebaters(Array.isArray(data.debaters) ? data.debaters : [])
            setMessages(Array.isArray(data.messages) ? data.messages : [])
            setCurrentRound(data.round || 1)
            const fallbackJudgment = Array.isArray(data.judgments) && data.judgments.length > 0
                ? data.judgments[data.judgments.length - 1]
                : null
            setLatestJudgment(data.latest_judgment || fallbackJudgment)
            setIsDebating(data.status !== 'completed')
            setHistoryPreview({
                session_id: data.session_id,
                topic: data.topic,
                created_at: data.created_at,
                updated_at: data.updated_at,
                messages: Array.isArray(data.messages) ? data.messages : [],
            })
            setDecisionInput('')
            // 切历史时保持当前位置，不自动跳到底部
            suppressAutoScrollRef.current = true
        } catch (error) {
            setErrorMessage(error.response?.data?.detail || '加载历史记录失败，请稍后重试。')
        } finally {
            setIsLoading(false)
        }
    }

    const getDebaterGlow = (debater) => {
        const key = getSpeakerKey(debater)
        return roleGlows[key] || 'shadow-glow-primary'
    }

    const getRoleLabel = (speaker) => {
        if (speaker === '主持人' || speaker === '裁判' || speaker === '用户') return speaker
        if (speaker === '用户裁决') return '最终裁决'
        return `辩手 · ${getSpeakerName(speaker)}`
    }

    const isBusinessTheme = uiTheme === 'business'

    return (
        <div className={`relative min-h-screen overflow-hidden font-sans ${isBusinessTheme ? 'bg-slate-100 text-slate-800' : 'bg-gradient-to-br from-fuchsia-100 via-cyan-100 to-amber-100 text-slate-800'}`}>
            <div className={`pointer-events-none absolute -left-24 -top-20 h-72 w-72 rounded-full blur-3xl ${isBusinessTheme ? 'bg-slate-300/45' : 'bg-fuchsia-300/50'}`} />
            <div className={`pointer-events-none absolute -right-24 top-24 h-80 w-80 rounded-full blur-3xl ${isBusinessTheme ? 'bg-slate-400/30' : 'bg-cyan-300/55'}`} />
            <div className="mx-auto w-full max-w-7xl px-4 py-6 md:px-6 md:py-8">
                <div className={`mb-5 rounded-3xl border p-5 backdrop-blur md:p-6 ${isBusinessTheme ? 'border-slate-200 bg-white shadow-xl shadow-slate-300/60' : 'border-white/90 bg-white/75 shadow-2xl shadow-fuchsia-200/80'}`}>
                    <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                        <div>
                            <h1 className="text-2xl font-bold tracking-tight md:text-3xl">🎯 智能辩论系统</h1>
                            <p className="mt-2 text-sm text-gray-600 md:text-base">
                                第 {currentRound} 轮 · {isDebating ? '辩论进行中' : '准备开始'} · 选中辩手 {activeDebaters.length} 位
                            </p>
                            <div className="mt-3 flex items-center gap-2">
                                <button
                                    type="button"
                                    onClick={() => setUiTheme('business')}
                                    className={`rounded-lg px-3 py-1 text-xs transition ${isBusinessTheme ? 'bg-slate-800 text-white shadow-md' : 'bg-white text-gray-700 border border-gray-200'}`}
                                >
                                    简约商务
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setUiTheme('youth')}
                                    className={`rounded-lg px-3 py-1 text-xs transition ${!isBusinessTheme ? 'bg-gradient-to-r from-fuchsia-500 via-pink-500 to-cyan-500 text-white shadow-md' : 'bg-white text-gray-700 border border-gray-200'}`}
                                >
                                    年轻活力
                                </button>
                            </div>
                        </div>
                        <button
                            onClick={onReset}
                            className={`rounded-2xl px-5 py-3 text-sm font-medium text-white transition md:text-base ${isBusinessTheme ? 'bg-slate-800 hover:bg-slate-700' : 'bg-gradient-to-r from-fuchsia-600 to-cyan-500 hover:opacity-90'}`}
                        >
                            重新开始
                        </button>
                    </div>
                </div>

                {errorMessage ? (
                    <div className="mb-4 rounded-2xl border border-error/30 bg-error/10 px-4 py-3 text-sm text-error shadow-sm">
                        {errorMessage}
                    </div>
                ) : null}

                <div className="grid grid-cols-1 gap-4 lg:grid-cols-[280px_1fr]">
                    <aside className={`rounded-3xl border p-5 backdrop-blur ${isBusinessTheme ? 'border-slate-200 bg-white shadow-lg shadow-slate-300/50' : 'border-white/90 bg-white/75 shadow-xl shadow-fuchsia-200/70'}`}>
                        <h2 className="text-base font-semibold">辩题</h2>
                        <p className="mt-2 rounded-xl bg-gray-50 p-3 text-sm leading-6">{activeTopic}</p>

                        <h3 className="mt-5 text-base font-semibold">参与者</h3>
                        <div className="mt-3 space-y-2">
                            {activeDebaters.map((debater, index) => (
                                <div
                                    key={index}
                                    className={`flex items-center gap-2 rounded-xl px-3 py-2 text-sm ${getDebaterColor(debater)} ${getDebaterGlow(debater)}`}
                                >
                                    <span>{getDebaterIcon(debater)}</span>
                                    <span className="truncate">{getSpeakerName(debater)}</span>
                                </div>
                            ))}
                        </div>

                        <div className="mt-5 space-y-3">
                            {!isDebating ? (
                                <button
                                    onClick={startDebate}
                                    disabled={isLoading}
                                    className="w-full rounded-2xl bg-gradient-to-r from-primary to-pink px-4 py-3 text-sm font-medium text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                                >
                                    开始辩论
                                </button>
                            ) : (
                                <button
                                    onClick={nextRound}
                                    disabled={isLoading}
                                    className="w-full rounded-2xl bg-gradient-to-r from-secondary to-blue px-4 py-3 text-sm font-medium text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                                >
                                    下一轮
                                </button>
                            )}
                            <p className="text-xs text-gray-500">提示：可在右侧消息输入框随时插入你的观点。</p>
                        </div>

                        <h3 className="mt-6 text-base font-semibold">历史记录（含日期）</h3>
                        <div className="mt-2 max-h-56 space-y-2 overflow-y-auto">
                            {historySessions.slice(0, 8).map((item) => (
                                <button
                                    key={item.session_id}
                                    type="button"
                                    onClick={() => loadHistorySession(item.session_id)}
                                    className={`w-full rounded-xl border px-3 py-2 text-left text-xs transition-all ${
                                        item.session_id === sessionId
                                            ? 'border-primary/35 bg-primary/10 shadow-sm'
                                            : 'border-gray-200 bg-gray-50 hover:-translate-y-[1px] hover:bg-gray-100'
                                    }`}
                                >
                                    <p className="line-clamp-1 font-medium text-gray-700">{item.topic}</p>
                                    <p className="mt-1 text-gray-500">{formatDateTime(item.created_at)}</p>
                                    <p className="text-gray-500">状态：{item.status} · 轮次：{item.round}</p>
                                </button>
                            ))}
                        </div>

                        {historyPreview ? (
                            <div className="mt-4 rounded-2xl border border-gray-200 bg-white p-3 shadow-sm">
                                <p className="text-sm font-semibold text-gray-800">历史记录内容</p>
                                <p className="mt-1 line-clamp-2 text-xs text-gray-600">{historyPreview.topic}</p>
                                <p className="mt-1 text-xs text-gray-500">
                                    创建于：{formatDateTime(historyPreview.created_at)}
                                </p>
                                <div className="mt-2 max-h-48 space-y-2 overflow-y-auto rounded-xl bg-gray-50 p-2">
                                    {historyPreview.messages.length === 0 ? (
                                        <p className="text-xs text-gray-500">该历史记录暂无消息内容。</p>
                                    ) : (
                                        historyPreview.messages.slice(-12).map((item, idx) => (
                                            <div key={`${item.timestamp || idx}-${idx}`} className="rounded-lg border border-gray-200 bg-white p-2">
                                                <p className="text-xs font-medium text-gray-700">
                                                    {getSpeakerName(item.speaker)} · {formatDateTime(item.timestamp)}
                                                </p>
                                                <p className="mt-1 line-clamp-3 text-xs text-gray-600">{item.content}</p>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>
                        ) : null}
                    </aside>

                    <section className={`flex min-h-[65vh] flex-col rounded-3xl border p-4 backdrop-blur md:p-6 ${isBusinessTheme ? 'border-slate-200 bg-white shadow-lg shadow-slate-300/50' : 'border-white/90 bg-white/75 shadow-xl shadow-cyan-200/70'}`}>
                        <div className="mb-4 flex items-center justify-between">
                            <h2 className="text-lg font-semibold md:text-xl">辩论过程</h2>
                            <span className="rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-600">
                                消息 {messages.length} 条
                            </span>
                        </div>

                        <div className={`flex-1 overflow-y-auto rounded-2xl border p-3 md:p-4 ${isBusinessTheme ? 'border-slate-200 bg-gradient-to-b from-slate-50 to-white' : 'border-fuchsia-200 bg-gradient-to-b from-fuchsia-50 via-pink-50 to-cyan-50'}`}>
                            {messages.length === 0 && !isLoading ? (
                                <div className="rounded-xl border border-dashed border-gray-300 bg-white p-6 text-center text-sm text-gray-500">
                                    点击“开始辩论”后，这里会显示完整辩论过程。
                                </div>
                            ) : null}

                            {messages.map((msg, index) => (
                                <div key={index} className="mb-4 animate-slide-up">
                                    <div className="flex items-start gap-3">
                                        <div className={`mt-1 flex h-10 w-10 items-center justify-center rounded-full text-sm ${getDebaterColor(msg.speaker)}`}>
                                            {getDebaterIcon(msg.speaker)}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="mb-1 flex flex-wrap items-center gap-2">
                                                <span className="text-sm font-semibold">{getSpeakerName(msg.speaker)}</span>
                                                <span className="text-xs text-gray-500">{getRoleLabel(msg.speaker)}</span>
                                                <span className="text-xs text-gray-400">{formatDateTime(msg.timestamp)}</span>
                                            </div>
                                            <div className={`rounded-xl border p-3 text-sm leading-6 shadow-sm md:text-base ${isBusinessTheme ? 'border-slate-200 bg-white text-slate-700' : 'border-fuchsia-100 bg-white/95 text-slate-700'}`}>
                                                {msg.content}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                            {isLoading ? (
                                <div className="flex items-center gap-3 py-4 text-gray-500">
                                    <div className="h-6 w-6 animate-spin rounded-full border-b-2 border-primary"></div>
                                    <span className="text-sm">辩论进行中，请稍候...</span>
                                </div>
                            ) : null}
                            <div ref={messagesEndRef} />
                        </div>

                        {latestJudgment ? (
                            <div className="mt-4 rounded-2xl border border-info/40 bg-info/10 p-4 shadow-sm">
                                <h3 className="mb-1 text-sm font-semibold">阶段结论（裁判）</h3>
                                <p className="text-sm leading-6 text-gray-700">
                                    {latestJudgment.proposed_conclusion}
                                </p>
                                <p className="mt-2 text-xs text-gray-600">
                                    置信度：{latestJudgment.confidence} · 是否建议继续辩论：
                                    {latestJudgment.continue_debate ? ' 是' : ' 否'}
                                </p>
                            </div>
                        ) : null}

                        {latestJudgment && !latestJudgment.continue_debate ? (
                            <div className="mt-3 rounded-2xl border border-gray-200 bg-gray-50 p-3 shadow-sm">
                                <label className="mb-2 block text-sm font-medium text-gray-700">
                                    你的裁决（可选）：可以补充你的结论，再决定接受或否决
                                </label>
                                <textarea
                                    value={decisionInput}
                                    onChange={(e) => setDecisionInput(e.target.value)}
                                    rows={3}
                                    className="w-full rounded-xl border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                                    placeholder="例如：我认为你们忽略了普通家庭风险承受能力，请继续辩论..."
                                />
                                <div className="mt-3 flex gap-2">
                                    <button
                                        onClick={() => handleDecision('accept')}
                                        disabled={isLoading}
                                        className="rounded-xl bg-success px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
                                    >
                                        接受结论并结束
                                    </button>
                                    <button
                                        onClick={() => handleDecision('reject')}
                                        disabled={isLoading}
                                        className="rounded-xl bg-error px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
                                    >
                                        否决结论并继续辩论
                                    </button>
                                </div>
                            </div>
                        ) : null}

                        <div className="mt-4 flex flex-col gap-3 md:flex-row">
                            <input
                                type="text"
                                value={userInput}
                                onChange={(e) => setUserInput(e.target.value)}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter') {
                                        e.preventDefault()
                                        handleSendUserInput()
                                    }
                                }}
                                placeholder="输入你的观点或质疑..."
                                className={`flex-1 rounded-2xl border-2 px-4 py-3 text-sm transition focus:outline-none md:text-base ${isBusinessTheme ? 'border-slate-300 focus:ring-4 focus:ring-slate-300/40' : 'border-fuchsia-200 focus:ring-4 focus:ring-fuchsia-300/35'}`}
                            />
                            <button
                                onClick={handleSendUserInput}
                                disabled={!sessionId || isLoading || !userInput.trim()}
                                className={`rounded-2xl px-6 py-3 text-sm font-medium text-white transition disabled:cursor-not-allowed disabled:opacity-50 md:text-base ${isBusinessTheme ? 'bg-slate-800 hover:bg-slate-700' : 'bg-gradient-to-r from-fuchsia-600 via-pink-500 to-cyan-500 hover:opacity-90'}`}
                            >
                                发送观点
                            </button>
                        </div>
                    </section>
                </div>
            </div>

            <footer className="mt-8 bg-dark py-6 text-white">
                <div className="mx-auto w-full max-w-6xl px-4 text-center text-sm md:px-6">
                    智能辩论系统 · 真实角色驱动 · 支持多轮辩论与用户参与
                </div>
            </footer>
        </div>
    )
}

export default DebateArena
