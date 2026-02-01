'use client'

import { JobFilters as JobFiltersType, FilterOptions } from '@/lib/types'
import { Search, Filter, SortAsc, SortDesc, X } from 'lucide-react'
import { useState } from 'react'

interface JobFiltersProps {
  filters: JobFiltersType
  onChange: (filters: JobFiltersType) => void
  options?: FilterOptions
}

const sortOptions = [
  { value: 'total_score', label: 'Total Score' },
  { value: 'money_score', label: 'Money Score' },
  { value: 'passion_score', label: 'Passion Score' },
  { value: 'location_score', label: 'Location Score' },
  { value: 'scraped_at', label: 'Date Added' },
  { value: 'title', label: 'Title' },
  { value: 'company', label: 'Company' },
]

export function JobFilters({ filters, onChange, options }: JobFiltersProps) {
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [searchInput, setSearchInput] = useState(filters.search || '')

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onChange({ ...filters, search: searchInput || undefined })
  }

  const clearFilters = () => {
    setSearchInput('')
    onChange({
      sort: 'total_score',
      order: 'desc',
      hideFiltered: true,
    })
  }

  const hasActiveFilters = filters.search || filters.minScore || filters.maxScore || 
    filters.locations || filters.companies || filters.platforms || filters.status

  return (
    <div className="bg-white rounded-lg shadow p-4 mb-4 space-y-4">
      {/* Search and Sort Row */}
      <div className="flex items-center gap-4">
        {/* Search */}
        <form onSubmit={handleSearchSubmit} className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search jobs by title, company, or description..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </form>

        {/* Sort */}
        <div className="flex items-center gap-2">
          <select
            value={filters.sort || 'total_score'}
            onChange={(e) => onChange({ ...filters, sort: e.target.value })}
            className="px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {sortOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>

          <button
            onClick={() => onChange({ ...filters, order: filters.order === 'asc' ? 'desc' : 'asc' })}
            className="p-2 border border-gray-200 rounded-lg hover:bg-gray-50"
            title={filters.order === 'asc' ? 'Ascending' : 'Descending'}
          >
            {filters.order === 'asc' ? (
              <SortAsc className="w-5 h-5 text-gray-600" />
            ) : (
              <SortDesc className="w-5 h-5 text-gray-600" />
            )}
          </button>
        </div>

        {/* Advanced toggle */}
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${
            showAdvanced || hasActiveFilters ? 'bg-primary-50 border-primary-200 text-primary-700' : 'border-gray-200 text-gray-600 hover:bg-gray-50'
          }`}
        >
          <Filter className="w-4 h-4" />
          Filters
          {hasActiveFilters && (
            <span className="w-2 h-2 bg-primary-500 rounded-full" />
          )}
        </button>

        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="flex items-center gap-1 px-3 py-2 text-gray-600 hover:text-gray-800"
          >
            <X className="w-4 h-4" />
            Clear
          </button>
        )}
      </div>

      {/* Advanced Filters */}
      {showAdvanced && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-gray-200">
          {/* Score Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Min Score</label>
            <input
              type="number"
              min="0"
              max="10"
              step="0.5"
              value={filters.minScore || ''}
              onChange={(e) => onChange({ ...filters, minScore: e.target.value ? parseFloat(e.target.value) : undefined })}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg"
              placeholder="0"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Max Score</label>
            <input
              type="number"
              min="0"
              max="10"
              step="0.5"
              value={filters.maxScore || ''}
              onChange={(e) => onChange({ ...filters, maxScore: e.target.value ? parseFloat(e.target.value) : undefined })}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg"
              placeholder="10"
            />
          </div>

          {/* Platform */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Platform</label>
            <select
              value={filters.platforms || ''}
              onChange={(e) => onChange({ ...filters, platforms: e.target.value || undefined })}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg"
            >
              <option value="">All Platforms</option>
              {options?.platforms.map(platform => (
                <option key={platform} value={platform}>{platform}</option>
              ))}
            </select>
          </div>

          {/* Status */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              value={filters.status || ''}
              onChange={(e) => onChange({ ...filters, status: e.target.value || undefined })}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg"
            >
              <option value="">All Statuses</option>
              {options?.statuses.map(status => (
                <option key={status} value={status}>
                  {status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </option>
              ))}
            </select>
          </div>

          {/* Hide Filtered Toggle */}
          <div className="col-span-2 md:col-span-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={filters.hideFiltered !== false}
                onChange={(e) => onChange({ ...filters, hideFiltered: e.target.checked })}
                className="w-4 h-4 text-primary-600 rounded border-gray-300 focus:ring-primary-500"
              />
              <span className="text-sm text-gray-700">Hide filtered/rejected jobs</span>
            </label>
          </div>
        </div>
      )}
    </div>
  )
}
