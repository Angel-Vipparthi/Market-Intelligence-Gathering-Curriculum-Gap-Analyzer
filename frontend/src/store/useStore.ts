import { create } from 'zustand'

interface AppState {
  selectedDigestId: string | null
  selectedGapId: string | null
  sidebarCollapsed: boolean
  setSelectedDigest: (id: string | null) => void
  setSelectedGap: (id: string | null) => void
  toggleSidebar: () => void
}

export const useStore = create<AppState>((set) => ({
  selectedDigestId: null,
  selectedGapId: null,
  sidebarCollapsed: false,
  setSelectedDigest: (id) => set({ selectedDigestId: id }),
  setSelectedGap: (id) => set({ selectedGapId: id }),
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
}))
