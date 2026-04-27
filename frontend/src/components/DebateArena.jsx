import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'

function DebateArena({ topic, debaters, onReset }) {
    const [messages, setMessages] = useState([])
    const [currentRound, setCurrentRound] = useState(1)
    const [isDebating, setIsDebating] = useState(false)
    const [currentSpeaker, setCurrentSpeaker] = useState(null)
    const [userInput, setUserInput] = useState('')
    const [sessionId, setSessionId] = useState(null)
    const [isLoading, setIsLoading] = useState(false)
    const [summary, setSummary] = useState('')
    const [isSummarizing, setIsSummarizing] = useState(false)
    const messagesEndRef = useRef(null)

    // 角色图标映射
    const roleIcons = {
        'subencai': '👨‍💼',
        'zhangxuefeng': '🎓',
        '主持人': '🎭',
        '裁判': '⚖️',
        '用户': '👤'
    }

    // 角色颜色映射
    const roleColors = {
        'subencai': 'bg-gradient-to-r from-primary to-pink text-white',
        'zhangxuefeng': 'bg-gradient-to-r from-secondary to-blue text-white',
        '主持人': 'bg-gradient-to-r from-accent to-warning text-dark',
        '裁判': 'bg-gradient-to-r from-info to-blue text-white',
        '用户': 'bg-gradient-to-r from-success to-secondary text-white'
    }

    // 角色发光效果
    const roleGlows = {
        'subencai': 'shadow-glow-primary',
        'zhangxuefeng': 'shadow-glow-secondary',
        '主持人': 'shadow-glow-accent',
        '裁判': 'shadow-glow',
        '用户': 'shadow-glow-secondary'
    }

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    useEffect(() => {
        if (messages.length > 0 && (messages.length + 1) % 5 === 0 && !isSummarizing) {
            generateSummary()
        }
    }, [messages])

    const generateSummary = async () => {
        if (!sessionId) return
        
        setIsSummarizing(true)
        try {
            const response = await axios.post('http://localhost:8000/api/debate/moderate', {
                session_id: sessionId
            })
            setSummary(response.data.summary)
            setMessages(prev => [...prev, {
                speaker: '主持人',
                content: `**辩论摘要**：${response.data.summary}`,
                round: currentRound,
                timestamp: new Date().toLocaleTimeString()
            }])
        } catch (error) {
            console.error('Error generating summary:', error)
        } finally {
            setIsSummarizing(false)
        }
    }

    const startDebate = async () => {
        setIsDebating(true)
        setIsLoading(true)
        try {
            const response = await axios.post('http://localhost:8000/api/debate/start', {
                topic: topic,
                debaters: debaters
            })
            setSessionId(response.data.session_id)
            setMessages([{
                speaker: '主持人',
                content: `辩论开始！辩题：${topic}`,
                round: 1,
                timestamp: new Date().toLocaleTimeString()
            }])
            await runRound()
        } catch (error) {
            console.error('Error starting debate:', error)
            console.error('Error response:', error.response)
            console.error('Error message:', error.message)
            console.error('Error config:', error.config)
            alert('启动辩论失败，请检查后端服务是否运行。错误：' + error.message)
            setIsDebating(false)
        } finally {
            setIsLoading(false)
        }
    }

    const runRound = async () => {
        if (!sessionId) return
        
        setIsLoading(true)
        try {
            const response = await axios.post('http://localhost:8000/api/debate/round', {
                session_id: sessionId
            })
            
            const newMessages = response.data.messages.map(msg => ({
                speaker: msg.speaker,
                content: msg.content,
                round: currentRound,
                timestamp: new Date().toLocaleTimeString()
            }))
            
            setMessages(prev => [...prev, ...newMessages])
            
            // 主持人总结
            const moderatorResponse = await axios.post('http://localhost:8000/api/debate/moderate', {
                session_id: sessionId
            })
            
            setMessages(prev => [...prev, {
                speaker: '主持人',
                content: moderatorResponse.data.summary,
                round: currentRound,
                timestamp: new Date().toLocaleTimeString()
            }])
            
            // 裁判裁决
            const judgeResponse = await axios.post('http://localhost:8000/api/debate/judge', {
                session_id: sessionId
            })
            
            setMessages(prev => [...prev, {
                speaker: '裁判',
                content: `**最终裁决**：${judgeResponse.data.judgment}`,
                round: currentRound,
                timestamp: new Date().toLocaleTimeString()
            }])
            
        } catch (error) {
            console.error('Error running round:', error)
            alert('运行辩论轮次失败')
        } finally {
            setIsLoading(false)
        }
    }

    const handleUserInput = async (e) => {
        if (e.key === 'Enter' && userInput.trim()) {
            const userMessage = {
                speaker: '用户',
                content: userInput,
                round: currentRound,
                timestamp: new Date().toLocaleTimeString()
            }
            setMessages(prev => [...prev, userMessage])
            setUserInput('')
            
            // 发送用户消息到后端
            if (sessionId) {
                try {
                    const response = await axios.post('http://localhost:8000/api/debate/user-message', {
                        session_id: sessionId,
                        message: userInput
                    })
                    
                    // 处理辩手回应
                    if (response.data.responses) {
                        const responses = response.data.responses.map(msg => ({
                            speaker: msg.speaker,
                            content: msg.content,
                            round: currentRound,
                            timestamp: new Date().toLocaleTimeString()
                        }))
                        setMessages(prev => [...prev, ...responses])
                    }
                } catch (error) {
                    console.error('Error sending user message:', error)
                }
            }
        }
    }

    const nextRound = async () => {
        if (!sessionId) return
        
        setCurrentRound(prev => prev + 1)
        setMessages(prev => [...prev, {
            speaker: '主持人',
            content: `第${currentRound + 1}轮开始！`,
            round: currentRound + 1,
            timestamp: new Date().toLocaleTimeString()
        }])
        
        try {
            await axios.post('http://localhost:8000/api/debate/next-round', {
                session_id: sessionId
            })
            await runRound()
        } catch (error) {
            console.error('Error starting next round:', error)
            alert('开始下一轮失败')
        }
    }

    useEffect(() => {
        if (isDebating && !sessionId) {
            startDebate()
        }
    }, [isDebating])

    return (
        <div className="min-h-screen bg-gradient-to-br from-light to-secondary/10 font-sans">
            {/* 顶部导航栏 */}
            <div className="bg-white shadow-cute p-6">
                <div className="container mx-auto flex justify-between items-center">
                    <h1 className="text-3xl font-bold text-dark flex items-center gap-3">
                        <span className="text-primary text-4xl">🎯</span>
                        智能辩论系统
                    </h1>
                    <div className="flex items-center gap-6">
                        <button 
                            onClick={onReset} 
                            className="px-6 py-3 bg-gradient-to-r from-dark to-gray-700 text-white rounded-2xl hover:from-dark/80 hover:to-gray-700/80 transition-all shadow-cute font-medium"
                        >
                            重新开始
                        </button>
                    </div>
                </div>
            </div>

            {/* 辩论信息 */}
            <div className="container mx-auto p-6">
                <div className="bg-white rounded-3xl shadow-cute p-8 mb-8 animate-fade-in">
                    <div className="flex flex-col md:flex-row justify-between items-center mb-6">
                        <div className="flex items-center gap-3 mb-4 md:mb-0">
                            <span className="bg-gradient-to-r from-accent to-warning text-dark px-4 py-2 rounded-2xl font-medium text-lg">
                                第{currentRound}轮
                            </span>
                            <h2 className="text-2xl font-semibold text-dark">
                                辩题：{topic}
                            </h2>
                        </div>
                        <div className="flex flex-wrap gap-3 justify-center">
                            {debaters.map((debater, index) => (
                                <div 
                                    key={index} 
                                    className={`flex items-center gap-2 px-4 py-2 rounded-2xl ${roleColors[debater] || 'bg-gray-200 text-dark'} ${roleGlows[debater] || ''}`}
                                >
                                    <span className="text-xl">{roleIcons[debater] || '👤'}</span>
                                    <span className="font-medium">{debater}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* 消息区域 */}
                <div className="bg-white rounded-3xl shadow-cute p-6 mb-8 max-h-[600px] overflow-y-auto animate-fade-in">
                    {messages.map((msg, index) => (
                        <div key={index} className="mb-6 animate-slide-up">
                            <div className="flex items-start gap-4">
                                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${roleColors[msg.speaker] || 'bg-gray-200 text-dark'} ${roleGlows[msg.speaker] || ''}`}>
                                    {roleIcons[msg.speaker] || '👤'}
                                </div>
                                <div className="flex-1">
                                    <div className="flex items-center gap-3 mb-2">
                                        <span className="font-semibold text-dark text-lg">{msg.speaker}</span>
                                        <span className="text-xs text-gray-500">{msg.timestamp}</span>
                                    </div>
                                    <div className="bg-gray-50 rounded-2xl p-4 border border-gray-100">
                                        {msg.content}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                    {isLoading && (
                        <div className="flex items-center gap-3 text-gray-500 py-4">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-4 border-primary"></div>
                            <span className="font-medium">辩论进行中...</span>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* 摘要区域 */}
                {summary && (
                    <div className="bg-gradient-to-r from-accent/20 to-warning/20 border-2 border-accent rounded-3xl p-6 mb-8 animate-fade-in">
                        <h3 className="font-semibold text-dark text-lg mb-3 flex items-center gap-2">
                            <span className="text-accent text-2xl">📝</span>
                            辩论摘要
                        </h3>
                        <p className="text-gray-700">{summary}</p>
                    </div>
                )}

                {/* 输入区域 */}
                <div className="bg-white rounded-3xl shadow-cute p-6 animate-fade-in">
                    <div className="flex gap-4">
                        <input
                            type="text"
                            value={userInput}
                            onChange={(e) => setUserInput(e.target.value)}
                            onKeyPress={handleUserInput}
                            placeholder="输入你的观点或质疑..."
                            className="flex-1 px-6 py-4 border-2 border-gray-200 rounded-2xl focus:outline-none focus:ring-4 focus:ring-primary/30 transition-all text-lg"
                        />
                        <button
                            onClick={() => handleUserInput({ key: 'Enter' })}
                            className="bg-gradient-to-r from-primary to-pink text-white px-8 py-4 rounded-2xl hover:from-primary/90 hover:to-pink/90 transition-all shadow-glow-primary font-medium transform hover:scale-105"
                        >
                            发送
                        </button>
                    </div>
                    <div className="flex justify-center gap-6 mt-6">
                        {isDebating && (
                            <button
                                onClick={nextRound}
                                className="bg-gradient-to-r from-secondary to-blue text-white px-10 py-4 rounded-2xl hover:from-secondary/90 hover:to-blue/90 transition-all shadow-glow-secondary font-medium text-lg transform hover:scale-105"
                            >
                                下一轮
                            </button>
                        )}
                        {!isDebating && (
                            <button
                                onClick={startDebate}
                                className="bg-gradient-to-r from-primary to-pink text-white px-12 py-4 rounded-2xl hover:from-primary/90 hover:to-pink/90 transition-all shadow-glow-primary font-medium text-lg transform hover:scale-105"
                            >
                                开始辩论
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* 页脚 */}
            <footer className="bg-dark text-white py-8 mt-12">
                <div className="container mx-auto text-center">
                    <p className="text-sm">
                        智能辩论系统 • 每5轮自动生成摘要 • 支持用户参与
                    </p>
                </div>
            </footer>
        </div>
    )
}

export default DebateArena
