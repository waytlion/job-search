'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { JobList } from '@/components/jobs/JobList'
import { JobFilters } from '@/components/jobs/JobFilters'
import { JobModal } from '@/components/jobs/JobModal'
import { useState } from 'react'
import { Loader2 } from 'lucide-react'
import { Job, JobFilters as JobFiltersType } from '@/lib/types'

export default function JobsPage() {
  const [page, setPage] = useState(1)
  const [selectedJob, setSelectedJob] = useState<Job | null>(null)
  const [filters, setFilters] = useState<JobFiltersType>({
    sort: 'total_score',
    order: 'desc',
    hideFiltered: true,
  })

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['jobs', page, filters],
    queryFn: () => api.getJobs({ page, limit: 20, ...filters }),
  })

  const { data: filterOptions } = useQuery({
    queryKey: ['filterOptions'],
    queryFn: api.getFilterOptions,
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
          <h2 className="text-xl font-semibold text-gray-800">Error loading jobs</h2>
          <p className="text-gray-600 mt-2">Make sure the backend is running on port 8000</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Jobs</h1>
        <p className="text-sm text-gray-500">
          {data?.total.toLocaleString()} jobs found
        </p>
      </div>

      <JobFilters 
        filters={filters} 
        onChange={setFilters}
        options={filterOptions}
      />

      <JobList
        jobs={data?.jobs || []}
        total={data?.total || 0}
        page={page}
        totalPages={data?.totalPages || 1}
        onPageChange={setPage}
        onJobClick={setSelectedJob}
        onStatusChange={() => refetch()}
      />

      {selectedJob && (
        <JobModal
          job={selectedJob}
          onClose={() => setSelectedJob(null)}
          onUpdate={() => {
            refetch()
          }}
        />
      )}
    </div>
  )
}
