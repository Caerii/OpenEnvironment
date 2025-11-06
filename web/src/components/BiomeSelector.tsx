import React from 'react'

interface BiomeSelectorProps {
  biome: string
  onBiomeChange: (biome: string) => void
  disabled?: boolean
}

const BIOMES = [
  { value: 'flat', label: 'Flat', description: 'Gently rolling base terrain' },
  { value: 'desert', label: 'Desert', description: 'Low, mostly flat, dune-friendly' },
  { value: 'forest', label: 'Forest', description: 'Slightly rolling hills' },
  { value: 'arctic', label: 'Arctic', description: 'Cold, smooth, glacier-friendly' }
]

export default function BiomeSelector({ biome, onBiomeChange, disabled = false }: BiomeSelectorProps) {
  return (
    <div style={{ padding: '12px', background: '#111', borderRadius: 8, border: '1px solid #333' }}>
      <div style={{ fontSize: 14, fontWeight: 'bold', marginBottom: 8, color: '#ddd' }}>
        🌍 Base Biome
      </div>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {BIOMES.map(b => (
          <label
            key={b.value}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px',
              background: biome === b.value ? '#1a3a1a' : '#1a1a1a',
              borderRadius: 6,
              border: biome === b.value ? '1px solid #4CAF50' : '1px solid #333',
              cursor: disabled ? 'not-allowed' : 'pointer',
              opacity: disabled ? 0.5 : 1
            }}
          >
            <input
              type="radio"
              name="biome"
              value={b.value}
              checked={biome === b.value}
              onChange={(e) => onBiomeChange(e.target.value)}
              disabled={disabled}
              style={{ cursor: disabled ? 'not-allowed' : 'pointer' }}
            />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 13, fontWeight: 'bold', color: '#ddd' }}>
                {b.label}
              </div>
              <div style={{ fontSize: 11, color: '#aaa' }}>
                {b.description}
              </div>
            </div>
          </label>
        ))}
      </div>
      
      <div style={{ fontSize: 10, opacity: 0.6, marginTop: 8, color: '#aaa' }}>
        Base biome sets the starting terrain before features are added.
      </div>
    </div>
  )
}

