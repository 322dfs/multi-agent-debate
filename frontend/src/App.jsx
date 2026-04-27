import React, { useState } from 'react'
import TopicInput from './components/TopicInput'
import DebaterSelection from './components/DebaterSelection'
import DebateArena from './components/DebateArena'
import ExamplePage from './components/ExamplePage'
import ResumeEvaluation from './components/ResumeEvaluation'

function App() {
    const [step, setStep] = useState(0)
    const [topic, setTopic] = useState('')
    const [debaters, setDebaters] = useState([])

    const handleStartDebateFlow = () => {
        setStep(1)
    }

    const handleTopicNext = (selectedTopic) => {
        setTopic(selectedTopic)
        setStep(2)
    }

    const handleDebatersNext = (selectedDebaters) => {
        setDebaters(selectedDebaters)
        setStep(3)
    }

    const handleReset = () => {
        setStep(0)
        setTopic('')
        setDebaters([])
    }

    const handleViewExample = () => {
        setStep(4)
    }

    const handleBackFromExample = () => {
        setStep(0)
    }

    const handleResumeMode = () => {
        setStep(5)
    }

    return (
        <div className="min-h-screen font-sans">
            {step === 0 && (
                <div className="min-h-screen bg-gradient-to-br from-light to-secondary/10 flex flex-col">
                    <div className="flex-1 flex items-center justify-center p-4">
                        <div className="bg-white rounded-3xl shadow-cute p-10 max-w-2xl w-full animate-fade-in">
                            <div className="text-center mb-12">
                                <h1 className="text-4xl font-bold text-gray-900 mb-4 flex items-center justify-center gap-3">
                                    <span className="text-primary text-5xl">🎯</span>
                                    智能辩论系统
                                </h1>
                                <p className="text-gray-600 text-lg mb-8">欢迎使用智能辩论系统，选择以下选项开始：</p>
                            </div>
                            
                            <div className="space-y-6">
                                <button
                                    onClick={handleStartDebateFlow}
                                    className="w-full bg-pink-500 bg-gradient-to-r from-primary to-pink text-white py-4 rounded-2xl hover:from-primary/90 hover:to-pink/90 transition-all shadow-glow-primary font-medium text-lg flex items-center justify-center gap-3 transform hover:scale-105"
                                >
                                    <span className="text-2xl">🚀</span>
                                    开始新辩论
                                </button>
                                <button
                                    onClick={handleViewExample}
                                    className="w-full bg-cyan-500 bg-gradient-to-r from-secondary to-blue text-white py-4 rounded-2xl hover:from-secondary/90 hover:to-blue/90 transition-all shadow-glow-secondary font-medium text-lg flex items-center justify-center gap-3 transform hover:scale-105"
                                >
                                    <span className="text-2xl">📚</span>
                                    查看系统示例
                                </button>
                                <button
                                    onClick={handleResumeMode}
                                    className="w-full bg-gradient-to-r from-purple to-blue text-white py-4 rounded-2xl hover:opacity-90 transition-all shadow-glow font-medium text-lg flex items-center justify-center gap-3 transform hover:scale-105"
                                >
                                    <span className="text-2xl">📄</span>
                                    简历评审模式
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <footer className="bg-dark text-white py-6">
                        <div className="container mx-auto text-center">
                            <p className="text-sm">
                                智能辩论系统 • 每5轮自动生成摘要 • 支持用户参与
                            </p>
                        </div>
                    </footer>
                </div>
            )}
            
            {step === 1 && <TopicInput onNext={handleTopicNext} />}
            {step === 2 && <DebaterSelection topic={topic} onNext={handleDebatersNext} />}
            {step === 3 && <DebateArena topic={topic} debaters={debaters} onReset={handleReset} />}
            {step === 4 && <ExamplePage onBack={handleBackFromExample} />}
            {step === 5 && <ResumeEvaluation onBack={handleBackFromExample} />}
        </div>
    )
}

export default App
