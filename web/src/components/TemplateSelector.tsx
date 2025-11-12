import React, { useState } from 'react'
import { Template, applyTemplate } from '../api'

interface TemplateSelectorProps {
  templates: Template[]
  categories: string[]
  isLoading: boolean
  templatesLoading: boolean
  seed?: number
  biome?: string
  onTemplateApplied: () => void
}

export default function TemplateSelector({
  templates,
  categories,
  isLoading,
  templatesLoading,
  seed,
  biome,
  onTemplateApplied
}: TemplateSelectorProps) {
  const [showTemplates, setShowTemplates] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [preciseMode, setPreciseMode] = useState<Record<string, boolean>>({})

  // Group templates: separate base templates from precise versions
  const baseTemplates = templates.filter(t => !t.id.endsWith('_precise'))
  const preciseTemplatesMap = new Map<string, Template>()
  templates.filter(t => t.id.endsWith('_precise')).forEach(t => {
    const baseId = t.id.replace('_precise', '')
    preciseTemplatesMap.set(baseId, t)
  })

  // Filter base templates by category
  const filteredTemplates = selectedCategory
    ? baseTemplates.filter(t => t.category === selectedCategory)
    : baseTemplates

  async function handleApplyTemplate(templateId: string) {
    try {
      await applyTemplate(templateId, seed, biome !== 'desert' ? biome : undefined)
      setShowTemplates(false)
      onTemplateApplied()
    } catch (error) {
      console.error('Failed to apply template:', error)
      throw error // Re-throw so parent can handle
    }
  }

  const btn: React.CSSProperties = {
    background: '#1f6feb',
    color: '#fff',
    border: 'none',
    padding: '8px 12px',
    borderRadius: 8,
    cursor: 'pointer'
  }

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
    <>
      <button
        onClick={() => setShowTemplates(!showTemplates)}
        disabled={templatesLoading}
        style={{
          ...btn,
          background: showTemplates ? '#1f6feb' : '#2a2a2a',
          border: '1px solid #444',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 8,
          fontSize: 13,
          opacity: templatesLoading ? 0.5 : 1,
          cursor: templatesLoading ? 'wait' : 'pointer'
        }}
      >
        <span>🗺️</span>
        <span>Templates {templates.length > 0 && `(${templates.length})`}</span>
      </button>

      {showTemplates && (
        <div style={{
          padding: '12px',
          background: '#111',
          borderRadius: 8,
          border: '1px solid #333',
          maxHeight: '400px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: 8
        }}>
          <div style={{ fontSize: 14, fontWeight: 'bold', color: '#ddd', marginBottom: 4 }}>
            Terrain Templates
          </div>
          
          {/* Category Filter */}
          {categories.length > 0 && (
            <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 8 }}>
              <button
                onClick={() => setSelectedCategory('')}
                style={{
                  ...presetBtn,
                  background: selectedCategory === '' ? '#1f6feb' : '#2a2a2a',
                  fontSize: 11
                }}
              >
                All
              </button>
              {categories.map(cat => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  style={{
                    ...presetBtn,
                    background: selectedCategory === cat ? '#1f6feb' : '#2a2a2a',
                    fontSize: 11,
                    textTransform: 'capitalize'
                  }}
                >
                  {cat}
                </button>
              ))}
            </div>
          )}

          {/* Template List */}
          {templatesLoading ? (
            <div style={{ color: '#aaa', fontSize: 12, textAlign: 'center', padding: '20px' }}>
              Loading templates...
            </div>
          ) : filteredTemplates.length === 0 ? (
            <div style={{ color: '#aaa', fontSize: 12, textAlign: 'center', padding: '20px' }}>
              No templates found
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {filteredTemplates.map(template => {
                const hasPreciseVersion = preciseTemplatesMap.has(template.id)
                const isPrecise = preciseMode[template.id] || false
                const preciseTemplate = preciseTemplatesMap.get(template.id)
                const activeTemplate = isPrecise && preciseTemplate ? preciseTemplate : template
                
                return (
                  <div
                    key={template.id}
                    style={{
                      padding: '12px',
                      background: '#1a1a1a',
                      borderRadius: 6,
                      border: '1px solid #333',
                      transition: 'background 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = '#252525'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = '#1a1a1a'
                    }}
                  >
                    <div style={{ fontSize: 13, fontWeight: 'bold', color: '#ddd', marginBottom: 4 }}>
                      {template.name}
                    </div>
                    <div style={{ fontSize: 11, color: '#aaa', marginBottom: 8, lineHeight: 1.4 }}>
                      {template.description}
                    </div>
                    
                    {/* Precise Mode Toggle */}
                    {hasPreciseVersion && (
                      <div style={{
                        marginBottom: 10,
                        padding: '10px',
                        background: isPrecise ? '#1a3a1a' : '#2a1a1a',
                        borderRadius: 6,
                        border: isPrecise ? '1px solid #4CAF50' : '1px solid #444',
                        cursor: 'pointer'
                      }}
                      onClick={(e) => {
                        e.stopPropagation()
                        setPreciseMode({ ...preciseMode, [template.id]: !isPrecise })
                      }}
                      >
                        <label style={{
                          display: 'flex',
                          alignItems: 'flex-start',
                          gap: 10,
                          cursor: 'pointer',
                          fontSize: 11
                        }}>
                          <input
                            type="checkbox"
                            checked={isPrecise}
                            onChange={(e) => {
                              e.stopPropagation()
                              setPreciseMode({ ...preciseMode, [template.id]: e.target.checked })
                            }}
                            onClick={(e) => e.stopPropagation()}
                            style={{ cursor: 'pointer', marginTop: 2, flexShrink: 0 }}
                          />
                          <div style={{ flex: 1 }}>
                            <div style={{ 
                              color: isPrecise ? '#4CAF50' : '#ddd', 
                              fontWeight: 'bold', 
                              marginBottom: 4,
                              display: 'flex',
                              alignItems: 'center',
                              gap: 6
                            }}>
                              <span>🎯</span>
                              <span>Precise Mode {isPrecise && '✓'}</span>
                            </div>
                            <div style={{ color: '#aaa', fontSize: 10, lineHeight: 1.5 }}>
                              {isPrecise ? (
                                <>
                                  <strong style={{ color: '#4CAF50' }}>Using pre-composed JSON actions</strong> — 
                                  Bypasses the semantic parser for <strong>deterministic, reproducible</strong> results. 
                                  Same terrain every time, perfect for testing and consistent generation.
                                </>
                              ) : (
                                <>
                                  <strong style={{ color: '#FFA726' }}>Using natural language commands</strong> — 
                                  Parsed by LLM for flexible interpretation. More natural but results may vary slightly between runs.
                                </>
                              )}
                            </div>
                          </div>
                        </label>
                      </div>
                    )}
                    
                    <div style={{ display: 'flex', gap: 6, alignItems: 'center', fontSize: 10, color: '#888', marginBottom: 10 }}>
                      <span style={{
                        background: '#2a2a2a',
                        padding: '2px 6px',
                        borderRadius: 3,
                        textTransform: 'capitalize'
                      }}>
                        {template.category}
                      </span>
                      <span>•</span>
                      <span>
                        {activeTemplate.format === 'actions' ? 'JSON Actions' : 'Natural Language'} 
                        ({activeTemplate.format === 'actions' ? activeTemplate.action_count : activeTemplate.command_count})
                      </span>
                      {isPrecise && hasPreciseVersion && (
                        <>
                          <span>•</span>
                          <span style={{ color: '#4CAF50', fontWeight: 'bold' }}>🎯 Precise</span>
                        </>
                      )}
                    </div>
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        const templateId = isPrecise && preciseTemplate ? preciseTemplate.id : template.id
                        handleApplyTemplate(templateId)
                      }}
                      disabled={isLoading}
                      style={{
                        ...btn,
                        width: '100%',
                        fontSize: 12,
                        padding: '10px',
                        background: isPrecise ? '#4CAF50' : '#1f6feb',
                        fontWeight: 'bold',
                        opacity: isLoading ? 0.5 : 1,
                        cursor: isLoading ? 'not-allowed' : 'pointer'
                      }}
                    >
                      {isPrecise ? '🎯 Apply Precise Template' : '✨ Apply Template'}
                    </button>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
    </>
  )
}

