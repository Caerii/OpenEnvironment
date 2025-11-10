import React from 'react'

interface TerrainControlsProps {
  input: string
  onInputChange: (value: string) => void
  isLoading: boolean
  onGenerate: () => void
  onModify: () => void
  onReset: () => void
  onRefresh: () => void
  autoRefresh: boolean
  onAutoRefreshToggle: (enabled: boolean) => void
}

export default function TerrainControls({
  input,
  onInputChange,
  isLoading,
  onGenerate,
  onModify,
  onReset,
  onRefresh,
  autoRefresh,
  onAutoRefreshToggle
}: TerrainControlsProps) {
  const btn: React.CSSProperties = {
    background: '#1f6feb',
    color: '#fff',
    border: 'none',
    padding: '8px 12px',
    borderRadius: 8,
    cursor: 'pointer'
  }

  const btnDisabled: React.CSSProperties = {
    ...btn,
    opacity: 0.5,
    cursor: 'not-allowed'
  }

  return (
    <>
      <textarea
        value={input}
        onChange={e => onInputChange(e.target.value)}
        rows={6}
        style={{ width: '100%', background: '#111', color: '#ddd', border: '1px solid #333', borderRadius: 8, padding: 8 }}
        placeholder='e.g., "add a valley in the center"'
      />
      
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button onClick={onGenerate} disabled={isLoading} style={isLoading ? btnDisabled : btn}>
          Generate
        </button>
        <button onClick={onModify} disabled={isLoading} style={isLoading ? btnDisabled : btn}>
          Modify
        </button>
        <button onClick={onReset} disabled={isLoading} style={isLoading ? {...btnDisabled, background: '#d32f2f'} : {...btn, background: '#d32f2f'}}>
          Reset
        </button>
      </div>
      
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        <button 
          onClick={onRefresh} 
          disabled={isLoading} 
          style={isLoading ? {...btnDisabled, background: '#388e3c'} : {...btn, background: '#388e3c'}}
          title="Sync with backend (useful after Postman/API calls)"
        >
          🔄 Refresh
        </button>
        
        <button
          onClick={() => onAutoRefreshToggle(!autoRefresh)}
          disabled={isLoading}
          style={isLoading ? {...btnDisabled, background: autoRefresh ? '#ff9800' : '#757575'} : {...btn, background: autoRefresh ? '#ff9800' : '#757575'}}
          title={autoRefresh ? "Auto-refresh ON (polls every 2s)" : "Auto-refresh OFF (manual only)"}
        >
          {autoRefresh ? '⚡ Auto ON' : '⏸️ Auto OFF'}
        </button>
        
        {autoRefresh && (
          <span style={{ color: '#ff9800', fontSize: '12px', fontWeight: 'bold' }}>
            • Polling every 2s
          </span>
        )}
      </div>
    </>
  )
}

