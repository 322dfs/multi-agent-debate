import React, { useState } from 'react'

function TopicInput({ onNext, onBack }) {
    const [topic, setTopic] = useState('')
    const exampleTopics = [
        'AI 会取代程序员吗？',
        '年轻人应该先就业还是先读研？',
        '高学历是否仍然是普通家庭最优解？',
        '个人品牌比硬技能更重要吗？'
    ]
    const itTemplates = [
        '【IT决策】是否把公司内部知识库从纯文档检索升级为 RAG + 权限分级？',
        '【IT决策】本季度是否优先上线统一监控告警平台（日志、主机、服务）？',
        '【IT决策】是否将发布流程改为灰度发布 + 自动回滚机制？',
        '【IT决策】是否推进统一身份认证（SSO）与权限最小化改造？',
    ]

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
                    <div className="mb-4 text-left">
                        <button
                            type="button"
                            onClick={onBack}
                            className="rounded-xl border border-gray-200 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                        >
                            返回上一步
                        </button>
                    </div>
                    <h1 className="text-4xl font-bold text-dark mb-4 flex items-center justify-center gap-3">
                        <span className="text-primary text-5xl">🎯</span>
                        智能辩论系统
                    </h1>
                    <p className="text-gray-600 text-lg">输入辩题后进入辩手选择，至少选择 2 位辩手即可开始</p>
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
                        <p className="mt-2 text-sm text-gray-500">建议使用明确、可辩驳的话题，效果会更好。</p>
                        <div className="mt-4">
                            <p className="mb-2 text-sm font-medium text-gray-700">快速示例：</p>
                            <div className="flex flex-wrap gap-2">
                                {exampleTopics.map((item) => (
                                    <button
                                        key={item}
                                        type="button"
                                        onClick={() => setTopic(item)}
                                        className="rounded-full bg-gray-100 px-3 py-1 text-sm text-gray-700 transition hover:bg-gray-200"
                                    >
                                        {item}
                                    </button>
                                ))}
                            </div>
                        </div>
                        <div className="mt-5">
                            <p className="mb-2 text-sm font-medium text-gray-700">IT 部门模板（推荐先用）：</p>
                            <div className="space-y-2">
                                {itTemplates.map((item) => (
                                    <button
                                        key={item}
                                        type="button"
                                        onClick={() => setTopic(item)}
                                        className="block w-full rounded-xl border border-blue-100 bg-blue-50 px-3 py-2 text-left text-sm text-blue-800 transition hover:bg-blue-100"
                                    >
                                        {item}
                                    </button>
                                ))}
                            </div>
                        </div>
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
