'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { StatsCards } from '@/components/dashboard/StatsCards'
import { ScoreChart } from '@/components/dashboard/ScoreChart'
import { JobsOverTimeChart } from '@/components/dashboard/JobsOverTimeChart'
import { TopLocations } from '@/components/dashboard/TopLocations'
import { TopCompanies } from '@/components/dashboard/TopCompanies'
import { Loader2 } from 'lucide-react'

export default function DashboardPage() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['stats'],
    queryFn: api.getStats,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-800">Error loading stats</h2>
          <p className="text-gray-600 mt-2">Make sure the backend is running on port 8000</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500">
          Last updated: {new Date().toLocaleString()}
        </p>
      </div>

      {/* Stats Cards */}
      <StatsCards stats={stats!} />

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ScoreChart distribution={stats!.scoreDistribution} />
        <JobsOverTimeChart data={stats!.jobsByDate} />
      </div>

      {/* Lists Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TopLocations locations={stats!.topLocations} />
        <TopCompanies companies={stats!.topCompanies} />
      </div>
    </div>
  )
}
