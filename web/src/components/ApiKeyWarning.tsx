import React from 'react'

interface ApiKeyWarningProps {
  configured: boolean
  checked: boolean
}

export default function ApiKeyWarning({ configured, checked }: ApiKeyWarningProps) {
  if (!checked || configured) return null

  return (
    <div style={{ 
      padding: '12px', 
      background: '#ff6b6b22', 
      border: '1px solid #ff6b6b', 
      borderRadius: 8, 
      fontSize: 13,
      color: '#ff6b6b'
    }}>
      <div style={{ fontWeight: 'bold', marginBottom: 4 }}>⚠️ Cerebras API Key Not Configured</div>
      <div style={{ fontSize: 12, opacity: 0.9, lineHeight: 1.5 }}>
        The <code style={{ background: '#000', padding: '2px 4px', borderRadius: 3 }}>CEREBRAS_API_KEY</code> environment variable is not set in the server folder.
        <br />
        <br />
        <strong>To fix:</strong>
        <ol style={{ margin: '8px 0 0 0', paddingLeft: '20px', fontSize: 11 }}>
          <li>Create a <code style={{ background: '#000', padding: '2px 4px', borderRadius: 3 }}>.env</code> file in the <code style={{ background: '#000', padding: '2px 4px', borderRadius: 3 }}>server</code> folder</li>
          <li>Add: <code style={{ background: '#000', padding: '2px 4px', borderRadius: 3 }}>CEREBRAS_API_KEY=your_api_key_here</code></li>
          <li>Restart the server</li>
        </ol>
        <div style={{ marginTop: 8, fontSize: 11, opacity: 0.8 }}>
          <strong>Note:</strong> The system will use regex-based parsing (limited features) until the API key is configured.
        </div>
      </div>
    </div>
  )
}

