import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Portfolio API
export const portfolioApi = {
  getOverview: () => api.get('/portfolio/overview'),
  getBySector: () => api.get('/portfolio/by-sector'),
  getByRegion: (grouped = true) => api.get('/portfolio/by-region', { params: { grouped } }),
  getLenderDistribution: () => api.get('/portfolio/lender-distribution'),
  getCompanies: (params?: { skip?: number; limit?: number; sector?: string; region?: string }) =>
    api.get('/portfolio/companies', { params }),
}

// Company API
export const companyApi = {
  getCompany: (id: number) => api.get(`/companies/${id}`),
  getAnalysis: (id: number) => api.get(`/companies/${id}/analysis`),
}

// Marketplace API
export const marketplaceApi = {
  getOpportunities: (lenderId: number, sector?: string, minRoi?: number) =>
    api.get('/marketplace/opportunities', { params: { lender_id: lenderId, sector, min_roi: minRoi } }),
  getMyLoans: (lenderId: number, mismatchedOnly = true) =>
    api.get('/marketplace/my-loans', { params: { lender_id: lenderId, mismatched_only: mismatchedOnly } }),
  listLoan: (loanId: number, lenderId: number) =>
    api.post('/marketplace/list', { loan_id: loanId, lender_id: lenderId }),
  submitBid: (loanId: number, lenderId: number, discountPercent: number) =>
    api.post('/marketplace/bid', { loan_id: loanId, lender_id: lenderId, discount_percent: discountPercent }),
  expressInterest: (loanId: number, lenderId: number) =>
    api.post('/marketplace/interest', { loan_id: loanId, lender_id: lenderId }),
  reveal: (loanId: number, lenderId: number, isBuyer: boolean) =>
    api.post('/marketplace/reveal', { loan_id: loanId, lender_id: lenderId, is_buyer: isBuyer }),
  getStats: () => api.get('/marketplace/stats'),
}

// Credits API
export const creditsApi = {
  getBalance: (lenderId: number) => api.get('/credits/balance', { params: { lender_id: lenderId } }),
  spend: (lenderId: number, actionType: string, targetType?: string, targetId?: string) =>
    api.post('/credits/spend', { lender_id: lenderId, action_type: actionType, target_type: targetType, target_id: targetId }),
  getHistory: (lenderId: number, limit = 50) =>
    api.get('/credits/history', { params: { lender_id: lenderId, limit } }),
  getCosts: () => api.get('/credits/costs'),
}

// AI API
export const aiApi = {
  getExplanation: (loanId: number) => api.post('/ai/explanation', { loan_id: loanId }),
  getMarketInsight: (focusArea?: string) => api.post('/ai/market-insight', { focus_area: focusArea }),
  getSwapStory: (loan1Id: number, loan2Id: number) =>
    api.post('/ai/swap-story', { loan1_id: loan1Id, loan2_id: loan2Id }),
  getCompanyInsight: (companyId: number) => api.post('/ai/company-insight', { company_id: companyId }),
}

// Swaps API
export const swapsApi = {
  getAutoMatches: (lenderId: number, inclusionOnly = false) =>
    api.get('/swaps/auto-matches', { params: { lender_id: lenderId, inclusion_only: inclusionOnly } }),
  getMyProposals: (lenderId: number, status?: string) =>
    api.get('/swaps/my-proposals', { params: { lender_id: lenderId, status } }),
  createProposal: (data: {
    proposer_lender_id: number
    proposer_loan_id: number
    counterparty_lender_id: number
    counterparty_loan_id?: number
    reasoning?: string
  }) => api.post('/swaps/propose', data),
  acceptProposal: (proposalId: number, lenderId: number, selectedLoanId?: number) =>
    api.post('/swaps/accept', { proposal_id: proposalId, lender_id: lenderId, selected_loan_id: selectedLoanId }),
  declineProposal: (proposalId: number, lenderId: number) =>
    api.post('/swaps/decline', null, { params: { proposal_id: proposalId, lender_id: lenderId } }),
}

// Market Intelligence API
export const marketApi = {
  getInclusionAnalysis: () => api.get('/market/inclusion-analysis'),
  getLenderFlows: () => api.get('/market/lender-flows'),
  getReallocationStats: () => api.get('/market/reallocation-stats'),
}

// Simulator API
export const simulatorApi = {
  getCandidates: (lenderId?: number) =>
    api.get('/simulator/candidates', { params: { lender_id: lenderId } }),
  getLoanDetails: (loanId: number) => api.get(`/simulator/details/${loanId}`),
  calculate: (transactionType: string, outgoingLoanId: number, incomingLoanId?: number) =>
    api.post('/simulator/calculate', {
      transaction_type: transactionType,
      outgoing_loan_id: outgoingLoanId,
      incoming_loan_id: incomingLoanId,
    }),
}

export default api
