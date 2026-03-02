'use client'

import { useEffect, useState } from 'react'
import { api, QuickStats, CashFlowTruth } from '@/lib/api'

import { AppShell } from '@/components/AppShell'
import UploadCard from '@/components/UploadCard'
import CashFlowCard from '@/components/CashFlowCard'
import SimulatorCard from '@/components/SimulatorCard'
import InsightCard from '@/components/InsightCard'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

export default function Dashboard() {
  const [stats, setStats] = useState<QuickStats | null>(null)
  const [cashflow, setCashflow] = useState<CashFlowTruth | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadData = async () => {
    setLoading(true)
    setError(null)

    try {
      const s = await api.stats()
      setStats(s)

      if (s.total_transactions > 0) {
        const cf = await api.cashflow(3)
        setCashflow(cf)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const hasData = stats && stats.total_transactions > 0

  return (
    <AppShell>
      <div className="space-y-8">

        {/* Header Stats */}
        {loading && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Skeleton className="h-28 rounded-xl" />
            <Skeleton className="h-28 rounded-xl" />
            <Skeleton className="h-28 rounded-xl" />
          </div>
        )}

        {!loading && stats && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Total Transactions
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">
                  {stats.total_transactions.toLocaleString()}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Data From
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-lg font-semibold">
                  {stats.earliest_date || '—'}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Data To
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-lg font-semibold">
                  {stats.latest_date || '—'}
                </p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Error State */}
        {error && (
          <Card className="border-red-500">
            <CardContent className="p-4 text-red-600">
              {error}
            </CardContent>
          </Card>
        )}

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          <UploadCard onUploadComplete={loadData} />

          {hasData && cashflow && (
            <CashFlowCard data={cashflow} />
          )}

          {hasData && (
            <SimulatorCard />
          )}

          {hasData && (
            <InsightCard />
          )}

        </div>

      </div>
    </AppShell>
  )
}
