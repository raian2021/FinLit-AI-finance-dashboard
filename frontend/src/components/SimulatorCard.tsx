'use client'

import { useState } from 'react'
import { api, SimulationResult } from '@/lib/api'

function formatGBP(n: number): string {
  return `£${Math.abs(n).toLocaleString('en-GB', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
}

export default function SimulatorCard() {
  const [amount, setAmount] = useState(100)
  const [years, setYears] = useState(10)
  const [returnRate, setReturnRate] = useState(7)
  const [result, setResult] = useState<SimulationResult | null>(null)
  const [loading, setLoading] = useState(false)

  const runSimulation = async () => {
    setLoading(true)
    try {
      const res = await api.simulate({
        monthly_amount: amount,
        annual_return: returnRate / 100,
        years,
      })
      setResult(res)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h2 className="text-lg font-semibold mb-1">What-If Simulator</h2>
      <p className="text-sm text-gray-500 mb-5">
        See what redirecting spending could grow to over time
      </p>

      <div className="space-y-4">
        {/* Monthly Amount */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Monthly amount: {formatGBP(amount)}
          </label>
          <input
            type="range"
            min={10} max={500} step={10}
            value={amount}
            onChange={(e) => setAmount(Number(e.target.value))}
            className="w-full accent-brand-600"
          />
          <div className="flex justify-between text-xs text-gray-400">
            <span>£10</span><span>£500</span>
          </div>
        </div>

        {/* Years */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Time horizon: {years} years
          </label>
          <input
            type="range"
            min={1} max={30} step={1}
            value={years}
            onChange={(e) => setYears(Number(e.target.value))}
            className="w-full accent-brand-600"
          />
          <div className="flex justify-between text-xs text-gray-400">
            <span>1yr</span><span>30yrs</span>
          </div>
        </div>

        {/* Return rate */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Assumed annual return: {returnRate}%
          </label>
          <input
            type="range"
            min={1} max={15} step={0.5}
            value={returnRate}
            onChange={(e) => setReturnRate(Number(e.target.value))}
            className="w-full accent-brand-600"
          />
          <div className="flex justify-between text-xs text-gray-400">
            <span>1%</span><span>15%</span>
          </div>
        </div>

        <button
          onClick={runSimulation}
          disabled={loading}
          className="w-full bg-brand-600 text-white py-2.5 rounded-lg font-medium hover:bg-brand-700 transition-colors disabled:opacity-50"
        >
          {loading ? 'Calculating...' : 'Run Simulation'}
        </button>
      </div>

      {/* Results */}
      {result && (
        <div className="mt-6 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-brand-50 rounded-lg p-4 text-center">
              <p className="text-xs text-brand-600 font-medium">You'd Contribute</p>
              <p className="text-xl font-bold text-brand-800">
                {formatGBP(Number(result.total_contributed))}
              </p>
            </div>
            <div className="bg-green-50 rounded-lg p-4 text-center">
              <p className="text-xs text-green-600 font-medium">Could Grow To</p>
              <p className="text-xl font-bold text-green-800">
                {formatGBP(Number(result.final_nominal))}
              </p>
            </div>
          </div>

          <div className="bg-amber-50 rounded-lg p-3 text-center">
            <p className="text-xs text-amber-600 font-medium">Growth (in today's money)</p>
            <p className="text-lg font-bold text-amber-800">
              {formatGBP(Number(result.final_real))}
            </p>
          </div>

          {/* Milestone table */}
          <div className="text-sm">
            <div className="grid grid-cols-4 gap-2 text-xs font-medium text-gray-500 mb-1 px-1">
              <span>Year</span><span className="text-right">Put In</span>
              <span className="text-right">Value</span><span className="text-right">Growth</span>
            </div>
            {result.projections
              .filter((p) => p.year % (years <= 10 ? 1 : 5) === 0 || p.year === 1)
              .map((p) => (
                <div key={p.year} className="grid grid-cols-4 gap-2 text-xs py-1.5 px-1 border-t border-gray-50">
                  <span className="font-medium">{p.year}</span>
                  <span className="text-right text-gray-600">{formatGBP(Number(p.total_contributed))}</span>
                  <span className="text-right font-medium">{formatGBP(Number(p.nominal_value))}</span>
                  <span className="text-right text-green-600">+{formatGBP(Number(p.growth))}</span>
                </div>
              ))}
          </div>

          <p className="text-xs text-gray-400 italic">{result.disclaimer}</p>
        </div>
      )}
    </div>
  )
}
