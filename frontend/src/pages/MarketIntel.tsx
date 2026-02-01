import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Header from '../components/Header'
import Tabs from '../components/Tabs'
import Card from '../components/Card'
import MetricCard from '../components/MetricCard'
import Badge from '../components/Badge'
import Button from '../components/Button'
import { marketApi } from '../services/api'

const tabs = [
  { id: 'insights', label: 'Market Insights', icon: 'insights' },
  { id: 'flows', label: 'Lender Flows', icon: 'swap_horiz' },
  { id: 'inclusion', label: 'Inclusion Reports', icon: 'diversity_3' },
]

export default function MarketIntel() {
  const [activeTab, setActiveTab] = useState('insights')

  const { data: reallocationStats } = useQuery({
    queryKey: ['reallocation-stats'],
    queryFn: () => marketApi.getReallocationStats().then((res) => res.data),
  })

  const { data: inclusionAnalysis } = useQuery({
    queryKey: ['inclusion-analysis'],
    queryFn: () => marketApi.getInclusionAnalysis().then((res) => res.data),
  })

  const { data: lenderFlows } = useQuery({
    queryKey: ['lender-flows'],
    queryFn: () => marketApi.getLenderFlows().then((res) => res.data),
  })

  return (
    <>
      <Header
        title="Market Intelligence"
        subtitle="Real-time SME loan reallocation and inclusion analytics"
        actions={
          <Button variant="primary" icon="download">
            Export Report
          </Button>
        }
      />

      <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Tabs */}
          <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

          {/* Metrics Row */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <MetricCard
              label="Reallocation Candidates"
              value={reallocationStats?.mismatched_count || 0}
              badge={`${reallocationStats?.mismatched_percentage?.toFixed(1) || 0}% of total`}
              badgeColor="orange"
            />
            <MetricCard
              label="Total Reallocation Value"
              value={`£${((reallocationStats?.total_value_at_risk || 0) / 1000000).toFixed(1)}M`}
              badge="+8.2% vs last month"
              badgeColor="teal"
            />
            <MetricCard
              label="Avg Fit Improvement"
              value={`+${reallocationStats?.avg_fit_improvement?.toFixed(1) || 0}%`}
              badge="+4.2% trend"
              badgeColor="teal"
            />
            <MetricCard
              label="High Inclusion Priority"
              value={reallocationStats?.high_inclusion_priority_count || 0}
              badge="Companies"
            />
          </div>

          {/* Content based on tab */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Content */}
            <div className="lg:col-span-2 space-y-6">
              {activeTab === 'insights' && (
                <>
                  {/* Regional Inclusion Analysis */}
                  <Card>
                    <h4 className="text-white font-bold mb-4">Financial Inclusion Analysis</h4>
                    <p className="text-slate-400 text-sm mb-4">Regional underserved SME performance</p>

                    <div className="space-y-4">
                      {inclusionAnalysis?.regions?.slice(0, 5).map((region: any) => (
                        <div key={region.region} className="flex items-center gap-4">
                          <div className="w-32 text-sm text-slate-300">{region.region}</div>
                          <div className="flex-1 bg-slate-800 h-2 rounded-full">
                            <div
                              className="bg-primary h-full rounded-full"
                              style={{ width: `${region.inclusion_percentage}%` }}
                            />
                          </div>
                          <div className="w-24 text-right">
                            <span className="text-white font-medium">
                              {region.inclusion_percentage.toFixed(0)}%
                            </span>
                            <span className="text-slate-500 text-xs ml-1">Inclusion</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>

                  {/* Reallocation by Status */}
                  <Card>
                    <h4 className="text-white font-bold mb-4">Reallocation Breakdown</h4>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="text-center p-4 bg-red-500/10 rounded-lg border border-red-500/20">
                        <p className="text-3xl font-bold text-red-400">
                          {reallocationStats?.strong_reallocation_count || 0}
                        </p>
                        <p className="text-xs text-slate-400 mt-1">Strong Candidates</p>
                      </div>
                      <div className="text-center p-4 bg-orange-500/10 rounded-lg border border-orange-500/20">
                        <p className="text-3xl font-bold text-orange-400">
                          {reallocationStats?.moderate_reallocation_count || 0}
                        </p>
                        <p className="text-xs text-slate-400 mt-1">Moderate Candidates</p>
                      </div>
                      <div className="text-center p-4 bg-slate-500/10 rounded-lg border border-slate-500/20">
                        <p className="text-3xl font-bold text-slate-400">
                          {reallocationStats?.minor_reallocation_count || 0}
                        </p>
                        <p className="text-xs text-slate-400 mt-1">Minor Candidates</p>
                      </div>
                    </div>
                  </Card>
                </>
              )}

              {activeTab === 'flows' && (
                <Card>
                  <h4 className="text-white font-bold mb-4">Optimal Lender Flows</h4>
                  <p className="text-slate-400 text-sm mb-6">
                    Portfolio rebalance: Current vs Proposed
                  </p>

                  <div className="space-y-6">
                    {lenderFlows?.map((flow: any) => (
                      <div key={flow.lender_id}>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-white font-medium">{flow.lender_name}</span>
                          <span
                            className={`text-sm font-medium ${
                              flow.net_flow > 0
                                ? 'text-accent-teal'
                                : flow.net_flow < 0
                                ? 'text-orange-400'
                                : 'text-slate-400'
                            }`}
                          >
                            {flow.net_flow > 0 ? '+' : ''}
                            {flow.net_flow} net
                          </span>
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-slate-400">Current</span>
                              <span className="text-slate-300">{flow.current_count} loans</span>
                            </div>
                            <div className="bg-slate-800 h-2 rounded-full">
                              <div
                                className="bg-slate-500 h-full rounded-full"
                                style={{
                                  width: `${Math.min(
                                    (flow.current_count / Math.max(flow.current_count, flow.optimal_count)) * 100,
                                    100
                                  )}%`,
                                }}
                              />
                            </div>
                          </div>
                          <div>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-slate-400">Optimal</span>
                              <span className="text-accent-teal">{flow.optimal_count} loans</span>
                            </div>
                            <div className="bg-slate-800 h-2 rounded-full">
                              <div
                                className="bg-accent-teal h-full rounded-full"
                                style={{
                                  width: `${Math.min(
                                    (flow.optimal_count / Math.max(flow.current_count, flow.optimal_count)) * 100,
                                    100
                                  )}%`,
                                }}
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {activeTab === 'inclusion' && (
                <Card>
                  <h4 className="text-white font-bold mb-4">Inclusion Report Summary</h4>
                  <div className="space-y-4">
                    <div className="p-4 bg-primary/10 border border-primary/20 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="material-symbols-outlined text-primary">verified</span>
                        <span className="text-white font-medium">Overall Inclusion Rate</span>
                      </div>
                      <p className="text-3xl font-bold text-white">
                        {inclusionAnalysis?.overall_inclusion_rate?.toFixed(1) || 0}%
                      </p>
                      <p className="text-slate-400 text-sm mt-1">
                        {inclusionAnalysis?.total_high_priority || 0} of {inclusionAnalysis?.total_companies || 0}{' '}
                        companies are high inclusion priority
                      </p>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      {inclusionAnalysis?.regions?.map((region: any) => (
                        <div
                          key={region.region}
                          className="p-3 bg-slate-800/50 rounded-lg"
                        >
                          <p className="text-white font-medium text-sm">{region.region}</p>
                          <p className="text-2xl font-bold text-accent-teal mt-1">
                            {region.high_priority_count}
                          </p>
                          <p className="text-xs text-slate-400">
                            High priority ({region.inclusion_percentage.toFixed(0)}%)
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </Card>
              )}
            </div>

            {/* AI Insights Sidebar */}
            <div className="lg:col-span-1">
              <Card>
                <div className="flex items-center gap-2 mb-4">
                  <span className="material-symbols-outlined text-primary">auto_awesome</span>
                  <h4 className="text-white font-bold">AI Insights</h4>
                </div>

                <div className="space-y-4">
                  <div className="p-3 bg-slate-800/50 rounded-lg border-l-2 border-accent-teal">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="success" size="sm">
                        HIGH PRIORITY
                      </Badge>
                    </div>
                    <p className="text-white text-sm font-medium">
                      High demand for green energy loans in Northern sector
                    </p>
                    <p className="text-slate-400 text-xs mt-1">
                      £5.2M unreallocated pool of SMEs seeking lenders with ESG mandates
                    </p>
                    <Button variant="ghost" size="sm" className="mt-2">
                      Create target list
                    </Button>
                  </div>

                  <div className="p-3 bg-slate-800/50 rounded-lg border-l-2 border-primary">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="info" size="sm">
                        OPPORTUNITY
                      </Badge>
                    </div>
                    <p className="text-white text-sm font-medium">
                      Women-led tech SMEs show reduced risk profiles
                    </p>
                    <p className="text-slate-400 text-xs mt-1">
                      Analysis shows 12% lower default rates in this segment
                    </p>
                    <Button variant="ghost" size="sm" className="mt-2">
                      View analysis
                    </Button>
                  </div>

                  <div className="p-3 bg-slate-800/50 rounded-lg border-l-2 border-orange-400">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="warning" size="sm">
                        PORTFOLIO ALERT
                      </Badge>
                    </div>
                    <p className="text-white text-sm font-medium">
                      Retail exposure reaching optimal threshold in Urban clusters
                    </p>
                    <p className="text-slate-400 text-xs mt-1">
                      Consider rebalancing to maintain diversification
                    </p>
                    <Button variant="ghost" size="sm" className="mt-2">
                      Adjust thresholds
                    </Button>
                  </div>
                </div>

                <Button variant="primary" className="w-full mt-4" icon="auto_awesome">
                  View All Intelligence
                </Button>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
