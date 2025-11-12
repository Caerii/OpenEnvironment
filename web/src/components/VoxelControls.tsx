import React from 'react'

interface VoxelControlsProps {
  voxelMode: boolean
  voxelResolution: number
  onVoxelModeChange: (enabled: boolean) => void
  onVoxelResolutionChange: (resolution: number) => void
}

export default function VoxelControls({
  voxelMode,
  voxelResolution,
  onVoxelModeChange,
  onVoxelResolutionChange
}: VoxelControlsProps) {
  return (
    <>
      <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, color: '#ddd' }}>
        <input
          type="checkbox"
          checked={voxelMode}
          onChange={e => onVoxelModeChange(e.target.checked)}
          style={{ cursor: 'pointer' }}
        />
        <span>Generate & View Voxel Terrain</span>
      </label>
      
      {voxelMode && (
        <div style={{ padding: '12px', background: '#111', borderRadius: 8, border: '1px solid #333' }}>
          <div style={{ fontSize: 14, fontWeight: 'bold', marginBottom: 8, color: '#ddd' }}>🧊 Voxel Resolution</div>
          
          <div style={{ marginBottom: 8 }}>
            <label style={{ display: 'block', fontSize: 12, marginBottom: 4, color: '#aaa' }}>
              Resolution: {voxelResolution}³ <span style={{ opacity: 0.6 }}>
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
              onChange={e => onVoxelResolutionChange(Number(e.target.value))}
              style={{ width: '100%', cursor: 'pointer' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, opacity: 0.5, marginTop: 2 }}>
              <span>128 (Low)</span>
              <span>512 (High)</span>
              <span>2048 (Ultra)</span>
            </div>
          </div>
          
          <div style={{ fontSize: 10, opacity: 0.6, marginTop: 8 }}>
            ⚠️ Higher resolutions increase generation time and memory usage
          </div>
        </div>
      )}
    </>
  )
}

