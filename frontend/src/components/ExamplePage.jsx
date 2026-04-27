import React from 'react'

function ExamplePage({ onBack }) {
    // 模拟辩论数据
    const mockMessages = [
        {
            speaker: '主持人',
            content: '辩论开始！辩题：AI会取代程序员吗？',
            round: 1,
            timestamp: '10:00:00'
        },
        {
            speaker: 'phoenix_riser',
            content: '我认为AI不会完全取代程序员，因为编程不仅仅是写代码，还需要创造力和解决问题的能力。',
            round: 1,
            timestamp: '10:01:30'
        },
        {
            speaker: 'zhangxuefeng',
            content: '你说得不对！数据说话，AI在代码生成和bug修复方面已经取得了显著进展，未来很多基础编程工作都会被AI取代。',
            round: 1,
            timestamp: '10:02:45'
        },
        {
            speaker: '主持人',
            content: '双方都有各自的观点，让我们继续深入讨论。',
            round: 1,
            timestamp: '10:03:15'
        },
        {
            speaker: '裁判',
            content: '**最终裁决**：AI会辅助程序员工作，但不会完全取代他们，因为创造力和人类思维是不可替代的。',
            round: 1,
            timestamp: '10:04:00'
        }
    ]

    // 角色图标映射
    const roleIcons = {
        'phoenix_riser': '🔥',
        'zhangxuefeng': '🎓',
        '主持人': '🎭',
        '裁判': '⚖️',
        '用户': '👤'
    }

    // 角色颜色映射
    const roleColors = {
        'phoenix_riser': 'bg-gradient-to-r from-primary to-pink text-white',
        'zhangxuefeng': 'bg-gradient-to-r from-secondary to-blue text-white',
        '主持人': 'bg-gradient-to-r from-accent to-warning text-dark',
        '裁判': 'bg-gradient-to-r from-info to-blue text-white',
        '用户': 'bg-gradient-to-r from-success to-secondary text-white'
    }

    // 角色发光效果
    const roleGlows = {
        'phoenix_riser': 'shadow-glow-primary',
        'zhangxuefeng': 'shadow-glow-secondary',
        '主持人': 'shadow-glow-accent',
        '裁判': 'shadow-glow',
        '用户': 'shadow-glow-secondary'
    }

    const displayNames = {
        phoenix_riser: '底层逆袭者 Phoenix Riser',
        zhangxuefeng: '教育实用导师 Zhang Xuefeng',
        主持人: '主持人',
        裁判: '裁判',
        用户: '用户'
    }

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
                            onClick={onBack} 
                            className="px-6 py-3 bg-gradient-to-r from-dark to-gray-700 text-white rounded-2xl hover:from-dark/80 hover:to-gray-700/80 transition-all shadow-cute font-medium"
                        >
                            返回主页
                        </button>
                    </div>
                </div>
            </div>

            {/* 示例说明 */}
            <div className="container mx-auto p-6">
                <div className="bg-white rounded-3xl shadow-cute p-8 mb-8 animate-fade-in">
                    <h2 className="text-3xl font-bold text-dark mb-6 flex items-center gap-3">
                        <span className="text-primary text-4xl">📚</span>
                        系统示例说明
                    </h2>
                    <div className="space-y-6 text-gray-700">
                        <p className="text-lg">智能辩论系统允许您：</p>
                        <ul className="list-disc pl-8 space-y-3 text-lg">
                            <li>输入辩论题目，选择辩手进行辩论</li>
                            <li>每轮辩论后，主持人会进行总结</li>
                            <li>裁判会给出最终裁决</li>
                            <li>您可以随时插入自己的观点，辩手会回应</li>
                            <li>每5轮对话会自动生成摘要，平衡token消耗</li>
                        </ul>
                        <p className="font-medium text-lg">以下是系统运行的示例效果：</p>
                    </div>
                </div>

                {/* 示例辩论 */}
                <div className="bg-white rounded-3xl shadow-cute p-8 mb-8 animate-fade-in">
                    <div className="flex flex-col md:flex-row justify-between items-center mb-6">
                        <div className="flex items-center gap-3 mb-4 md:mb-0">
                            <span className="bg-gradient-to-r from-accent to-warning text-dark px-4 py-2 rounded-2xl font-medium text-lg">
                                第1轮
                            </span>
                            <h2 className="text-2xl font-semibold text-dark">
                                辩题：AI会取代程序员吗？
                            </h2>
                        </div>
                        <div className="flex flex-wrap gap-3 justify-center">
                            <div className="flex items-center gap-2 px-4 py-2 rounded-2xl bg-gradient-to-r from-primary to-pink text-white shadow-glow-primary">
                                <span className="text-xl">🔥</span>
                                <span className="font-medium">底层逆袭者 Phoenix Riser</span>
                            </div>
                            <div className="flex items-center gap-2 px-4 py-2 rounded-2xl bg-gradient-to-r from-secondary to-blue text-white shadow-glow-secondary">
                                <span className="text-xl">🎓</span>
                                <span className="font-medium">教育实用导师 Zhang Xuefeng</span>
                            </div>
                        </div>
                    </div>

                    {/* 示例消息 */}
                    <div className="space-y-6">
                        {mockMessages.map((msg, index) => (
                            <div key={index} className="animate-slide-up">
                                <div className="flex items-start gap-4">
                                    <div className={`w-12 h-12 rounded-full flex items-center justify-center ${roleColors[msg.speaker] || 'bg-gray-200 text-dark'} ${roleGlows[msg.speaker] || ''}`}>
                                        {roleIcons[msg.speaker] || '👤'}
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-2">
                                            <span className="font-semibold text-dark text-lg">{displayNames[msg.speaker] || msg.speaker}</span>
                                            <span className="text-xs text-gray-500">{msg.timestamp}</span>
                                        </div>
                                        <div className="bg-gray-50 rounded-2xl p-4 border border-gray-100">
                                            {msg.content}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* 系统功能 */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-white rounded-3xl shadow-cute p-6 animate-fade-in">
                        <div className="text-primary text-4xl mb-4">🎯</div>
                        <h3 className="font-semibold text-dark text-xl mb-3">智能辩论</h3>
                        <p className="text-gray-600">支持多Agent辩论，每个辩手都有独特的观点和风格</p>
                    </div>
                    <div className="bg-white rounded-3xl shadow-cute p-6 animate-fade-in">
                        <div className="text-secondary text-4xl mb-4">📝</div>
                        <h3 className="font-semibold text-dark text-xl mb-3">智能摘要</h3>
                        <p className="text-gray-600">每5轮自动生成摘要，平衡token消耗和上下文完整性</p>
                    </div>
                    <div className="bg-white rounded-3xl shadow-cute p-6 animate-fade-in">
                        <div className="text-accent text-4xl mb-4">👤</div>
                        <h3 className="font-semibold text-dark text-xl mb-3">用户参与</h3>
                        <p className="text-gray-600">您可以随时插入观点，辩手会回应并保持完整上下文</p>
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

export default ExamplePage
