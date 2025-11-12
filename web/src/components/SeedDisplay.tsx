
interface SeedDisplayProps {
  seed: number
  onSeedChange: (seed: number) => void
  lastGeneratedSeed?: number | null  // Last actual seed used when seed=-1
  disabled?: boolean
}

export default function SeedDisplay({ seed, onSeedChange, lastGeneratedSeed = null, disabled = false }: SeedDisplayProps) {
  return (
    <div style={{ padding: '12px', background: '#111', borderRadius: 8, border: '1px solid #333' }}>
      <div style={{ fontSize: 14, fontWeight: 'bold', marginBottom: 8, color: '#ddd' }}>
        🌱 Seed
      </div>
      
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <input
          type="number"
          value={seed}
          onChange={(e) => {
            const val = e.target.value === '' ? -1 : parseInt(e.target.value)
            if (!isNaN(val)) {
              onSeedChange(val)
            }
          }}
          disabled={disabled}
          style={{
            flex: 1,
            background: '#1a1a1a',
            color: '#ddd',
            border: '1px solid #444',
            borderRadius: 4,
            padding: '6px 8px',
            fontSize: 13,
            cursor: disabled ? 'not-allowed' : 'text'
          }}
          min={-1}
          max={2147483647}
        />
        <button
          onClick={() => {
            onSeedChange(-1)  // Set to auto mode
          }}
          disabled={disabled}
          style={{
            background: seed === -1 ? '#4a4a4a' : '#2a2a2a',
            color: '#ddd',
            border: '1px solid #444',
            padding: '6px 12px',
            borderRadius: 4,
            cursor: disabled ? 'not-allowed' : 'pointer',
            fontSize: 12,
            whiteSpace: 'nowrap'
          }}
          title={seed === -1 ? 'Auto mode (random seed each time)' : 'Set to auto mode (random seed)'}
        >
          {seed === -1 ? '🎲 Auto' : '🎲 Random'}
        </button>
      </div>
      
      <div style={{ fontSize: 10, opacity: 0.6, marginTop: 8, color: '#aaa' }}>
        {seed === -1 
          ? lastGeneratedSeed !== null
            ? `Auto mode: Last generated seed was ${lastGeneratedSeed}`
            : 'Auto mode: Random seed generated each time'
          : 'Seed controls terrain generation. Same seed = same terrain. Use -1 for auto mode.'}
      </div>
    </div>
  )
}

