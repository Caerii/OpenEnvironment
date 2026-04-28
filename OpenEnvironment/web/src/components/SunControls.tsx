import React from 'react'

interface SunControlsProps {
  sunAzimuth: number
  sunElevation: number
  onAzimuthChange: (azimuth: number) => void
  onElevationChange: (elevation: number) => void
}

export default function SunControls({
  sunAzimuth,
  sunElevation,
  onAzimuthChange,
  onElevationChange
}: SunControlsProps) {
  const presetBtn: React.CSSProperties = {
    background: '#2a2a2a',
    color: '#ddd',
    border: '1px solid #444',
    padding: '4px 8px',
    borderRadius: 4,
    cursor: 'pointer',
    fontSize: 11
  }

  return (
    <div style={{ padding: '12px', background: '#111', borderRadius: 8, border: '1px solid #333' }}>
      <div style={{ fontSize: 14, fontWeight: 'bold', marginBottom: 8, color: '#ddd' }}>☀️ Sun Position</div>
      
      <div style={{ marginBottom: 8 }}>
        <label style={{ display: 'block', fontSize: 12, marginBottom: 4, color: '#aaa' }}>
          Azimuth: {sunAzimuth}° <span style={{ opacity: 0.6 }}>
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
          onChange={e => onAzimuthChange(Number(e.target.value))}
          style={{ width: '100%', cursor: 'pointer' }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, opacity: 0.5, marginTop: 2 }}>
          <span>N (0°)</span>
          <span>E (90°)</span>
          <span>S (180°)</span>
          <span>W (270°)</span>
        </div>
      </div>
      
      <div style={{ marginBottom: 8 }}>
        <label style={{ display: 'block', fontSize: 12, marginBottom: 4, color: '#aaa' }}>
          Elevation: {sunElevation}° <span style={{ opacity: 0.6 }}>
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
          onChange={e => onElevationChange(Number(e.target.value))}
          style={{ width: '100%', cursor: 'pointer' }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, opacity: 0.5, marginTop: 2 }}>
          <span>Horizon (5°)</span>
          <span>Mid (45°)</span>
          <span>Overhead (90°)</span>
        </div>
      </div>
      
      {/* Quick Presets */}
      <div style={{ fontSize: 11, marginTop: 12, paddingTop: 8, borderTop: '1px solid #333' }}>
        <div style={{ opacity: 0.7, marginBottom: 4 }}>Presets:</div>
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          <button onClick={() => { onAzimuthChange(135); onElevationChange(60) }} style={presetBtn}>Morning</button>
          <button onClick={() => { onAzimuthChange(180); onElevationChange(70) }} style={presetBtn}>Noon</button>
          <button onClick={() => { onAzimuthChange(225); onElevationChange(20) }} style={presetBtn}>Evening</button>
          <button onClick={() => { onAzimuthChange(90); onElevationChange(10) }} style={presetBtn}>Sunrise</button>
        </div>
      </div>
    </div>
  )
}

