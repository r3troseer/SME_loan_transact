import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface Lender {
  id: number
  name: string
}

interface LenderState {
  currentLender: Lender | null
  setCurrentLender: (lender: Lender) => void
}

// Default lenders (will be fetched from API in real app)
export const LENDERS: Lender[] = [
  { id: 1, name: 'Alpha Bank' },
  { id: 2, name: 'Growth Capital Partners' },
  { id: 3, name: 'Regional Development Fund' },
  { id: 4, name: 'Sector Specialist Credit' },
]

export const useLenderStore = create<LenderState>()(
  persist(
    (set) => ({
      currentLender: LENDERS[0], // Default to first lender
      setCurrentLender: (lender) => set({ currentLender: lender }),
    }),
    {
      name: 'lender-storage',
    }
  )
)
