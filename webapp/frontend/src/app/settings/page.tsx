'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useState } from 'react'
import { Loader2, Save, RefreshCw } from 'lucide-react'

export default function SettingsPage() {
  const queryClient = useQueryClient()
  
  const { data: config, isLoading } = useQuery({
    queryKey: ['config'],
    queryFn: api.getConfig,
  })

  const [weights, setWeights] = useState({
    money: 0.33,
    passion: 0.34,
    location: 0.33,
  })

  const [weightsLoaded, setWeightsLoaded] = useState(false)

  // Load weights from config when it arrives
  if (config && !weightsLoaded) {
    setWeights(config.scoring_weights)
    setWeightsLoaded(true)
  }

  const updateMutation = useMutation({
    mutationFn: api.updateConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
    },
  })

  const syncMutation = useMutation({
    mutationFn: api.triggerSync,
  })

  const handleWeightChange = (key: 'money' | 'passion' | 'location', value: number) => {
    const newWeights = { ...weights, [key]: value }
    
    // Normalize to sum to 1.0
    const total = newWeights.money + newWeights.passion + newWeights.location
    if (total > 0) {
      const scale = 1 / total
      newWeights.money = Math.round(newWeights.money * scale * 100) / 100
      newWeights.passion = Math.round(newWeights.passion * scale * 100) / 100
      newWeights.location = Math.round((1 - newWeights.money - newWeights.passion) * 100) / 100
    }
    
    setWeights(newWeights)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  return (
    <div className="p-6 max-w-4xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>

      {/* Scoring Weights */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Scoring Weights</h2>
        <p className="text-sm text-gray-600 mb-4">
          Adjust how much each factor contributes to the total score. Weights must sum to 100%.
        </p>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Money (Salary) - {Math.round(weights.money * 100)}%
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={weights.money * 100}
              onChange={(e) => handleWeightChange('money', parseInt(e.target.value) / 100)}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Passion (Keywords) - {Math.round(weights.passion * 100)}%
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={weights.passion * 100}
              onChange={(e) => handleWeightChange('passion', parseInt(e.target.value) / 100)}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Location - {Math.round(weights.location * 100)}%
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={weights.location * 100}
              onChange={(e) => handleWeightChange('location', parseInt(e.target.value) / 100)}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
          </div>
        </div>

        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <div className="text-sm text-gray-600">
            <span className="font-medium">Preview:</span>
            <span className="ml-2">
              Money: {Math.round(weights.money * 100)}% | 
              Passion: {Math.round(weights.passion * 100)}% | 
              Location: {Math.round(weights.location * 100)}%
            </span>
          </div>
        </div>

        <button
          onClick={() => updateMutation.mutate({ scoring_weights: weights })}
          disabled={updateMutation.isPending}
          className="mt-4 flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
        >
          {updateMutation.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          Save & Recalculate Scores
        </button>

        {updateMutation.isSuccess && (
          <p className="mt-2 text-sm text-green-600">
            ✓ Scores updated for all jobs
          </p>
        )}
      </div>

      {/* Sync Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Data Sync</h2>
        <p className="text-sm text-gray-600 mb-4">
          Sync with the latest data from GitHub Actions. This will import any new jobs
          that were scraped by the automated pipeline.
        </p>

        <button
          onClick={() => syncMutation.mutate()}
          disabled={syncMutation.isPending}
          className="flex items-center gap-2 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-900 disabled:opacity-50"
        >
          {syncMutation.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <RefreshCw className="w-4 h-4" />
          )}
          Sync Now
        </button>

        {syncMutation.isSuccess && (
          <p className="mt-2 text-sm text-green-600">
            ✓ Sync complete - {syncMutation.data?.newJobs || 0} new jobs imported
          </p>
        )}

        {syncMutation.isError && (
          <p className="mt-2 text-sm text-red-600">
            ✗ Sync failed - check console for details
          </p>
        )}
      </div>
    </div>
  )
}
