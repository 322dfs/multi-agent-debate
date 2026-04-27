import React, { useState } from 'react'

function TopicInput({ onNext }) {
    const [topic, setTopic] = useState('')

    const handleSubmit = (e) => {
        e.preventDefault()
        if (topic.trim()) {
            onNext(topic.trim())
        }
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-light to-secondary/10 font-sans flex items-center justify-center p-4">
            <div className="bg-white rounded-3xl shadow-cute p-10 max-w-2xl w-full animate-fade-in">
                <div className="text-center mb-12">
                    <h1 className="text-4xl font-bold text-dark mb-4 flex items-center justify-center gap-3">
                        <span className="text-primary text-5xl">🎯</span>
                        智能辩论系统
                    </h1>
                    <p className="text-gray-600 text-lg">输入辩论题目，开始精彩的辩论之旅</p>
                </div>
                
                <form onSubmit={handleSubmit} className="space-y-8">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-3">
                            辩论题目
                        </label>
                        <input
                            type="text"
                            value={topic}
                            onChange={(e) => setTopic(e.target.value)}
                            placeholder="例如：AI会取代程序员吗？"
                            className="w-full px-6 py-4 border-2 border-gray-200 rounded-2xl focus:outline-none focus:ring-4 focus:ring-primary/30 transition-all text-lg"
                            required
                        />
                    </div>
                    
                    <button
                        type="submit"
                        className="w-full bg-gradient-to-r from-primary to-pink text-white py-4 rounded-2xl hover:from-primary/90 hover:to-pink/90 transition-all shadow-glow-primary font-medium text-lg transform hover:scale-105"
                    >
                        下一步
                    </button>
                </form>
            </div>
        </div>
    )
}

export default TopicInput
