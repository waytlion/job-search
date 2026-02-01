'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Job, JobDetail } from '@/lib/types'
import { X, ExternalLink, Building2, MapPin, Calendar, DollarSign, Heart, Star, Tag, Clock, Loader2 } from 'lucide-react'
import { useState, useEffect } from 'react'
import clsx from 'clsx'

interface JobModalProps {
  job: Job
  onClose: () => void
  onUpdate: () => void
}

const statusOptions = [
  { value: 'not_viewed', label: 'Not Viewed', color: 'bg-gray-100 text-gray-700 border-gray-200' },
  { value: 'interested', label: 'Interested', color: 'bg-blue-100 text-blue-700 border-blue-200' },
  { value: 'applied', label: 'Applied', color: 'bg-green-100 text-green-700 border-green-200' },
  { value: 'not_interested', label: 'Not Interested', color: 'bg-orange-100 text-orange-700 border-orange-200' },
  { value: 'archived', label: 'Archived', color: 'bg-slate-100 text-slate-700 border-slate-200' },
]

function getScoreColor(score: number): string {
  if (score >= 8) return 'text-green-600 bg-green-50 border-green-200'
  if (score >= 6) return 'text-blue-600 bg-blue-50 border-blue-200'
  if (score >= 4) return 'text-yellow-600 bg-yellow-50 border-yellow-200'
  return 'text-red-600 bg-red-50 border-red-200'
}

