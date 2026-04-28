import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'

function DebaterSelection({ topic, onNext, onBack }) {
    const [debaters, setDebaters] = useState([])
    const [selectedDebaters, setSelectedDebaters] = useState([])
    const [recommendedIds, setRecommendedIds] = useState([])
    const [recommendationMeta, setRecommendationMeta] = useState({ source: '', reason: '', llmError: '' })
    const [recommendationItems, setRecommendationItems] = useState([])
    const [hasRequestedRecommendation, setHasRequestedRecommendation] = useState(false)
    const [activeScenario, setActiveScenario] = useState('')
    const [isLoading, setIsLoading] = useState(true)
    const recommendReqSeqRef = useRef(0)

    const inferScenarioById = (id) => {
        const itIds = new Set(['it_ops_manager', 'it_project_manager', 'platform_engineer', 'product_manager', 'qa_test_engineer', 'security_engineer', 'senior_engineer'])
        const businessIds = new Set(['investor', 'small_business_owner'])
        const careerIds = new Set(['phoenix_riser', 'zhangxuefeng', 'hr_evaluator'])
        const governanceIds = new Set(['lawyer_public_policy', 'civil_servant'])
        const societyIds = new Set(['doctor_public_health', 'journalist_observer', 'factory_worker', 'counselor'])
        if (itIds.has(id)) return 'it'
        if (businessIds.has(id)) return 'business'
        if (careerIds.has(id)) return 'career'
        if (governanceIds.has(id)) return 'governance'
        if (societyIds.has(id)) return 'society'
        return 'general'
    }

    const normalizeDebaters = (items) => {
        return (items || []).map((item) => ({
            ...item,
            scenario: item.scenario || inferScenarioById(item.id),
        }))
    }

    useEffect(() => {
        const fetchDebaters = async () => {
            try {
                const response = await axios.get('/api/debaters')
                const allDebaters = normalizeDebaters(response.data.debaters || [])
                setDebaters(allDebaters)
            } catch (error) {
                console.error('Error fetching debaters:', error)
                // 使用默认辩手列表作为备用
                const fallback = [
                    {id: 'phoenix_riser', name: '底层逆袭者 Phoenix Riser', role: '底层逆袭者 / Grassroots Riser', description: '从低谷逆袭并拿到腾讯与字节跳动等大厂 offer 的成长型辩手', scenario: 'career'},
                    {id: 'zhangxuefeng', name: '教育实用导师 Zhang Xuefeng', role: '教育选择专家/实用主义导师', description: '考研名师、高考志愿填报专家', scenario: 'career'},
                    {id: 'senior_engineer', name: '资深工程师 Senior Engineer', role: '大厂资深工程师/技术面试官', description: '逻辑严密、可落地、可验证，擅长技术可执行性评估', scenario: 'it'},
                    {id: 'investor', name: '早期投资人 Early Investor', role: '早期投资人/创业导师', description: '关注赛道、商业模式、规模化与竞争壁垒', scenario: 'business'}
                ]
                setDebaters(normalizeDebaters(fallback))
                setSelectedDebaters(fallback.slice(0, 2))
            } finally {
                setIsLoading(false)
            }
        }
        fetchDebaters()
    }, [topic])

    useEffect(() => {
        // 切场景时清空已选，避免“上一场景的自动选中”造成误导
        setSelectedDebaters([])
        setRecommendedIds([])
        setRecommendationItems([])
        setRecommendationMeta({ source: '', reason: '', llmError: '' })
        setHasRequestedRecommendation(false)
    }, [activeScenario])

    const toggleDebater = (debater) => {
        setSelectedDebaters(prev => {
            if (prev.some(d => d.id === debater.id)) {
                return prev.filter(d => d.id !== debater.id)
            } else {
                return [...prev, debater]
            }
        })
    }

    const handleSubmit = (e) => {
        e.preventDefault()
        if (!activeScenario) {
            alert('请先选择场景，再进行辩手推荐。')
            return
        }
        if (selectedDebaters.length >= 2) {
            const debaterIds = selectedDebaters.map(d => d.id)
            onNext(debaterIds)
        } else {
            alert('请先点击“使用智能推荐”，或手动至少选择2位同场景辩手。')
        }
    }

    const getScenarioDebaters = () => {
        return debaters.filter((d) => activeScenario ? (d.scenario || inferScenarioById(d.id)) === activeScenario : false)
    }

    const handleUseRecommended = async () => {
        if (!activeScenario) {
            alert('请先选择场景。')
            return
        }
        const reqSeq = ++recommendReqSeqRef.current
        setHasRequestedRecommendation(true)
        let ids = []
        try {
            const recommendResp = await axios.get('/api/debaters/recommend', { params: { topic, scenario: activeScenario } })
            if (reqSeq !== recommendReqSeqRef.current) return
            ids = recommendResp.data?.debater_ids || []
            setRecommendedIds(ids)
            setRecommendationItems(recommendResp.data?.recommendation_items || [])
            setRecommendationMeta({
                source: recommendResp.data?.selector_source || '',
                reason: recommendResp.data?.selector_reason || '',
                llmError: recommendResp.data?.llm_error || '',
            })
        } catch (e) {
            console.warn('Fetch recommendations failed:', e)
            if (reqSeq !== recommendReqSeqRef.current) return
            setRecommendedIds([])
            setRecommendationItems([])
            setRecommendationMeta({
                source: 'rule_fallback',
                reason: '推荐接口调用失败，请稍后重试。',
                llmError: '',
            })
            alert('智能推荐请求失败，请稍后重试或手动选择辩手。')
            return
        }
        let matched = debaters.filter((d) => {
            if (!ids.includes(d.id)) return false
            return (d.scenario || inferScenarioById(d.id)) === activeScenario
        })
        if (matched.length >= 2) {
            setSelectedDebaters(matched)
        } else {
            alert('当前场景推荐人数不足，请重试智能推荐或手动选择至少2位辩手。')
        }
    }

    // 角色图标映射
    const roleIcons = {
        'phoenix_riser': '🔥',
        'zhangxuefeng': '🎓',
        '程序员': '💻',
        '产品经理': '📱'
    }

    const scenarioTabs = [
        { id: 'it', label: 'IT 决策' },
        { id: 'business', label: '商业经营' },
        { id: 'career', label: '人才成长' },
        { id: 'governance', label: '治理合规' },
        { id: 'society', label: '社会公共' },
    ]
    const scenarioLabelMap = {
        it: 'IT 决策',
        business: '商业经营',
        career: '人才成长',
        governance: '治理合规',
        society: '社会公共',
        general: '通用',
    }
    const recommendationItemMap = Object.fromEntries((recommendationItems || []).map((x) => [x.id, x]))

    const visibleDebaters = debaters.filter((d) => activeScenario ? d.scenario === activeScenario : false)

    // 角色颜色映射
    const roleColors = {
        'phoenix_riser': 'from-primary to-pink',
        'zhangxuefeng': 'from-secondary to-blue',
        '程序员': 'from-purple to-blue',
        '产品经理': 'from-accent to-warning'
    }

    // 获取辩手的图标
    const getDebaterIcon = (debater) => {
        return roleIcons[debater.id] || roleIcons[debater.name] || '👤'
    }

    // 获取辩手的颜色
    const getDebaterColor = (debater) => {
        return roleColors[debater.id] || roleColors[debater.name] || 'from-primary to-pink'
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-light to-secondary/10 font-sans p-4">
            <div className="container mx-auto max-w-4xl">
                <div className="bg-white rounded-3xl shadow-cute p-10 animate-fade-in">
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
                            <div className="flex flex-wrap gap-2">
                                {scenarioTabs.map((tab) => (
                                    <button
                                        key={tab.id}
                                        type="button"
                                        onClick={() => setActiveScenario(tab.id)}
                                        className={`rounded-full px-3 py-1 text-sm transition ${activeScenario === tab.id ? 'bg-slate-800 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
                                    >
                                        {tab.label}
                                    </button>
                                ))}
                            </div>
                            {!activeScenario && (
                                <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                                    请先选择一个场景，系统会基于该场景调用大模型推荐辩手。
                                </div>
                            )}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {visibleDebaters.map((debater, index) => {
                                    const isSelected = selectedDebaters.some(d => d.id === debater.id)
                                    return (
                                        <button
                                            key={debater.id || index}
                                            type="button"
                                            onClick={() => toggleDebater(debater)}
                                            className={`flex items-center gap-4 p-6 rounded-2xl transition-all text-left ${isSelected ? `bg-gradient-to-r ${getDebaterColor(debater)} text-white shadow-glow-primary transform scale-105` : 'bg-gray-50 border-2 border-gray-200 hover:bg-gray-100'}`}
                                        >
                                            <div className="w-16 h-16 rounded-full flex items-center justify-center bg-white/30 text-2xl">
                                                {getDebaterIcon(debater)}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <h3 className="font-medium text-xl">{debater.name}</h3>
                                                {recommendedIds.includes(debater.id) && (
                                                    <span className={`inline-block mt-1 rounded-full px-2 py-0.5 text-xs ${isSelected ? 'bg-white/20 text-white' : 'bg-emerald-100 text-emerald-700'}`}>
                                                        智能推荐
                                                    </span>
                                                )}
                                                {recommendedIds.includes(debater.id) && (
                                                    <span className={`inline-block mt-1 ml-2 rounded-full px-2 py-0.5 text-xs ${isSelected ? 'bg-white/20 text-white' : 'bg-indigo-100 text-indigo-700'}`}>
                                                        来源：{recommendationItemMap[debater.id]?.source === 'llm' ? 'LLM推荐' : '默认规则补充'}
                                                    </span>
                                                )}
                                                {debater.scenario && (
                                                    <span className={`inline-block mt-1 ml-2 rounded-full px-2 py-0.5 text-xs ${isSelected ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-700'}`}>
                                                        场景：{scenarioLabelMap[debater.scenario] || debater.scenario}
                                                    </span>
                                                )}
                                                <p className={`text-sm font-medium ${isSelected ? 'text-white/90' : 'text-gray-600'}`}>{debater.role}</p>
                                                <p className={`text-sm mt-1 line-clamp-2 ${isSelected ? 'text-white/80' : 'text-gray-500'}`}>{debater.description}</p>
                                                {recommendedIds.includes(debater.id) && recommendationItemMap[debater.id]?.source === 'llm' && recommendationItemMap[debater.id]?.reason && (
                                                    <p className={`text-xs mt-1 ${isSelected ? 'text-white/80' : 'text-indigo-700'}`}>
                                                        选择理由：{recommendationItemMap[debater.id]?.reason}
                                                    </p>
                                                )}
                                            </div>
                                        </button>
                                    )
                                })}
                            </div>
                            <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
                                <div className="mb-1 text-xs">
                                    推荐来源：{
                                        !hasRequestedRecommendation
                                            ? '未触发（点击“智能推荐”后才会调用）'
                                            : (recommendationMeta.source === 'llm' ? 'LLM 推荐' : '规则兜底')
                                    }
                                    {hasRequestedRecommendation && recommendationMeta.reason ? `（${recommendationMeta.reason}）` : ''}
                                </div>
                                {hasRequestedRecommendation && recommendationMeta.source !== 'llm' && recommendationMeta.llmError ? (
                                    <div className="mb-1 text-xs text-amber-700">
                                        LLM失败原因：{recommendationMeta.llmError}
                                    </div>
                                ) : null}
                                {activeScenario && hasRequestedRecommendation && recommendedIds.length > 0 ? (
                                    <span>
                                    本场景智能推荐：{
                                        debaters
                                            .filter((d) => recommendedIds.includes(d.id))
                                            .filter((d) => (d.scenario || inferScenarioById(d.id)) === activeScenario)
                                            .map((d) => d.name)
                                            .join('、') || '暂无'
                                    }
                                    </span>
                                ) : (
                                    <span>
                                        {activeScenario
                                            ? (hasRequestedRecommendation ? '本场景智能推荐：暂无（可点击“智能推荐”重试）' : '本场景智能推荐：尚未触发（请点击“智能推荐”）')
                                            : '本场景智能推荐：请先选择场景'}
                                    </span>
                                )}
                            </div>
                            <div className="text-xs text-gray-500">
                                说明：系统仅提供推荐，不会自动替你改选；请点“使用智能推荐”应用本场景建议。
                            </div>
                            {activeScenario && visibleDebaters.length === 0 && (
                                <div className="rounded-2xl border border-dashed border-gray-300 bg-gray-50 p-6 text-center text-sm text-gray-600">
                                    当前场景暂无可见辩手，可能是接口瞬时失败。请刷新页面后重试。
                                </div>
                            )}
                            
                            <div className="flex justify-between items-center">
                                <p className="text-sm text-gray-600">
                                    已选择 {selectedDebaters.length} 位辩手
                                </p>
                                <div className="flex items-center gap-3">
                                    <button
                                        type="button"
                                        onClick={handleUseRecommended}
                                        disabled={!debaters.length || !activeScenario}
                                        className={`px-5 py-3 rounded-xl font-medium text-sm transition-all ${debaters.length && activeScenario ? 'bg-emerald-500 text-white hover:bg-emerald-600' : 'bg-gray-200 text-gray-400 cursor-not-allowed'}`}
                                    >
                                        {hasRequestedRecommendation ? '重试智能推荐' : '智能推荐'}
                                    </button>
                                    <button
                                        type="submit"
                                        disabled={selectedDebaters.length < 2}
                                        className={`px-10 py-4 rounded-2xl font-medium text-lg transition-all ${selectedDebaters.length >= 2 ? 'bg-gradient-to-r from-primary to-pink text-white shadow-glow-primary hover:from-primary/90 hover:to-pink/90 transform hover:scale-105' : 'bg-gray-300 text-gray-500 cursor-not-allowed'}`}
                                    >
                                        开始辩论
                                    </button>
                                </div>
                            </div>
                        </form>
                    )}
                </div>
            </div>
        </div>
    )
}

export default DebaterSelection
