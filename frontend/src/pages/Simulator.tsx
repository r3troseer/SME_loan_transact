import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import Header from '../components/Header'
import Tabs from '../components/Tabs'
import Card from '../components/Card'
import Badge from '../components/Badge'
import Button from '../components/Button'
import { simulatorApi } from '../services/api'
import { useLenderStore } from '../stores/lenderStore'

const tabs = [
  { id: 'sale', label: 'Loan Sale' },
  { id: 'swap', label: 'Loan Swap' },
  { id: 'swap_cash', label: 'Swap + Cash' },
]

export default function Simulator() {
  const [activeTab, setActiveTab] = useState('swap')
  const [outgoingLoanId, setOutgoingLoanId] = useState<number | null>(null)
  const [incomingLoanId, setIncomingLoanId] = useState<number | null>(null)
  const { currentLender } = useLenderStore()

  const { data: candidates } = useQuery({
    queryKey: ['simulator-candidates', currentLender?.id],
    queryFn: () => simulatorApi.getCandidates(currentLender?.id).then((res) => res.data),
    enabled: !!currentLender?.id,
  })

  const { data: outgoingDetails } = useQuery({
    queryKey: ['loan-details', outgoingLoanId],
    queryFn: () => simulatorApi.getLoanDetails(outgoingLoanId!).then((res) => res.data),
    enabled: !!outgoingLoanId,
  })

  const { data: incomingDetails } = useQuery({
    queryKey: ['loan-details', incomingLoanId],
    queryFn: () => simulatorApi.getLoanDetails(incomingLoanId!).then((res) => res.data),
    enabled: !!incomingLoanId,
  })

  const simulateMutation = useMutation({
    mutationFn: () =>
      simulatorApi.calculate(activeTab, outgoingLoanId!, incomingLoanId || undefined).then((res) => res.data),
  })

  const simulation = simulateMutation.data

  return (
    <>
      <Header
        title="Transaction Simulator"
        subtitle="Simulate potential reallocation scenarios and optimize your portfolio balance"
        actions={
          simulation && (
            <Badge variant={simulation.is_zero_cash ? 'success' : 'warning'}>
              {simulation.is_zero_cash ? 'AI MATCH CONFIRMED' : 'CASH ADJUSTMENT REQUIRED'}
            </Badge>
          )
        }
      />

      <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
        <div className="max-w-6xl mx-auto space-y-6">
          {/* Transaction Type Tabs */}
          <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

          {/* Loan Selection */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-slate-400 mb-2 block">Outgoing Asset</label>
              <select
                value={outgoingLoanId || ''}
                onChange={(e) => setOutgoingLoanId(Number(e.target.value) || null)}
                className="w-full bg-slate-800 border-slate-700 text-sm text-white rounded px-3 py-2 focus:ring-primary"
              >
                <option value="">Select a loan to transfer...</option>
                {candidates?.map((c: any) => (
                  <option key={c.loan_id} value={c.loan_id}>
                    {c.company_id} - {c.sector} ({c.outstanding_balance_banded})
                  </option>
                ))}
              </select>
            </div>

            {activeTab !== 'sale' && (
              <div>
                <label className="text-xs text-slate-400 mb-2 block">Incoming Asset</label>
                <select
                  value={incomingLoanId || ''}
                  onChange={(e) => setIncomingLoanId(Number(e.target.value) || null)}
                  className="w-full bg-slate-800 border-slate-700 text-sm text-white rounded px-3 py-2 focus:ring-primary"
                >
                  <option value="">Select a loan to receive...</option>
                  {candidates
                    ?.filter((c: any) => c.loan_id !== outgoingLoanId)
                    .map((c: any) => (
                      <option key={c.loan_id} value={c.loan_id}>
                        {c.company_id} - {c.sector} ({c.outstanding_balance_banded})
                      </option>
                    ))}
                </select>
              </div>
            )}
          </div>

          {/* Simulate Button */}
          <Button
            variant="primary"
            onClick={() => simulateMutation.mutate()}
            disabled={!outgoingLoanId || (activeTab !== 'sale' && !incomingLoanId)}
            icon="calculate"
          >
            Run Simulation
          </Button>

          {/* Simulation Results */}
          {(outgoingDetails || simulation) && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Outgoing Asset */}
              <Card>
                <p className="text-xs text-orange-400 font-bold mb-4">OUTGOING ASSET</p>
                {outgoingDetails ? (
                  <div className="space-y-4">
                    <div>
                      <p className="text-white font-bold text-lg">{outgoingDetails.current_lender_name}</p>
                      <p className="text-slate-400 text-sm">Loan #{outgoingDetails.loan_id}</p>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-slate-400 text-xs">Book Value</p>
                        <p className="text-white font-medium">
                          £{outgoingDetails.outstanding_balance?.toLocaleString()}
                        </p>
                      </div>
                      <div>
                        <p className="text-slate-400 text-xs">Risk Weight</p>
                        <Badge variant={outgoingDetails.risk_score >= 60 ? 'success' : 'warning'}>
                          {outgoingDetails.risk_category}
                        </Badge>
                      </div>
                      <div>
                        <p className="text-slate-400 text-xs">Current Fit</p>
                        <p className="text-orange-400 font-medium">
                          {outgoingDetails.current_lender_fit?.toFixed(0)}%
                        </p>
                      </div>
                      <div>
                        <p className="text-slate-400 text-xs">Strategy Fit</p>
                        <Badge variant="neutral">Low ({outgoingDetails.reallocation_status})</Badge>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-slate-500 text-sm">Select an outgoing loan</p>
                )}
              </Card>

              {/* Flow Visualization */}
              <Card className="flex flex-col items-center justify-center">
                {simulation ? (
                  <>
                    <div className="flex items-center gap-4 mb-6">
                      <div className="text-center">
                        <div className="size-12 rounded-full bg-orange-500/20 flex items-center justify-center mb-2">
                          <span className="material-symbols-outlined text-orange-400">arrow_forward</span>
                        </div>
                        <p className="text-xs text-slate-400">
                          {simulation.is_zero_cash ? '50%' : `${((simulation.outgoing_value / (simulation.outgoing_value + (simulation.incoming_value || 0))) * 100).toFixed(0)}%`}
                        </p>
                      </div>
                      <span className="material-symbols-outlined text-slate-600 text-3xl">swap_horiz</span>
                      <div className="text-center">
                        <div className="size-12 rounded-full bg-accent-teal/20 flex items-center justify-center mb-2">
                          <span className="material-symbols-outlined text-accent-teal">arrow_back</span>
                        </div>
                        <p className="text-xs text-slate-400">
                          {simulation.incoming_value ? '50%' : '0%'}
                        </p>
                      </div>
                    </div>

                    <div className="text-center">
                      <p className="text-xs text-slate-400 mb-1">Valuation Delta</p>
                      <p className="text-3xl font-bold text-white">
                        £{Math.abs(simulation.valuation_delta).toLocaleString()}
                      </p>
                      <p className="text-xs text-slate-500">
                        Differential in risk-adjusted valuation
                      </p>
                    </div>

                    <div className="mt-6 p-4 bg-slate-800/50 rounded-lg text-center w-full">
                      <p className="text-xs text-slate-400 mb-1">NET SETTLEMENT REQUIRED</p>
                      <p
                        className={`text-2xl font-bold ${
                          simulation.is_zero_cash ? 'text-accent-teal' : 'text-orange-400'
                        }`}
                      >
                        {simulation.is_zero_cash
                          ? 'Zero Cash'
                          : `£${Math.abs(simulation.net_settlement).toLocaleString()}`}
                      </p>
                      {!simulation.is_zero_cash && (
                        <p className="text-xs text-slate-500">
                          {simulation.net_settlement > 0 ? 'You receive' : 'You pay'}
                        </p>
                      )}
                    </div>
                  </>
                ) : (
                  <div className="text-center text-slate-500">
                    <span className="material-symbols-outlined text-4xl mb-2">calculate</span>
                    <p className="text-sm">Run simulation to see flow</p>
                  </div>
                )}
              </Card>

              {/* Incoming Asset */}
              <Card>
                <p className="text-xs text-accent-teal font-bold mb-4">INCOMING ASSET</p>
                {incomingDetails ? (
                  <div className="space-y-4">
                    <div>
                      <p className="text-white font-bold text-lg">
                        {incomingDetails.best_match_lender_name || 'Counterparty'}
                      </p>
                      <p className="text-slate-400 text-sm">Loan #{incomingDetails.loan_id}</p>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-slate-400 text-xs">Book Value</p>
                        <p className="text-white font-medium">
                          £{incomingDetails.outstanding_balance?.toLocaleString()}
                        </p>
                      </div>
                      <div>
                        <p className="text-slate-400 text-xs">Risk Weight</p>
                        <Badge variant={incomingDetails.risk_score >= 60 ? 'success' : 'warning'}>
                          {incomingDetails.risk_category}
                        </Badge>
                      </div>
                      <div>
                        <p className="text-slate-400 text-xs">Your Fit</p>
                        <p className="text-accent-teal font-medium">
                          {incomingDetails.best_match_fit?.toFixed(0)}%
                        </p>
                      </div>
                      <div>
                        <p className="text-slate-400 text-xs">Strategy Fit</p>
                        <Badge variant="success">High</Badge>
                      </div>
                    </div>
                  </div>
                ) : activeTab === 'sale' ? (
                  <div className="text-center text-slate-500 py-8">
                    <span className="material-symbols-outlined text-3xl mb-2">payments</span>
                    <p className="text-sm">Sale transaction - no incoming asset</p>
                  </div>
                ) : (
                  <p className="text-slate-500 text-sm">Select an incoming loan</p>
                )}
              </Card>
            </div>
          )}

          {/* AI Analysis & Actions */}
          {simulation && (
            <Card>
              <div className="flex items-start gap-4">
                <div className="size-10 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                  <span className="material-symbols-outlined text-primary">auto_awesome</span>
                </div>
                <div className="flex-1">
                  <h4 className="text-white font-bold mb-2">AI Swap Analysis</h4>
                  <p className="text-slate-300 text-sm mb-4">
                    {activeTab === 'sale' ? (
                      `Selling Loan #${simulation.outgoing_loan_id} at suggested price of £${simulation.outgoing_value.toLocaleString()} provides liquidity while releasing a mismatched asset from your portfolio.`
                    ) : (
                      `Swapping Loan #${simulation.outgoing_loan_id} for Bond #${simulation.incoming_loan_id} is highly efficient. You shed a high-risk asset while acquiring a stable Agri-Tech bond that aligns with your ESG mandate. Conversely, the counterparty gains exposure to a sector where they have excess risk appetite, without cash outlay.`
                    )}
                  </p>
                  <p className="text-accent-teal text-sm font-medium">
                    Total Fit Improvement: +{simulation.total_fit_improvement?.toFixed(0)}%
                  </p>
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-slate-800">
                <Button variant="ghost" icon="tune">
                  Adjust
                </Button>
                <Button variant="secondary" icon="close">
                  Reject
                </Button>
                <Button variant="primary" icon="send">
                  {activeTab === 'sale' ? 'Initiate Sale' : 'Propose Swap'} (5 Credits)
                </Button>
              </div>
            </Card>
          )}
        </div>
      </div>
    </>
  )
}
