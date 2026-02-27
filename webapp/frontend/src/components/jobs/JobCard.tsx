'use client'

import { Job } from '@/lib/types'
import { api } from '@/lib/api'
import { MapPin, Building2, ExternalLink, DollarSign, Heart, Star } from 'lucide-react'
import clsx from 'clsx'

interface JobCardProps {
  job: Job
  rank?: number
  onClick: () => void
  onStatusChange: () => void
}

function getRankStyle(rank: number): string {
  if (rank === 1) return 'bg-yellow-400 text-yellow-900'   // Gold
  if (rank === 2) return 'bg-gray-300 text-gray-800'       // Silver
  if (rank === 3) return 'bg-amber-600 text-amber-50'      // Bronze
  if (rank <= 10) return 'bg-primary-100 text-primary-700'
  return 'bg-gray-100 text-gray-600'
}

const statusOptions = [
  { value: 'not_viewed', label: 'Not Viewed', color: 'bg-gray-100 text-gray-700' },
  { value: 'interested', label: 'Interested', color: 'bg-blue-100 text-blue-700' },
  { value: 'applied', label: 'Applied', color: 'bg-green-100 text-green-700' },
  { value: 'not_interested', label: 'Not Interested', color: 'bg-orange-100 text-orange-700' },
  { value: 'archived', label: 'Archived', color: 'bg-slate-100 text-slate-700' },
]

function getScoreColor(score: number): string {
  if (score >= 8) return 'text-green-600 bg-green-50'
  if (score >= 6) return 'text-blue-600 bg-blue-50'
  if (score >= 4) return 'text-yellow-600 bg-yellow-50'
  return 'text-red-600 bg-red-50'
}

export function JobCard({ job, rank, onClick, onStatusChange }: JobCardProps) {
  const handleStatusChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    e.stopPropagation()
    const newStatus = e.target.value
    try {
      await api.updateJobStatus(job.id, newStatus)
      onStatusChange()
    } catch (error) {
      console.error('Failed to update status:', error)
    }
  }

  const currentStatus = statusOptions.find(s => s.value === job.user_status) || statusOptions[0]

  return (
    <div
      className="job-card bg-white rounded-lg shadow p-4 cursor-pointer border border-transparent hover:border-primary-200"
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-4">
        {/* Rank badge */}
        {rank != null && (
          <div className={clsx(
            'flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center font-bold text-sm',
            getRankStyle(rank)
          )}>
            #{rank}
          </div>
        )}
        {/* Left side - Job info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-gray-900 truncate">{job.title}</h3>
            <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
              {job.platform}
            </span>
          </div>
          
          <div className="flex items-center gap-4 text-sm text-gray-600 mb-2">
            <span className="flex items-center gap-1">
              <Building2 className="w-4 h-4" />
              {job.company}
            </span>
            {job.location && (
              <span className="flex items-center gap-1">
                <MapPin className="w-4 h-4" />
                {job.location}
              </span>
            )}
            {job.salary_text && (
              <span className="flex items-center gap-1 text-green-600">
                <DollarSign className="w-4 h-4" />
                {job.salary_text}
              </span>
            )}
          </div>

          {/* Score breakdown */}
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1" title="Money Score">
              <DollarSign className="w-3 h-3 text-green-500" />
              {job.money_score.toFixed(1)}
            </span>
            <span className="flex items-center gap-1" title="Passion Score">
              <Heart className="w-3 h-3 text-red-500" />
              {job.passion_score.toFixed(1)}
            </span>
            <span className="flex items-center gap-1" title="Location Score">
              <MapPin className="w-3 h-3 text-blue-500" />
              {job.location_score.toFixed(1)}
            </span>
          </div>
        </div>

        {/* Right side - Score and actions */}
        <div className="flex flex-col items-end gap-2">
          {/* Total Score */}
          <div className={clsx(
            'flex items-center gap-1 px-3 py-1 rounded-full font-bold text-lg',
            getScoreColor(job.total_score)
          )}>
            <Star className="w-4 h-4" />
            {job.total_score.toFixed(1)}
          </div>

          {/* Status dropdown */}
          <select
            value={job.user_status || 'not_viewed'}
            onChange={handleStatusChange}
            onClick={(e) => e.stopPropagation()}
            className={clsx(
              'text-xs px-2 py-1 rounded border-none cursor-pointer',
              currentStatus.color
            )}
          >
            {statusOptions.map(status => (
              <option key={status.value} value={status.value}>
                {status.label}
              </option>
            ))}
          </select>

          {/* External link */}
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="text-gray-400 hover:text-primary-600"
            title="Open job posting"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </div>
    </div>
  )
}
