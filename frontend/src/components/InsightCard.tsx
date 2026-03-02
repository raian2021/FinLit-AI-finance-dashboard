'use client'

import { useState } from 'react'
import { api, InsightResponse } from '@/lib/api'

export default function InsightCard() {
  const [insight, setInsight] = useState<InsightResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const generateInsight = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.insights(3)
      setInsight(res)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h2 className="text-lg font-semibold mb-1">AI Financial Education</h2>
      <p className="text-sm text-gray-500 mb-5">
        Get a personalised educational snapshot of your finances
      </p>

      <button
        onClick={generateInsight}
        disabled={loading}
        className="w-full bg-gradient-to-r from-purple-600 to-brand-600 text-white py-2.5 rounded-lg font-medium hover:from-purple-700 hover:to-brand-700 transition-all disabled:opacity-50"
      >
        {loading ? (
          <span className="animate-pulse">Generating insight...</span>
        ) : (
          '✨ Generate Insight'
        )}
      </button>

      {error && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {insight && (
        <div className="mt-5 space-y-4">
          <div className="prose prose-sm max-w-none">
            {insight.insight.split('\n').map((paragraph, i) => (
              paragraph.trim() && (
                <p key={i} className="text-gray-700 text-sm leading-relaxed mb-2">
                  {paragraph}
                </p>
              )
            ))}
          </div>

          <div className="flex items-center gap-2 pt-2 border-t border-gray-100">
            <span className="text-xs text-gray-400">
              {insight.model_used} · {new Date(insight.generated_at).toLocaleString('en-GB')}
            </span>
          </div>

          <p className="text-xs text-gray-400 italic bg-gray-50 rounded-lg p-3">
            {insight.disclaimer}
          </p>
        </div>
      )}

      {!insight && !loading && (
        <div className="mt-5 text-center text-sm text-gray-400 py-8">
          <p>Click above to get an AI-powered educational overview</p>
          <p className="text-xs mt-1">Only aggregated data is sent — never raw transactions</p>
        </div>
      )}
    </div>
  )
}
