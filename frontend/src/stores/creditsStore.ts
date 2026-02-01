import { create } from 'zustand'

interface CreditsState {
  balance: number
  totalSpent: number
  actionCount: number
  setBalance: (balance: number) => void
  updateAfterSpend: (cost: number, newBalance: number) => void
}

export const useCreditsStore = create<CreditsState>((set) => ({
  balance: 100, // Initial credits
  totalSpent: 0,
  actionCount: 0,
  setBalance: (balance) => set({ balance }),
  updateAfterSpend: (cost, newBalance) =>
    set((state) => ({
      balance: newBalance,
      totalSpent: state.totalSpent + cost,
      actionCount: state.actionCount + 1,
    })),
}))
