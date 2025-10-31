import { useState, useEffect } from 'react'
import { postCommand, modifyCommand, resetTerrain, regenerateTerrain } from './api'
import { useStore } from './state'
import TerrainViewer from './components/TerrainViewer'

export default function App() {
  const [input, setInput] = useState('create a desert with rolling dunes and two mountains on the left')
  const { 
    setAssets, setStateJson, assets, voxelMode, setVoxelMode,
    sunAzimuth, sunElevation, setSunAzimuth, setSunElevation,
    voxelResolution, setVoxelResolution
  } = useStore()
  const [isLoading, setIsLoading] = useState(false)

  // Auto-load last terrain on mount
  useEffect(() => {
    async function loadLastTerrain() {
      try {
        setIsLoading(true)
        const res = await regenerateTerrain(voxelMode, voxelResolution)
        setAssets(res.assets)
        setStateJson(res.state)
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
      const res = await fn(input, voxelMode, voxelResolution)
      setAssets(res.assets)
      setStateJson(res.state)
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
      const res = await resetTerrain()
      setAssets(res.assets)
      setStateJson(res.state)
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
        <textarea
          value={input}
          onChange={e=>setInput(e.target.value)}
          rows={6}
          style={{ width:'100%', background:'#111', color:'#ddd', border:'1px solid #333', borderRadius:8, padding:8 }}
          placeholder='e.g., "add a valley in the center"'
        />
        <label style={{ display:'flex', alignItems:'center', gap:8, fontSize:14, color:'#ddd' }}>
          <input
            type="checkbox"
            checked={voxelMode}
            onChange={e=>setVoxelMode(e.target.checked)}
            style={{ cursor:'pointer' }}
          />
          <span>Generate & View Voxel Terrain</span>
        </label>
        
        {/* Voxel Resolution Slider */}
        {voxelMode && (
          <div style={{ padding:'12px', background:'#111', borderRadius:8, border:'1px solid #333' }}>
            <div style={{ fontSize:14, fontWeight:'bold', marginBottom:8, color:'#ddd' }}>🧊 Voxel Resolution</div>
            
            <div style={{ marginBottom:8 }}>
              <label style={{ display:'block', fontSize:12, marginBottom:4, color:'#aaa' }}>
                Resolution: {voxelResolution}³ <span style={{ opacity:0.6 }}>
                  ({Math.pow(voxelResolution, 3).toLocaleString()} voxels, 
                  {voxelResolution <= 128 ? ' Low' : 
                   voxelResolution <= 256 ? ' Medium' : 
                   voxelResolution <= 512 ? ' High' : 
                   voxelResolution <= 1024 ? ' Very High' : ' Ultra'})
                </span>
              </label>
              <input
                type="range"
                min="128"
                max="2048"
                step="128"
                value={voxelResolution}
                onChange={e=>setVoxelResolution(Number(e.target.value))}
                style={{ width:'100%', cursor:'pointer' }}
              />
              <div style={{ display:'flex', justifyContent:'space-between', fontSize:10, opacity:0.5, marginTop:2 }}>
                <span>128 (Low)</span>
                <span>512 (High)</span>
                <span>2048 (Ultra)</span>
              </div>
            </div>
            
            <div style={{ fontSize:10, opacity:0.6, marginTop:8 }}>
              ⚠️ Higher resolutions increase generation time and memory usage
            </div>
          </div>
        )}
        
        {/* Sun Position Controls */}
        <div style={{ padding:'12px', background:'#111', borderRadius:8, border:'1px solid #333' }}>
          <div style={{ fontSize:14, fontWeight:'bold', marginBottom:8, color:'#ddd' }}>☀️ Sun Position</div>
          
          <div style={{ marginBottom:8 }}>
            <label style={{ display:'block', fontSize:12, marginBottom:4, color:'#aaa' }}>
              Azimuth: {sunAzimuth}° <span style={{ opacity:0.6 }}>
                ({sunAzimuth === 0 ? 'N' : 
                  sunAzimuth === 45 ? 'NE' : 
                  sunAzimuth === 90 ? 'E' : 
                  sunAzimuth === 135 ? 'SE' : 
                  sunAzimuth === 180 ? 'S' : 
                  sunAzimuth === 225 ? 'SW' : 
                  sunAzimuth === 270 ? 'W' : 
                  sunAzimuth === 315 ? 'NW' : ''})
              </span>
            </label>
            <input
              type="range"
              min="0"
              max="360"
              step="1"
              value={sunAzimuth}
              onChange={e=>setSunAzimuth(Number(e.target.value))}
              style={{ width:'100%', cursor:'pointer' }}
            />
            <div style={{ display:'flex', justifyContent:'space-between', fontSize:10, opacity:0.5, marginTop:2 }}>
              <span>N (0°)</span>
              <span>E (90°)</span>
              <span>S (180°)</span>
              <span>W (270°)</span>
            </div>
          </div>
          
          <div style={{ marginBottom:8 }}>
            <label style={{ display:'block', fontSize:12, marginBottom:4, color:'#aaa' }}>
              Elevation: {sunElevation}° <span style={{ opacity:0.6 }}>
                ({sunElevation <= 10 ? 'Sunrise/Sunset' : 
                  sunElevation <= 30 ? 'Low' : 
                  sunElevation <= 60 ? 'Mid' : 
                  sunElevation <= 85 ? 'High' : 'Overhead'})
              </span>
            </label>
            <input
              type="range"
              min="5"
              max="90"
              step="1"
              value={sunElevation}
              onChange={e=>setSunElevation(Number(e.target.value))}
              style={{ width:'100%', cursor:'pointer' }}
            />
            <div style={{ display:'flex', justifyContent:'space-between', fontSize:10, opacity:0.5, marginTop:2 }}>
              <span>Horizon (5°)</span>
              <span>Mid (45°)</span>
              <span>Overhead (90°)</span>
            </div>
          </div>
          
          {/* Quick Presets */}
          <div style={{ fontSize:11, marginTop:12, paddingTop:8, borderTop:'1px solid #333' }}>
            <div style={{ opacity:0.7, marginBottom:4 }}>Presets:</div>
            <div style={{ display:'flex', gap:4, flexWrap:'wrap' }}>
              <button onClick={()=>{setSunAzimuth(135);setSunElevation(60)}} style={presetBtn}>Morning</button>
              <button onClick={()=>{setSunAzimuth(180);setSunElevation(70)}} style={presetBtn}>Noon</button>
              <button onClick={()=>{setSunAzimuth(225);setSunElevation(20)}} style={presetBtn}>Evening</button>
              <button onClick={()=>{setSunAzimuth(90);setSunElevation(10)}} style={presetBtn}>Sunrise</button>
            </div>
          </div>
        </div>
        
        <div style={{ display:'flex', gap:8 }}>
          <button onClick={()=>send('gen')} disabled={isLoading} style={isLoading ? btnDisabled : btn}>Generate</button>
          <button onClick={()=>send('mod')} disabled={isLoading} style={isLoading ? btnDisabled : btn}>Modify</button>
          <button onClick={reset} disabled={isLoading} style={isLoading ? {...btnDisabled, background:'#d32f2f'} : {...btn, background:'#d32f2f'}}>Reset</button>
        </div>
        
        {/* Loading Indicator */}
        {isLoading && (
          <div style={{ 
            padding: '12px', 
            background: '#1f6feb22', 
            border: '1px solid #1f6feb', 
            borderRadius: 8, 
            fontSize: 13,
            color: '#1f6feb',
            display: 'flex',
            alignItems: 'center',
            gap: 8
          }}>
            <div style={{ 
              width: 12, 
              height: 12, 
              border: '2px solid #1f6feb', 
              borderTop: '2px solid transparent',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }} />
            <span>Generating terrain...</span>
          </div>
        )}
        
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
        
        <div style={{ fontSize:12, opacity:0.8 }}>
          <p>Latest assets:</p>
          <code style={{ display:'block', wordBreak:'break-all', maxHeight: 200, overflow: 'auto' }}>
            {assets ? JSON.stringify(assets, null, 2) : 'No terrain loaded yet'}
          </code>
        </div>
      </div>
    </div>
  )
}

const btn: React.CSSProperties = {
  background:'#1f6feb', color:'#fff', border:'none', padding:'8px 12px',
  borderRadius:8, cursor:'pointer'
}

const btnDisabled: React.CSSProperties = {
  ...btn,
  opacity: 0.5,
  cursor: 'not-allowed'
}

const presetBtn: React.CSSProperties = {
  background:'#2a2a2a', 
  color:'#ddd', 
  border:'1px solid #444', 
  padding:'4px 8px',
  borderRadius:4, 
  cursor:'pointer',
  fontSize:11
}

