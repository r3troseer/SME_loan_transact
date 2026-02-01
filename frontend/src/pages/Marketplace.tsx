import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Header from '../components/Header'
import Tabs from '../components/Tabs'
import Card from '../components/Card'
import Badge from '../components/Badge'
import Button from '../components/Button'
import { marketplaceApi } from '../services/api'
import { useLenderStore } from '../stores/lenderStore'
import { useCreditsStore } from '../stores/creditsStore'

const tabs = [
  { id: 'sell', label: 'Loans to Sell', icon: 'sell' },
  { id: 'buy', label: 'Opportunities to Buy', icon: 'shopping_cart' },
]

export default function Marketplace() {
  const [activeTab, setActiveTab] = useState('sell')
  const [selectedLoan, setSelectedLoan] = useState<number | null>(null)
  const { currentLender } = useLenderStore()
  const { balance } = useCreditsStore()
  const queryClient = useQueryClient()

  const { data: myLoans } = useQuery({
    queryKey: ['my-loans', currentLender?.id],
    queryFn: () => marketplaceApi.getMyLoans(currentLender!.id).then((res) => res.data),
    enabled: !!currentLender?.id,
  })

  const { data: opportunities } = useQuery({
    queryKey: ['opportunities', currentLender?.id],
    queryFn: () => marketplaceApi.getOpportunities(currentLender!.id).then((res) => res.data),
    enabled: !!currentLender?.id,
  })

  const listMutation = useMutation({
    mutationFn: (loanId: number) => marketplaceApi.listLoan(loanId, currentLender!.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['my-loans'] }),
  })

  const interestMutation = useMutation({
    mutationFn: (loanId: number) => marketplaceApi.expressInterest(loanId, currentLender!.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['opportunities'] }),
  })

  return (
    <>
      <Header
        title="Loan Sales Marketplace"
        subtitle="Real-time SME loan reallocation powered by Inclusive AI"
        actions={
          <div className="flex items-center gap-4">
            <div className="text-sm">
              <span className="text-slate-400">AI Credit Balance:</span>
              <span className="text-white font-bold ml-2">{balance} Credits</span>
            </div>
          </div>
        }
      />

      <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Tabs */}
          <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

          {/* Content */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Loan List */}
            <div className="lg:col-span-2 space-y-4">
              {activeTab === 'sell' ? (
                // Loans to Sell
                myLoans?.length > 0 ? (
                  myLoans.map((loan: any) => (
                    <Card
                      key={loan.loan_id}
                      className={`cursor-pointer transition-all ${
                        selectedLoan === loan.loan_id ? 'ring-2 ring-primary' : ''
                      }`}
                      onClick={() => setSelectedLoan(loan.loan_id)}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <h4 className="text-white font-bold">{loan.company_id}</h4>
                            <Badge variant={loan.reallocation_status === 'STRONG' ? 'warning' : 'neutral'}>
                              {loan.reallocation_status}
                            </Badge>
                            {loan.is_listed && <Badge variant="success">Listed</Badge>}
                          </div>
                          <p className="text-slate-400 text-sm">
                            {loan.sector} • {loan.region}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-white font-bold text-lg">{loan.outstanding_balance_banded}</p>
                          <p className="text-slate-400 text-xs">Outstanding</p>
                        </div>
                      </div>
                      <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <p className="text-slate-400 text-xs">Current Fit</p>
                          <p className="text-orange-400 font-medium">{loan.current_fit?.toFixed(0)}%</p>
                        </div>
                        <div>
                          <p className="text-slate-400 text-xs">Best Match Fit</p>
                          <p className="text-accent-teal font-medium">{loan.best_match_fit?.toFixed(0)}%</p>
                        </div>
                        <div>
                          <p className="text-slate-400 text-xs">Fit Gap</p>
                          <p className="text-white font-medium">+{loan.fit_gap?.toFixed(0)}%</p>
                        </div>
                      </div>
                      <div className="mt-4 flex gap-2">
                        {!loan.is_listed ? (
                          <Button
                            variant="primary"
                            size="sm"
                            icon="storefront"
                            onClick={(e) => {
                              e.stopPropagation()
                              listMutation.mutate(loan.loan_id)
                            }}
                          >
                            List for Sale
                          </Button>
                        ) : (
                          <>
                            <Button variant="secondary" size="sm" icon="visibility">
                              View Bids ({loan.bid_count})
                            </Button>
                            <Button variant="ghost" size="sm" icon="person">
                              Reveal (5 credits)
                            </Button>
                          </>
                        )}
                      </div>
                    </Card>
                  ))
                ) : (
                  <div className="text-center py-12 text-slate-500">
                    <span className="material-symbols-outlined text-4xl mb-2">inventory_2</span>
                    <p>No mismatched loans in your portfolio</p>
                  </div>
                )
              ) : (
                // Opportunities to Buy
                opportunities?.length > 0 ? (
                  opportunities.map((loan: any) => (
                    <Card
                      key={loan.loan_id}
                      className={`cursor-pointer transition-all ${
                        selectedLoan === loan.loan_id ? 'ring-2 ring-primary' : ''
                      }`}
                      onClick={() => setSelectedLoan(loan.loan_id)}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <h4 className="text-white font-bold">{loan.company_id}</h4>
                            <Badge variant="info">Best Match</Badge>
                          </div>
                          <p className="text-slate-400 text-sm">
                            {loan.sector} • {loan.region} • Seller: {loan.seller_lender}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-white font-bold text-lg">
                            £{loan.suggested_price?.toLocaleString()}
                          </p>
                          <p className="text-accent-teal text-xs">
                            {loan.discount_percent?.toFixed(1)}% discount
                          </p>
                        </div>
                      </div>
                      <div className="mt-4 grid grid-cols-4 gap-4 text-sm">
                        <div>
                          <p className="text-slate-400 text-xs">Your Fit</p>
                          <p className="text-accent-teal font-medium">{loan.your_fit?.toFixed(0)}%</p>
                        </div>
                        <div>
                          <p className="text-slate-400 text-xs">Improvement</p>
                          <p className="text-white font-medium">+{loan.fit_improvement?.toFixed(0)}%</p>
                        </div>
                        <div>
                          <p className="text-slate-400 text-xs">Risk Score</p>
                          <p className="text-white font-medium">{loan.risk_score?.toFixed(0)}</p>
                        </div>
                        <div>
                          <p className="text-slate-400 text-xs">Ann. ROI</p>
                          <p className="text-white font-medium">{loan.annualized_roi?.toFixed(1)}%</p>
                        </div>
                      </div>
                      <div className="mt-4 flex gap-2">
                        <Button variant="secondary" size="sm" icon="info">
                          View Details (1)
                        </Button>
                        <Button
                          variant="primary"
                          size="sm"
                          icon="favorite"
                          onClick={(e) => {
                            e.stopPropagation()
                            interestMutation.mutate(loan.loan_id)
                          }}
                        >
                          Express Interest (5)
                        </Button>
                        <Button variant="ghost" size="sm" icon="gavel">
                          Submit Bid (3)
                        </Button>
                      </div>
                    </Card>
                  ))
                ) : (
                  <div className="text-center py-12 text-slate-500">
                    <span className="material-symbols-outlined text-4xl mb-2">search_off</span>
                    <p>No opportunities available for you right now</p>
                  </div>
                )
              )}
            </div>

            {/* AI Insights Panel */}
            <div className="lg:col-span-1">
              <Card>
                <div className="flex items-center gap-2 mb-4">
                  <span className="material-symbols-outlined text-primary">auto_awesome</span>
                  <h4 className="text-white font-bold">AI Insight</h4>
                  <Badge variant="info">BETA</Badge>
                </div>
                {selectedLoan ? (
                  <div className="space-y-4">
                    <div className="p-3 bg-slate-800/50 rounded-lg">
                      <p className="text-xs text-slate-400 mb-1">MATCH REASON</p>
                      <p className="text-sm text-white">
                        This loan shows 92% alignment with your risk profile. The 24-month payment
                        history is flawless, and the sector shows strong growth signals.
                      </p>
                    </div>
                    <div className="p-3 bg-slate-800/50 rounded-lg">
                      <p className="text-xs text-slate-400 mb-1">RISK FACTORS</p>
                      <ul className="text-sm text-slate-300 space-y-1">
                        <li className="flex items-center gap-2">
                          <span className="size-1.5 rounded-full bg-accent-teal" />
                          Market Volatility: Low
                        </li>
                        <li className="flex items-center gap-2">
                          <span className="size-1.5 rounded-full bg-accent-teal" />
                          Cashflow Speed: Balanced
                        </li>
                      </ul>
                    </div>
                    <Button variant="primary" size="sm" icon="auto_awesome" className="w-full">
                      Generate AI Explanation (2)
                    </Button>
                  </div>
                ) : (
                  <div className="text-center py-8 text-slate-500">
                    <span className="material-symbols-outlined text-3xl mb-2">touch_app</span>
                    <p className="text-sm">Select a loan to see AI insights</p>
                  </div>
                )}
              </Card>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
