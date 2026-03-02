'use client'

import { CashFlowTruth } from '@/lib/api'

interface CashFlowCardProps {
  data: CashFlowTruth
}

function formatGBP(n: number): string {
  return `£${Math.abs(n).toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function BarSegment({ label, amount, pct, color }: {
  label: string; amount: number; pct: number; color: string
}) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-gray-600">{label}</span>
        <span className="font-medium">{formatGBP(amount)} ({pct.toFixed(1)}%)</span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-3">
        <div
          className={`${color} h-3 rounded-full transition-all duration-500`}
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
    </div>
  )
}

export default function CashFlowCard({ data }: CashFlowCardProps) {
  const surplus = Number(data.income) - Number(data.essential_spend) - Number(data.discretionary_spend) - Number(data.savings_outflows)

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h2 className="text-lg font-semibold mb-1">Where Your Money Goes</h2>
      <p className="text-sm text-gray-500 mb-6">
        {data.period_start} to {data.period_end}
      </p>

      {/* Income header */}
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-gray-100">
        <span className="text-gray-600">Total Income</span>
        <span className="text-2xl font-bold text-green-600">{formatGBP(Number(data.income))}</span>
      </div>

      {/* Spending bars */}
      <div className="space-y-4 mb-6">
        <BarSegment
          label="🏠 Essentials"
          amount={Number(data.essential_spend)}
          pct={data.essential_pct}
          color="bg-blue-500"
        />
        <BarSegment
          label="🎯 Discretionary"
          amount={Number(data.discretionary_spend)}
          pct={data.discretionary_pct}
          color="bg-amber-500"
        />
        <BarSegment
          label="💰 Savings & Investments"
          amount={Number(data.savings_outflows)}
          pct={data.savings_pct}
          color="bg-green-500"
        />
      </div>

      {/* Surplus / deficit */}
      <div className={`p-4 rounded-lg ${surplus >= 0 ? 'bg-green-50' : 'bg-red-50'}`}>
        <div className="flex justify-between items-center">
          <span className="text-sm font-medium">
            {surplus >= 0 ? '✅ Monthly Surplus' : '⚠️ Monthly Deficit'}
          </span>
          <span className={`text-lg font-bold ${surplus >= 0 ? 'text-green-700' : 'text-red-700'}`}>
            {formatGBP(surplus)}
          </span>
        </div>
        {surplus > 0 && (
          <p className="text-xs text-green-600 mt-1">
            This is money that could be working for you — check the simulator below
          </p>
        )}
      </div>

      {/* Top discretionary */}
      {data.top_discretionary.length > 0 && (
        <div className="mt-6">
          <h3 className="text-sm font-medium text-gray-500 mb-3">Top Discretionary Spending</h3>
          <div className="space-y-2">
            {data.top_discretionary.map((cat) => (
              <div key={cat.category} className="flex justify-between text-sm">
                <span className="text-gray-600 capitalize">
                  {cat.category.replace(/_/g, ' ')}
                </span>
                <span className="font-medium">
                  {formatGBP(Number(cat.total))} · {cat.transaction_count} txns
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