export function JobModal({ job, onClose, onUpdate }: JobModalProps) {
  const queryClient = useQueryClient()
  const [notes, setNotes] = useState('')
  const [status, setStatus] = useState(job.user_status || 'not_viewed')

  const { data: jobDetail, isLoading } = useQuery({
    queryKey: ['job', job.id],
    queryFn: () => api.getJob(job.id),
  })

  useEffect(() => {
    if (jobDetail) {
      setNotes(jobDetail.user_notes || '')
      setStatus(jobDetail.user_status || 'not_viewed')
    }
  }, [jobDetail])

  const updateMutation = useMutation({
    mutationFn: (data: { user_status?: string; user_notes?: string }) =>
      api.updateJob(job.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job', job.id] })
      onUpdate()
    },
  })

  const handleStatusChange = (newStatus: string) => {
    setStatus(newStatus)
    updateMutation.mutate({ user_status: newStatus })
  }

  const handleNotesBlur = () => {
    if (notes !== (jobDetail?.user_notes || '')) {
      updateMutation.mutate({ user_notes: notes })
    }
  }

  // Close on escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [onClose])

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative min-h-screen flex items-center justify-center p-4">
        <div className="relative bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
          {/* Header */}
          <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-start justify-between">
            <div className="flex-1 min-w-0 pr-4">
              <h2 className="text-xl font-bold text-gray-900 truncate">{job.title}</h2>
              <div className="flex items-center gap-4 mt-1 text-sm text-gray-600">
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
                <span className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                  {job.platform}
                </span>
              </div>
            </div>
            
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
              </div>
            ) : jobDetail ? (
              <div className="space-y-6">
                {/* Score Cards */}
                <div className="grid grid-cols-4 gap-4">
                  <div className={clsx('p-4 rounded-lg border text-center', getScoreColor(jobDetail.total_score))}>
                    <Star className="w-5 h-5 mx-auto mb-1" />
                    <div className="text-2xl font-bold">{jobDetail.total_score.toFixed(1)}</div>
                    <div className="text-xs opacity-75">Total Score</div>
                  </div>
                  <div className="p-4 rounded-lg border bg-green-50 border-green-200 text-green-700 text-center">
                    <DollarSign className="w-5 h-5 mx-auto mb-1" />
                    <div className="text-2xl font-bold">{jobDetail.money_score.toFixed(1)}</div>
                    <div className="text-xs opacity-75">Money</div>
                  </div>
                  <div className="p-4 rounded-lg border bg-red-50 border-red-200 text-red-700 text-center">
                    <Heart className="w-5 h-5 mx-auto mb-1" />
                    <div className="text-2xl font-bold">{jobDetail.passion_score.toFixed(1)}</div>
                    <div className="text-xs opacity-75">Passion</div>
                  </div>
                  <div className="p-4 rounded-lg border bg-blue-50 border-blue-200 text-blue-700 text-center">
                    <MapPin className="w-5 h-5 mx-auto mb-1" />
                    <div className="text-2xl font-bold">{jobDetail.location_score.toFixed(1)}</div>
                    <div className="text-xs opacity-75">Location</div>
                  </div>
                </div>

                {/* Status and Actions */}
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                    <div className="flex flex-wrap gap-2">
                      {statusOptions.map(opt => (
                        <button
                          key={opt.value}
                          onClick={() => handleStatusChange(opt.value)}
                          className={clsx(
                            'px-3 py-1.5 rounded-lg text-sm font-medium border transition-all',
                            status === opt.value
                              ? opt.color + ' ring-2 ring-offset-1 ring-current'
                              : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'
                          )}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </div>
                  
                  <a
                    href={jobDetail.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                  >
                    <ExternalLink className="w-4 h-4" />
                    View Original
                  </a>
                </div>

                {/* Details */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                  {jobDetail.salary_text && (
                    <div>
                      <span className="text-gray-500">Salary:</span>
                      <span className="ml-2 text-gray-900">{jobDetail.salary_text}</span>
                    </div>
                  )}
                  {jobDetail.posted_date && (
                    <div>
                      <span className="text-gray-500">Posted:</span>
                      <span className="ml-2 text-gray-900">{jobDetail.posted_date}</span>
                    </div>
                  )}
                  {jobDetail.scraped_at && (
                    <div>
                      <span className="text-gray-500">Scraped:</span>
                      <span className="ml-2 text-gray-900">
                        {new Date(jobDetail.scraped_at).toLocaleDateString()}
                      </span>
                    </div>
                  )}
                  {jobDetail.years_experience_required !== null && (
                    <div>
                      <span className="text-gray-500">Experience Required:</span>
                      <span className="ml-2 text-gray-900">
                        {jobDetail.years_experience_required} years
                      </span>
                    </div>
                  )}
                </div>

                {/* Tags */}
                {jobDetail.tags && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Tags</label>
                    <div className="flex flex-wrap gap-2">
                      {jobDetail.tags.split(',').map((tag, i) => (
                        <span
                          key={i}
                          className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
                        >
                          {tag.trim()}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Description */}
                {jobDetail.description && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                    <div className="prose prose-sm max-w-none bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
                      <pre className="whitespace-pre-wrap font-sans text-gray-700">
                        {jobDetail.description}
                      </pre>
                    </div>
                  </div>
                )}

                {/* Requirements */}
                {jobDetail.requirements && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Requirements</label>
                    <div className="prose prose-sm max-w-none bg-gray-50 rounded-lg p-4 max-h-48 overflow-y-auto">
                      <pre className="whitespace-pre-wrap font-sans text-gray-700">
                        {jobDetail.requirements}
                      </pre>
                    </div>
                  </div>
                )}

                {/* Notes */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Your Notes</label>
                  <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    onBlur={handleNotesBlur}
                    placeholder="Add your notes about this job..."
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-y min-h-[100px]"
                  />
                  {updateMutation.isPending && (
                    <p className="text-xs text-gray-500 mt-1">Saving...</p>
                  )}
                </div>

                {/* Filter status */}
                {jobDetail.filtered_out && (
                  <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
                    <div className="flex items-center gap-2 text-orange-700">
                      <Clock className="w-4 h-4" />
                      <span className="font-medium">Filtered Out</span>
                    </div>
                    {jobDetail.filter_reason && (
                      <p className="text-sm text-orange-600 mt-1">{jobDetail.filter_reason}</p>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                Failed to load job details
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
