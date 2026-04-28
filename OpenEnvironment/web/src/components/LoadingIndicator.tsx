import React from 'react'

interface LoadingIndicatorProps {
  isLoading: boolean
  message?: string
}

export default function LoadingIndicator({ isLoading, message = 'Generating terrain...' }: LoadingIndicatorProps) {
  if (!isLoading) return null

  return (
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
      <span>{message}</span>
    </div>
  )
}

