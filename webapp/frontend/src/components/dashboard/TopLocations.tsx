import { MapPin } from 'lucide-react'

interface TopLocationsProps {
  locations: { name: string; count: number }[]
}

export function TopLocations({ locations }: TopLocationsProps) {
  const maxCount = Math.max(...locations.map(l => l.count), 1)

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center gap-2 mb-4">
        <MapPin className="w-5 h-5 text-gray-600" />
        <h3 className="text-lg font-semibold text-gray-800">Top Locations</h3>
      </div>
      <div className="space-y-3">
        {locations.map((location, index) => (
          <div key={location.name} className="flex items-center gap-3">
            <span className="text-sm text-gray-500 w-6">{index + 1}.</span>
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-gray-700 truncate max-w-[200px]">
                  {location.name}
                </span>
                <span className="text-sm text-gray-500">{location.count}</span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary-500 rounded-full"
                  style={{ width: `${(location.count / maxCount) * 100}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
