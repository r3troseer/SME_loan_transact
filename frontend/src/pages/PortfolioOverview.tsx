import { useQuery } from '@tanstack/react-query'
import Header from '../components/Header'
import MetricCard from '../components/MetricCard'
import BarChart from '../components/BarChart'
import PieChart from '../components/PieChart'
import Button from '../components/Button'
import { portfolioApi } from '../services/api'

export default function PortfolioOverview() {
  const { data: overview } = useQuery({
    queryKey: ['portfolio-overview'],
    queryFn: () => portfolioApi.getOverview().then((res) => res.data),
  })

  const { data: sectorData } = useQuery({
    queryKey: ['portfolio-sector'],
    queryFn: () => portfolioApi.getBySector().then((res) => res.data),
  })

  const { data: regionData } = useQuery({
    queryKey: ['portfolio-region'],
    queryFn: () => portfolioApi.getByRegion().then((res) => res.data),
  })

  const { data: lenderData } = useQuery({
    queryKey: ['portfolio-lender'],
    queryFn: () => portfolioApi.getLenderDistribution().then((res) => res.data),
  })

  const pieColors = ['#135bec', '#14b8a6', '#818cf8', '#38bdf8']

  return (
    <>
      <Header
        title="Portfolio Overview Dashboard"
        subtitle="SME Hackathon • Inclusive AI Reallocation Engine"
        actions={
          <>
            <Button variant="secondary" icon="download">
              Export CSV
            </Button>
            <Button variant="primary" icon="autorenew">
              Run Engine
            </Button>
          </>
        }
      />

      <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
        <div className="max-w-7xl mx-auto space-y-8">
          {/* Metrics Row */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <MetricCard
              label="Total Companies"
              value={overview?.total_companies || 0}
              suffix="SMEs"
            />
            <MetricCard
              label="Total Loan Value"
              value={overview?.total_loan_value_banded || '£0'}
              icon="visibility_off"
            />
            <MetricCard
              label="Mismatched Loans"
              value={`${overview?.mismatch_percentage || 0}%`}
              badge={overview?.mismatch_percentage > 10 ? '+' : ''}
              badgeColor={overview?.mismatch_percentage > 15 ? 'orange' : 'teal'}
            />
            <MetricCard
              label="Avg Risk Score"
              value={overview?.avg_risk_score?.toFixed(1) || 0}
              badge={overview?.avg_risk_score >= 60 ? 'Low Risk' : overview?.avg_risk_score >= 40 ? 'Moderate' : 'High Risk'}
              badgeColor={overview?.avg_risk_score >= 60 ? 'teal' : overview?.avg_risk_score >= 40 ? 'orange' : 'red'}
            />
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <BarChart
              title="Companies by Sector"
              icon="bar_chart"
              items={
                sectorData?.map((s: { sector: string; count: number }) => ({
                  label: s.sector,
                  value: s.count,
                })) || []
              }
            />
            <BarChart
              title="Companies by Region"
              icon="location_on"
              items={
                regionData?.map((r: { region: string; count: number }) => ({
                  label: r.region,
                  value: r.count,
                })) || []
              }
            />
          </div>

          {/* Bottom Row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pb-10">
            <PieChart
              title="Current Lender Distribution"
              centerLabel={`Top ${lenderData?.length || 0}\nLenders`}
              items={
                lenderData?.map((l: { lender: string; count: number; percentage: number }, i: number) => ({
                  label: l.lender,
                  value: l.count,
                  percentage: l.percentage,
                  color: pieColors[i % pieColors.length],
                })) || []
              }
            />

            {/* Hotspots Map */}
            <div className="bg-surface-dark border border-slate-800 rounded-lg p-6 lg:col-span-2 overflow-hidden relative">
              <div className="flex justify-between items-start mb-4 relative z-10">
                <div>
                  <h4 className="text-white font-bold">Reallocation Hotspots</h4>
                  <p className="text-slate-400 text-xs">Regions with highest mismatch rates</p>
                </div>
              </div>
              <div className="w-full h-64 rounded bg-slate-900/50 relative overflow-hidden flex items-center justify-center">
                {/* Placeholder for UK map */}
                <div className="text-slate-600 text-center">
                  <span className="material-symbols-outlined text-6xl">map</span>
                  <p className="text-xs mt-2">UK Regional Heatmap</p>
                </div>
                {/* Pulsing hotspot indicators */}
                <div className="absolute top-1/3 left-1/2 transform -translate-x-8">
                  <div className="size-3 bg-primary rounded-full animate-pulse-glow text-primary" />
                </div>
                <div className="absolute top-1/2 left-1/3">
                  <div className="size-2 bg-accent-teal rounded-full animate-pulse-glow text-accent-teal" />
                </div>
                <div className="absolute bottom-1/3 right-1/3">
                  <div className="size-2.5 bg-orange-400 rounded-full animate-pulse-glow text-orange-400" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="px-8 py-3 border-t border-slate-800 bg-background-dark flex justify-between items-center text-[10px] text-slate-500 font-medium">
        <p>DESIGNED FOR SME HACKATHON 2024 • INCLUSIVE AI v2.4.0</p>
        <div className="flex gap-4">
          <span>
            SYSTEM STATUS: <span className="text-accent-teal">OPERATIONAL</span>
          </span>
          <span>ENGINE LATENCY: 42ms</span>
        </div>
      </footer>
    </>
  )
}
