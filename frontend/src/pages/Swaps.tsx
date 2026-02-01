import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Header from '../components/Header'
import Tabs from '../components/Tabs'
import Card from '../components/Card'
import Badge from '../components/Badge'
import Button from '../components/Button'
import { swapsApi, marketplaceApi } from '../services/api'
import { useLenderStore } from '../stores/lenderStore'
import { useCreditsStore } from '../stores/creditsStore'

const tabs = [
  { id: 'auto', label: 'Auto Swaps', icon: 'autorenew' },
  { id: 'manual', label: 'Manual Proposals', icon: 'edit' },
]

export default function Swaps() {
  const [activeTab, setActiveTab] = useState('auto')
  const [inclusionOnly, setInclusionOnly] = useState(false)
  const { currentLender } = useLenderStore()
  const { balance } = useCreditsStore()
  const queryClient = useQueryClient()

  const { data: autoMatches } = useQuery({
    queryKey: ['auto-swaps', currentLender?.id, inclusionOnly],
    queryFn: () => swapsApi.getAutoMatches(currentLender!.id, inclusionOnly).then((res) => res.data),
    enabled: !!currentLender?.id,
  })

  const { data: proposals } = useQuery({
    queryKey: ['my-proposals', currentLender?.id],
    queryFn: () => swapsApi.getMyProposals(currentLender!.id).then((res) => res.data),
    enabled: !!currentLender?.id,
  })

  const { data: myLoans } = useQuery({
    queryKey: ['my-loans-for-swap', currentLender?.id],
    queryFn: () => marketplaceApi.getMyLoans(currentLender!.id, true).then((res) => res.data),
    enabled: !!currentLender?.id && activeTab === 'manual',
  })

  const acceptMutation = useMutation({
    mutationFn: (proposalId: number) => swapsApi.acceptProposal(proposalId, currentLender!.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['my-proposals'] }),
  })

  return (
    <>
      <Header
        title="Loan Swaps Dashboard"
        subtitle="AI-identified swaps that optimize portfolio fit for both parties"
        actions={
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-400">
              {balance} <span className="text-white">Credits</span>
            </span>
            <Button variant="secondary" size="sm" icon="history">
              Swap History
            </Button>
          </div>
        }
      />

      <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Tabs */}
          <div className="flex items-center justify-between">
            <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
            {activeTab === 'auto' && (
              <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
                <input
                  type="checkbox"
                  checked={inclusionOnly}
                  onChange={(e) => setInclusionOnly(e.target.checked)}
                  className="rounded bg-slate-800 border-slate-700 text-primary focus:ring-primary"
                />
                Inclusion swaps only
              </label>
            )}
          </div>

          {/* Content */}
          {activeTab === 'auto' ? (
            // Auto Swaps
            <div className="space-y-6">
              <h3 className="text-white font-bold">Double-Benefit Matches</h3>
              <p className="text-slate-400 text-sm -mt-4">
                AI-identified swaps that optimize portfolio fit for both parties
              </p>

              {autoMatches?.length > 0 ? (
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                  {autoMatches.map((match: any, index: number) => (
                    <Card key={index} padding="none">
                      <div className="p-4 border-b border-slate-800">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            {match.is_inclusion_swap && (
                              <Badge variant="info">Inclusion</Badge>
                            )}
                            <span className="text-slate-400 text-xs">
                              Score: {match.swap_score.toFixed(0)}
                            </span>
                          </div>
                          <span className="text-accent-teal text-sm font-medium">
                            +{match.total_fit_improvement.toFixed(0)}% Total Improvement
                          </span>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 divide-x divide-slate-800">
                        {/* Give */}
                        <div className="p-4">
                          <p className="text-xs text-orange-400 font-medium mb-2">YOU GIVE</p>
                          <h4 className="text-white font-bold">{match.give_company_id}</h4>
                          <p className="text-slate-400 text-sm">{match.give_sector}</p>
                          <p className="text-white font-medium mt-2">{match.give_value_banded}</p>
                          <div className="mt-2 text-xs">
                            <span className="text-slate-400">Fit improvement for them: </span>
                            <span className="text-accent-teal">+{match.give_fit_improvement?.toFixed(0)}%</span>
                          </div>
                        </div>

                        {/* Receive */}
                        <div className="p-4">
                          <p className="text-xs text-accent-teal font-medium mb-2">YOU RECEIVE</p>
                          <h4 className="text-white font-bold">{match.receive_company_id}</h4>
                          <p className="text-slate-400 text-sm">{match.receive_sector}</p>
                          <p className="text-white font-medium mt-2">{match.receive_value_banded}</p>
                          <div className="mt-2 text-xs">
                            <span className="text-slate-400">Fit improvement for you: </span>
                            <span className="text-accent-teal">+{match.receive_fit_improvement?.toFixed(0)}%</span>
                          </div>
                        </div>
                      </div>

                      <div className="p-4 border-t border-slate-800 flex items-center justify-between">
                        <div className="text-sm">
                          <span className="text-slate-400">Counterparty: </span>
                          <span className="text-white">{match.counterparty_lender}</span>
                          {match.cash_adjustment !== 0 && (
                            <span className="text-slate-400 ml-2">
                              Cash: {match.cash_adjustment > 0 ? '+' : ''}
                              £{Math.abs(match.cash_adjustment).toLocaleString()}
                            </span>
                          )}
                        </div>
                        <div className="flex gap-2">
                          <Button variant="secondary" size="sm" icon="info">
                            Details (1)
                          </Button>
                          <Button variant="primary" size="sm" icon="check">
                            Accept (3)
                          </Button>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-slate-500">
                  <span className="material-symbols-outlined text-4xl mb-2">swap_horiz</span>
                  <p>No auto-matched swaps available</p>
                </div>
              )}
            </div>
          ) : (
            // Manual Proposals
            <div className="space-y-6">
              {/* Proposal Wizard */}
              <Card>
                <h4 className="text-white font-bold mb-4">Manual Proposal Wizard</h4>
                <p className="text-slate-400 text-sm mb-4">
                  Can't find an auto-match? Create a custom swap proposal.
                </p>
                <div className="space-y-4">
                  <div>
                    <label className="text-xs text-slate-400 mb-1 block">
                      Step 1: Pick the loan you want to swap
                    </label>
                    <select className="w-full bg-slate-800 border-slate-700 text-sm text-white rounded px-3 py-2 focus:ring-primary">
                      <option value="">Select a loan...</option>
                      {myLoans?.map((loan: any) => (
                        <option key={loan.loan_id} value={loan.loan_id}>
                          {loan.company_id} - {loan.sector} ({loan.outstanding_balance_banded})
                        </option>
                      ))}
                    </select>
                  </div>
                  <Button variant="primary" icon="arrow_forward">
                    Next Step
                  </Button>
                </div>
              </Card>

              {/* Incoming Proposals */}
              <div>
                <h4 className="text-white font-bold mb-4">Incoming Proposals</h4>
                {proposals?.filter((p: any) => !p.is_proposer && p.status === 'pending').length > 0 ? (
                  <div className="space-y-4">
                    {proposals
                      .filter((p: any) => !p.is_proposer && p.status === 'pending')
                      .map((proposal: any) => (
                        <Card key={proposal.id}>
                          <div className="flex items-start justify-between">
                            <div>
                              <div className="flex items-center gap-2 mb-2">
                                <h4 className="text-white font-bold">
                                  Swap Proposal from {proposal.proposer_lender}
                                </h4>
                                {proposal.is_inclusion_swap && <Badge variant="info">Inclusion</Badge>}
                              </div>
                              <p className="text-slate-400 text-sm">
                                They offer: {proposal.proposer_company_id} ({proposal.proposer_sector})
                              </p>
                            </div>
                            <div className="flex gap-2">
                              <Button
                                variant="ghost"
                                size="sm"
                                icon="close"
                              >
                                Decline
                              </Button>
                              <Button
                                variant="primary"
                                size="sm"
                                icon="check"
                                onClick={() => acceptMutation.mutate(proposal.id)}
                              >
                                Accept
                              </Button>
                            </div>
                          </div>
                        </Card>
                      ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-slate-500 bg-surface-dark rounded-lg border border-slate-800">
                    <span className="material-symbols-outlined text-3xl mb-2">inbox</span>
                    <p>No incoming proposals</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Inclusion Banner */}
          <div className="bg-gradient-to-r from-primary/20 to-accent-teal/20 border border-primary/30 rounded-lg p-6">
            <h4 className="text-white font-bold mb-2">Join the Inclusion Revolution</h4>
            <p className="text-slate-300 text-sm mb-4">
              Our AI engines have already reallocated over $50M in SME loans, prioritizing businesses
              that foster regional growth and sustainability. Your swap isn't just a financial move—
              it's a story of growth.
            </p>
            <div className="flex gap-8">
              <div>
                <p className="text-3xl font-bold text-white">120+</p>
                <p className="text-xs text-slate-400">Loans Reallocated</p>
              </div>
              <div>
                <p className="text-3xl font-bold text-accent-teal">14.2%</p>
                <p className="text-xs text-slate-400">Avg. Inclusion Improvement</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
