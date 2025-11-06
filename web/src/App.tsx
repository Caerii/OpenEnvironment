import { useState, useEffect } from 'react'
import { postCommand, modifyCommand, resetTerrain, regenerateTerrain, getServerStatus, listTemplates, Template } from './api'
import { useStore } from './state'
import TerrainViewer from './components/TerrainViewer'
import ApiKeyWarning from './components/ApiKeyWarning'
import TemplateSelector from './components/TemplateSelector'
import SeedDisplay from './components/SeedDisplay'
import BiomeSelector from './components/BiomeSelector'
import VoxelControls from './components/VoxelControls'
import SunControls from './components/SunControls'
import TerrainControls from './components/TerrainControls'
import LoadingIndicator from './components/LoadingIndicator'

export default function App() {
  const [input, setInput] = useState('create a desert with rolling dunes and two mountains on the left')
  const { 
    setAssets, setStateJson, assets, voxelMode, setVoxelMode,
    sunAzimuth, sunElevation, setSunAzimuth, setSunElevation,
    voxelResolution, setVoxelResolution, seed, setSeed, biome, setBiome,
    lastGeneratedSeed, setLastGeneratedSeed
  } = useStore()
  const [isLoading, setIsLoading] = useState(false)
  const [apiKeyStatus, setApiKeyStatus] = useState<{ configured: boolean; checked: boolean }>({ configured: true, checked: false })
  const [templates, setTemplates] = useState<Template[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [templatesLoading, setTemplatesLoading] = useState(false)

  // Check API key status on mount
  useEffect(() => {
    async function checkApiKeyStatus() {
      try {
        const status = await getServerStatus()
        setApiKeyStatus({ configured: status.cerebras_api_key_configured, checked: true })
      } catch (error) {
        console.error('Failed to check API key status:', error)
        setApiKeyStatus({ configured: false, checked: true })
      }
    }
    checkApiKeyStatus()
  }, [])

  // Load templates on mount
  useEffect(() => {
    async function loadTemplates() {
      try {
        setTemplatesLoading(true)
        const response = await listTemplates()
        setTemplates(response.templates)
        setCategories(response.categories)
      } catch (error) {
        console.error('Failed to load templates:', error)
      } finally {
        setTemplatesLoading(false)
      }
    }
    loadTemplates()
  }, [])

  // Auto-load last terrain on mount
  useEffect(() => {
    async function loadLastTerrain() {
      try {
        setIsLoading(true)
        const res = await regenerateTerrain(voxelMode, voxelResolution)
        setAssets(res.assets)
        setStateJson(res.state)
        // Update seed from state if available, but preserve -1 if in auto mode
        if (res.state?.seed !== undefined) {
          if (seed === -1) {
            // In auto mode, just store the generated seed for display
            setLastGeneratedSeed(res.state.seed)
          } else {
            setSeed(res.state.seed)
            setLastGeneratedSeed(null)
          }
        }
      } catch (error) {
        console.error('Failed to load last terrain:', error)
      } finally {
        setIsLoading(false)
      }
    }
    loadLastTerrain()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // Empty deps = run once on mount (setAssets/setStateJson are stable)

  // Auto-regenerate when voxel mode or resolution is toggled
  useEffect(() => {
    // Only regenerate if we have existing state (not on initial mount)
    if (!assets) return
    
    async function regenerateWithVoxelSettings() {
      setIsLoading(true)
      try {
        // Regenerate current terrain state with the new voxel settings
        const res = await regenerateTerrain(voxelMode, voxelResolution)
        setAssets(res.assets)
        setStateJson(res.state)
        // Update seed from state if available, but preserve -1 if in auto mode
        if (res.state?.seed !== undefined) {
          if (seed === -1) {
            // In auto mode, just store the generated seed for display
            setLastGeneratedSeed(res.state.seed)
          } else {
            setSeed(res.state.seed)
            setLastGeneratedSeed(null)
          }
        }
      } catch (error) {
        console.error('Failed to regenerate with voxel settings:', error)
      } finally {
        setIsLoading(false)
      }
    }
    
    regenerateWithVoxelSettings()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [voxelMode, voxelResolution]) // Regenerate when voxel mode or resolution changes

  async function send(kind: 'gen' | 'mod') {
    setIsLoading(true)
    try {
      const fn = kind === 'gen' ? postCommand : modifyCommand
      const res = await fn(input, voxelMode, voxelResolution, seed, biome !== 'desert' ? biome : undefined)
      setAssets(res.assets)
      setStateJson(res.state)
      // If seed is -1, preserve it but store the generated seed for display
      if (seed === -1 && res.state?.seed !== undefined) {
        setLastGeneratedSeed(res.state.seed)
        // Keep seed at -1 for next time
      } else if (res.state?.seed !== undefined) {
        // Update seed from state if not in auto mode
        setSeed(res.state.seed)
        setLastGeneratedSeed(null)  // Clear last generated seed when not in auto mode
      }
      // Update voxel mode in store if voxel assets are present
      if (res.assets.voxel_obj) {
        setVoxelMode(true)
      }
    } finally {
      setIsLoading(false)
    }
  }

  async function reset() {
    setIsLoading(true)
    try {
      const res = await resetTerrain(seed, biome !== 'desert' ? biome : undefined)
      setAssets(res.assets)
      setStateJson(res.state)
      // If seed is -1, preserve it but store the generated seed for display
      if (seed === -1 && res.state?.seed !== undefined) {
        setLastGeneratedSeed(res.state.seed)
        // Keep seed at -1 for next time
      } else if (res.state?.seed !== undefined) {
        // Update seed from state if not in auto mode
        setSeed(res.state.seed)
        setLastGeneratedSeed(null)  // Clear last generated seed when not in auto mode
      }
      setInput('') // Clear input
    } finally {
      setIsLoading(false)
    }
  }


  return (
    <div style={{ display:'grid', gridTemplateColumns:'1fr 380px', height:'100vh' }}>
      <div><TerrainViewer /></div>
      <div style={{ padding:'16px', borderLeft:'1px solid #222', display:'flex', flexDirection:'column', gap:'12px' }}>
        <h2 style={{ margin:0 }}>Semantic Terrain</h2>
        
        <TemplateSelector
          templates={templates}
          categories={categories}
          isLoading={isLoading}
          templatesLoading={templatesLoading}
          seed={seed}
          biome={biome}
          onTemplateApplied={() => {}}
        />
        
        <ApiKeyWarning configured={apiKeyStatus.configured} checked={apiKeyStatus.checked} />
        
        <SeedDisplay 
          seed={seed} 
          onSeedChange={(newSeed) => {
            setSeed(newSeed)
            // Clear last generated seed if user changes away from auto mode
            if (newSeed !== -1) {
              setLastGeneratedSeed(null)
            }
          }} 
          lastGeneratedSeed={lastGeneratedSeed} 
          disabled={isLoading} 
        />
        
        <BiomeSelector biome={biome} onBiomeChange={setBiome} disabled={isLoading} />
        
        <TerrainControls
          input={input}
          onInputChange={setInput}
          isLoading={isLoading}
          onGenerate={() => send('gen')}
          onModify={() => send('mod')}
          onReset={reset}
        />
        
        <VoxelControls
          voxelMode={voxelMode}
          voxelResolution={voxelResolution}
          onVoxelModeChange={setVoxelMode}
          onVoxelResolutionChange={setVoxelResolution}
        />
        
        <SunControls
          sunAzimuth={sunAzimuth}
          sunElevation={sunElevation}
          onAzimuthChange={setSunAzimuth}
          onElevationChange={setSunElevation}
        />
        
        <LoadingIndicator isLoading={isLoading} />
        
        {/* No Terrain Loaded Message */}
        {!isLoading && !assets && (
          <div style={{ 
            padding: '12px', 
            background: '#ffaa0022', 
            border: '1px solid #ffaa00', 
            borderRadius: 8, 
            fontSize: 13,
            color: '#ffaa00'
          }}>
            ⚠️ No terrain loaded. Click "Generate" to create terrain or check if server is running.
          </div>
        )}
      </div>
    </div>
  )
}
