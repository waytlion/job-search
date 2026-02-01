import { Building2 } from 'lucide-react'

interface TopCompaniesProps {
  companies: { name: string; count: number }[]
}

export function TopCompanies({ companies }: TopCompaniesProps) {
  const maxCount = Math.max(...companies.map(c => c.count), 1)

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center gap-2 mb-4">
        <Building2 className="w-5 h-5 text-gray-600" />
        <h3 className="text-lg font-semibold text-gray-800">Top Companies</h3>
      </div>
      <div className="space-y-3">
        {companies.map((company, index) => (
          <div key={company.name} className="flex items-center gap-3">
            <span className="text-sm text-gray-500 w-6">{index + 1}.</span>
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-gray-700 truncate max-w-[200px]">
                  {company.name}
                </span>
                <span className="text-sm text-gray-500">{company.count}</span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-green-500 rounded-full"
                  style={{ width: `${(company.count / maxCount) * 100}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
