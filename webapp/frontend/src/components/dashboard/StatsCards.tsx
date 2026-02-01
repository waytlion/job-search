import { Stats } from '@/lib/types'
import { Briefcase, CheckCircle, XCircle, Star, TrendingUp, Calendar } from 'lucide-react'

interface StatsCardsProps {
  stats: Stats
}

export function StatsCards({ stats }: StatsCardsProps) {
  const cards = [
    {
      title: 'Total Jobs',
      value: stats.totalJobs.toLocaleString(),
      icon: Briefcase,
      color: 'bg-blue-500',
    },
    {
      title: 'Valid Jobs',
      value: stats.validJobs.toLocaleString(),
      icon: CheckCircle,
      color: 'bg-green-500',
    },
    {
      title: 'Filtered Out',
      value: stats.filteredJobs.toLocaleString(),
      icon: XCircle,
      color: 'bg-red-500',
    },
    {
      title: 'Average Score',
      value: stats.avgScore.toFixed(1),
      icon: TrendingUp,
      color: 'bg-purple-500',
    },
    {
      title: 'Top Score',
      value: stats.topScore.toFixed(1),
      icon: Star,
      color: 'bg-yellow-500',
    },
    {
      title: 'New This Week',
      value: stats.newThisWeek.toLocaleString(),
      icon: Calendar,
      color: 'bg-indigo-500',
    },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {cards.map((card) => (
        <div
          key={card.title}
          className="bg-white rounded-lg shadow p-4"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">{card.title}</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{card.value}</p>
            </div>
            <div className={`p-2 rounded-lg ${card.color}`}>
              <card.icon className="w-5 h-5 text-white" />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
