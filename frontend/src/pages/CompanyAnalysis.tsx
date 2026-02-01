import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Header from '../components/Header'
import Card from '../components/Card'
import Badge from '../components/Badge'
import Button from '../components/Button'
import { portfolioApi, companyApi } from '../services/api'

export default function CompanyAnalysis() {
  const [selectedCompanyId, setSelectedCompanyId] = useState<number | null>(null)

  const { data: companies } = useQuery({
    queryKey: ['companies-list'],
    queryFn: () => portfolioApi.getCompanies({ limit: 100 }).then((res) => res.data),
  })

  const { data: analysis, isLoading } = useQuery({
    queryKey: ['company-analysis', selectedCompanyId],
    queryFn: () => companyApi.getAnalysis(selectedCompanyId!).then((res) => res.data),
    enabled: !!selectedCompanyId,
  })

  const company = analysis?.company
  const loan = analysis?.loan

  const getRiskVariant = (score: number | null) => {
    if (!score) return 'neutral'
    if (score >= 60) return 'success'
    if (score >= 40) return 'warning'
    return 'danger'
  }

  return (
    <>
      <Header
        title="Company Health Analysis"
        subtitle="Deep-dive SME credit and inclusion metrics for reallocation processing"
        actions={
          <select
            value={selectedCompanyId || ''}
            onChange={(e) => setSelectedCompanyId(Number(e.target.value) || null)}
            className="bg-slate-800 border-slate-700 text-sm text-white rounded px-3 py-1.5 focus:ring-primary min-w-[200px]"
          >
            <option value="">Select a company...</option>
            {companies?.map((c: { id: number; sme_id: string; sector: string }) => (
              <option key={c.id} value={c.id}>
                {c.sme_id} - {c.sector}
              </option>
            ))}
          </select>
        }
      />

      <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
        {!selectedCompanyId ? (
          <div className="flex items-center justify-center h-full text-slate-500">
            <div className="text-center">
              <span className="material-symbols-outlined text-6xl mb-4">search</span>
              <p>Select a company to view analysis</p>
            </div>
          </div>
        ) : isLoading ? (
          <div className="flex items-center justify-center h-full text-slate-500">
            <span className="material-symbols-outlined animate-spin text-4xl">progress_activity</span>
          </div>
        ) : company ? (
          <div className="max-w-7xl mx-auto space-y-6">
            {/* Company Profile & Scores */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Company Profile */}
              <Card>
                <div className="flex items-start gap-4 mb-4">
                  <div className="size-12 rounded-lg bg-primary/20 flex items-center justify-center">
                    <span className="material-symbols-outlined text-primary text-2xl">business</span>
                  </div>
                  <div>
                    <h3 className="text-white font-bold text-lg">{company.sme_id}</h3>
                    <p className="text-slate-400 text-sm">Company Profile</p>
                  </div>
                </div>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Sector</span>
                    <span className="text-white">{company.sector}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Region</span>
                    <span className="text-white">{company.region}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Turnover Band</span>
                    <span className="text-white">{company.turnover_banded}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Employees</span>
                    <span className="text-white">{company.employees || 'N/A'}</span>
                  </div>
                </div>
              </Card>

              {/* Risk Assessment */}
              <Card>
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-white font-bold">Risk Assessment</h4>
                  <Badge variant={getRiskVariant(company.risk_score)}>{company.risk_category || 'N/A'}</Badge>
                </div>
                <div className="flex items-center gap-4 mb-4">
                  <div className="text-4xl font-bold text-white">
                    {company.risk_score?.toFixed(0) || 'N/A'}
                    <span className="text-lg text-slate-500">/100</span>
                  </div>
                </div>
                <div className="space-y-2 text-xs">
                  {[
                    { label: 'Liquidity', value: company.liquidity_score },
                    { label: 'Profitability', value: company.profitability_score },
                    { label: 'Leverage', value: company.leverage_score },
                    { label: 'Cash Position', value: company.cash_score },
                  ].map((item) => (
                    <div key={item.label} className="flex items-center gap-2">
                      <span className="text-slate-400 w-24">{item.label}</span>
                      <div className="flex-1 bg-slate-800 h-1.5 rounded-full">
                        <div
                          className="bg-primary h-full rounded-full"
                          style={{ width: `${item.value || 0}%` }}
                        />
                      </div>
                      <span className="text-slate-300 w-8 text-right">{item.value?.toFixed(0) || 0}</span>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Inclusion Profile */}
              <Card>
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-white font-bold">Inclusion Profile</h4>
                  <Badge variant={company.inclusion_score >= 60 ? 'info' : 'neutral'}>
                    {company.inclusion_category || 'N/A'}
                  </Badge>
                </div>
                <div className="flex items-center gap-4 mb-4">
                  <div className="text-4xl font-bold text-white">
                    {company.inclusion_score?.toFixed(0) || 'N/A'}
                    <span className="text-lg text-slate-500">/100</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <p className="text-xs text-slate-400">Inclusion Flags:</p>
                  <div className="flex flex-wrap gap-1">
                    {company.inclusion_flags?.length > 0 ? (
                      company.inclusion_flags.map((flag: string) => (
                        <Badge key={flag} variant="info" size="sm">
                          {flag}
                        </Badge>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500">No flags</span>
                    )}
                  </div>
                </div>
              </Card>
            </div>

            {/* Lender Optimization */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <h4 className="text-white font-bold mb-4">Lender Optimization</h4>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                    <div>
                      <p className="text-xs text-slate-400">Current Lender</p>
                      <p className="text-white font-medium">{company.current_lender || 'N/A'}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-orange-400">
                        {company.current_lender_fit?.toFixed(0) || 0}%
                      </p>
                      <p className="text-xs text-slate-400">Fit Score</p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-primary/10 rounded-lg border border-primary/20">
                    <div>
                      <p className="text-xs text-slate-400">Best Match</p>
                      <p className="text-white font-medium">{company.best_match_lender || 'N/A'}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-accent-teal">
                        {company.best_match_fit?.toFixed(0) || 0}%
                      </p>
                      <p className="text-xs text-slate-400">Fit Score</p>
                    </div>
                  </div>

                  {company.fit_gap && company.fit_gap > 0 && (
                    <Button variant="primary" className="w-full" icon="swap_horiz">
                      Initiate Reallocation (+{company.fit_gap.toFixed(0)}% improvement)
                    </Button>
                  )}
                </div>
              </Card>

              {/* Loan Summary */}
              {loan && (
                <Card>
                  <h4 className="text-white font-bold mb-4">Loan Summary</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-slate-400 text-xs">Outstanding Balance</p>
                      <p className="text-white font-medium">
                        £{loan.outstanding_balance?.toLocaleString() || 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-400 text-xs">Years Remaining</p>
                      <p className="text-white font-medium">{loan.years_remaining?.toFixed(1) || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-slate-400 text-xs">Interest Rate</p>
                      <p className="text-white font-medium">
                        {loan.interest_rate ? `${(loan.interest_rate * 100).toFixed(2)}%` : 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-400 text-xs">Monthly Payment</p>
                      <p className="text-white font-medium">
                        £{loan.monthly_payment?.toLocaleString() || 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-400 text-xs">Suggested Price</p>
                      <p className="text-white font-medium">
                        £{loan.suggested_price?.toLocaleString() || 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-400 text-xs">Reallocation Status</p>
                      <Badge
                        variant={
                          loan.reallocation_status === 'STRONG'
                            ? 'success'
                            : loan.reallocation_status === 'MODERATE'
                            ? 'warning'
                            : 'neutral'
                        }
                      >
                        {loan.reallocation_status || 'N/A'}
                      </Badge>
                    </div>
                  </div>
                </Card>
              )}
            </div>

            {/* Bottom Insight Banners */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pb-10">
              {company.regional_inclusion_score && company.regional_inclusion_score >= 60 && (
                <div className="bg-orange-500/10 border border-orange-500/20 rounded-lg p-4 flex items-center gap-3">
                  <span className="material-symbols-outlined text-orange-400">warning</span>
                  <div>
                    <p className="text-white text-sm font-medium">Regional Disadvantage</p>
                    <p className="text-slate-400 text-xs">Located in underserved region</p>
                  </div>
                </div>
              )}
              {company.risk_score && company.risk_score >= 65 && (
                <div className="bg-accent-teal/10 border border-accent-teal/20 rounded-lg p-4 flex items-center gap-3">
                  <span className="material-symbols-outlined text-accent-teal">trending_up</span>
                  <div>
                    <p className="text-white text-sm font-medium">Strong Growth Signal</p>
                    <p className="text-slate-400 text-xs">Solid financial health indicators</p>
                  </div>
                </div>
              )}
              {company.inclusion_score && company.inclusion_score >= 60 && (
                <div className="bg-primary/10 border border-primary/20 rounded-lg p-4 flex items-center gap-3">
                  <span className="material-symbols-outlined text-primary">priority_high</span>
                  <div>
                    <p className="text-white text-sm font-medium">Inclusion Priority</p>
                    <p className="text-slate-400 text-xs">{company.inclusion_category}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : null}
      </div>
    </>
  )
}
