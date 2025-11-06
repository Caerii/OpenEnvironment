import React from 'react'

interface TerrainControlsProps {
  input: string
  onInputChange: (value: string) => void
  isLoading: boolean
  onGenerate: () => void
  onModify: () => void
  onReset: () => void
}

export default function TerrainControls({
  input,
  onInputChange,
  isLoading,
  onGenerate,
  onModify,
  onReset
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
      
      <div style={{ display: 'flex', gap: 8 }}>
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
    </>
  )
}

