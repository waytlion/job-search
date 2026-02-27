'use client'

import { Job } from '@/lib/types'
import { JobCard } from './JobCard'
import { ChevronLeft, ChevronRight } from 'lucide-react'

interface JobListProps {
  jobs: Job[]
  total: number
  page: number
  totalPages: number
  onPageChange: (page: number) => void
  onJobClick: (job: Job) => void
  onStatusChange: () => void
}

export function JobList({ jobs, total, page, totalPages, onPageChange, onJobClick, onStatusChange }: JobListProps) {
  return (
    <div>
      {/* Job cards */}
      <div className="space-y-3 mb-6">
        {jobs.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg">
            <p className="text-gray-500">No jobs match your filters</p>
          </div>
        ) : (
          jobs.map((job, index) => (
            <JobCard
              key={job.id}
              job={job}
              rank={(page - 1) * 20 + index + 1}
              onClick={() => onJobClick(job)}
              onStatusChange={onStatusChange}
            />
          ))
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between bg-white rounded-lg shadow px-4 py-3">
          <div className="text-sm text-gray-600">
            Page {page} of {totalPages} ({total.toLocaleString()} total jobs)
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>

            {/* Page numbers */}
            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNum: number
                if (totalPages <= 5) {
                  pageNum = i + 1
                } else if (page <= 3) {
                  pageNum = i + 1
                } else if (page >= totalPages - 2) {
                  pageNum = totalPages - 4 + i
                } else {
                  pageNum = page - 2 + i
                }

                return (
                  <button
                    key={pageNum}
                    onClick={() => onPageChange(pageNum)}
                    className={`w-8 h-8 rounded-lg text-sm font-medium ${pageNum === page
                        ? 'bg-primary-600 text-white'
                        : 'hover:bg-gray-100 text-gray-700'
                      }`}
                  >
                    {pageNum}
                  </button>
                )
              })}
            </div>

            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
