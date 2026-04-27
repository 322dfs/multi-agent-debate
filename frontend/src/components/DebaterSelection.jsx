import React, { useState, useEffect } from 'react'
import axios from 'axios'

function DebaterSelection({ topic, onNext }) {
    const [debaters, setDebaters] = useState([])
    const [selectedDebaters, setSelectedDebaters] = useState([])
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        const fetchDebaters = async () => {
            try {
                const response = await axios.get('http://localhost:8000/api/debaters')
                setDebaters(response.data.debaters)
            } catch (error) {
                console.error('Error fetching debaters:', error)
                // 使用默认辩手列表作为备用
                setDebaters(['subencai', 'zhangxuefeng', '程序员', '产品经理'])
            } finally {
                setIsLoading(false)
            }
        }
        fetchDebaters()
    }, [])

    const toggleDebater = (debater) => {
        setSelectedDebaters(prev => {
            if (prev.includes(debater)) {
                return prev.filter(d => d !== debater)
            } else {
                return [...prev, debater]
            }
        })
    }

    const handleSubmit = (e) => {
        e.preventDefault()
        if (selectedDebaters.length >= 2) {
            onNext(selectedDebaters)
        } else {
            alert('请至少选择2位辩手')
        }
    }

    // 角色图标映射
    const roleIcons = {
        'subencai': '👨‍💼',
        'zhangxuefeng': '🎓',
        '程序员': '💻',
        '产品经理': '📱'
    }

    // 角色颜色映射
    const roleColors = {
        'subencai': 'from-primary to-pink',
        'zhangxuefeng': 'from-secondary to-blue',
        '程序员': 'from-purple to-blue',
        '产品经理': 'from-accent to-warning'
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-light to-secondary/10 font-sans p-4">
            <div className="container mx-auto max-w-4xl">
                <div className="bg-white rounded-3xl shadow-cute p-10 animate-fade-in">
                    <div className="text-center mb-12">
                        <h1 className="text-4xl font-bold text-dark mb-4 flex items-center justify-center gap-3">
                            <span className="text-primary text-5xl">🎯</span>
                            智能辩论系统
                        </h1>
                        <p className="text-gray-600 text-lg mb-6">选择辩手，开始精彩的辩论</p>
                        <div className="bg-accent/20 border-2 border-accent rounded-2xl p-4 inline-block">
                            <p className="font-medium text-dark text-lg">辩题：{topic}</p>
                        </div>
                    </div>
                    
                    {isLoading ? (
                        <div className="text-center py-16">
                            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-primary mx-auto mb-6"></div>
                            <p className="text-gray-600 text-lg">加载辩手列表中...</p>
                        </div>
                    ) : (
                        <form onSubmit={handleSubmit} className="space-y-8">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {debaters.map((debater, index) => (
                                    <button
                                        key={index}
                                        type="button"
                                        onClick={() => toggleDebater(debater)}
                                        className={`flex items-center gap-4 p-6 rounded-2xl transition-all ${selectedDebaters.includes(debater) ? `bg-gradient-to-r ${roleColors[debater] || 'from-primary to-pink'} text-white shadow-glow-primary transform scale-105` : 'bg-gray-50 border-2 border-gray-200 hover:bg-gray-100'}`}
                                    >
                                        <div className="w-16 h-16 rounded-full flex items-center justify-center bg-white/30 text-2xl">
                                            {roleIcons[debater] || '👤'}
                                        </div>
                                        <div>
                                            <h3 className="font-medium text-xl">{debater}</h3>
                                            <p className="text-sm text-gray-500">点击选择</p>
                                        </div>
                                    </button>
                                ))}
                            </div>
                            
                            <div className="flex justify-between items-center">
                                <p className="text-sm text-gray-600">
                                    已选择 {selectedDebaters.length} 位辩手
                                </p>
                                <button
                                    type="submit"
                                    disabled={selectedDebaters.length < 2}
                                    className={`px-10 py-4 rounded-2xl font-medium text-lg transition-all ${selectedDebaters.length >= 2 ? 'bg-gradient-to-r from-primary to-pink text-white shadow-glow-primary hover:from-primary/90 hover:to-pink/90 transform hover:scale-105' : 'bg-gray-300 text-gray-500 cursor-not-allowed'}`}
                                >
                                    开始辩论
                                </button>
                            </div>
                        </form>
                    )}
                </div>
            </div>
        </div>
    )
}

export default DebaterSelection
