import { create } from 'zustand'

type Assets = { 
  height8: string
  height16: string
  splat: string
  voxel_obj?: string
  voxel_bin?: string
}

type Store = {
  assets: Assets | null
  stateJson: any | null
  voxelMode: boolean
  sunAzimuth: number    // Sun angle around horizon (0-360 degrees)
  sunElevation: number  // Sun height above horizon (0-90 degrees)
  voxelResolution: number  // Voxel grid resolution (128-2048)
  seed: number  // Terrain generation seed
  biome: string  // Base biome type ('desert', 'forest', 'arctic', 'flat')
  lastGeneratedSeed: number | null  // Last actual seed used when seed=-1 (for display only)
  autoRefresh: boolean  // Auto-refresh enabled (polls backend for changes)
  setAssets: (a: Assets | null) => void
  setStateJson: (s: any | null) => void
  setVoxelMode: (v: boolean) => void
  setSunAzimuth: (a: number) => void
  setSunElevation: (e: number) => void
  setVoxelResolution: (r: number) => void
  setSeed: (s: number) => void
  setBiome: (b: string) => void
  setLastGeneratedSeed: (s: number | null) => void
  setAutoRefresh: (a: boolean) => void
}

export const useStore = create<Store>((set) => ({
  assets: null,
  stateJson: null,
  voxelMode: false,
  sunAzimuth: 82,      // Default: 82° - sunrise/sunset angle
  sunElevation: 5,     // Default: 5° above horizon - low sun for dramatic lighting
  voxelResolution: 256, // Default: 256x256x256 voxel grid (good balance)
  seed: -1,  // Default seed (-1 = auto-generate random seed)
  biome: 'desert',  // Default biome
  lastGeneratedSeed: null,  // Last actual seed used when seed=-1 (for display only)
  autoRefresh: false,  // Default: auto-refresh disabled (enable for Postman workflow)
  setAssets: (a) => set({ assets: a }),
  setStateJson: (s) => set({ stateJson: s }),
  setVoxelMode: (v) => set({ voxelMode: v }),
  setSunAzimuth: (a) => set({ sunAzimuth: a }),
  setSunElevation: (e) => set({ sunElevation: e }),
  setVoxelResolution: (r) => set({ voxelResolution: r }),
  setSeed: (s) => set({ seed: s }),
  setBiome: (b) => set({ biome: b }),
  setLastGeneratedSeed: (s) => set({ lastGeneratedSeed: s }),
  setAutoRefresh: (a) => set({ autoRefresh: a })
}))

