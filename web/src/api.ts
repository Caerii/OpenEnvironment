import axios from 'axios'

const API = axios.create({ baseURL: 'http://localhost:8001' })

export async function postCommand(text: string, voxel: boolean = false, voxel_resolution: number = 256, seed?: number, biome?: string) {
  const { data } = await API.post('/api/generate', { text, voxel, voxel_resolution, seed, biome })
  return data as { ok: boolean, state: any, assets: {height8:string,height16:string,splat:string,voxel_obj?:string,voxel_bin?:string} }
}

export async function modifyCommand(text: string, voxel: boolean = false, voxel_resolution: number = 256, seed?: number, biome?: string) {
  const { data } = await API.post('/api/modify', { text, voxel, voxel_resolution, seed, biome })
  return data as { ok: boolean, state: any, assets: {height8:string,height16:string,splat:string,voxel_obj?:string,voxel_bin?:string} }
}

export async function fetchState() {
  const { data } = await API.get('/api/state')
  return data
}

export async function resetTerrain(seed?: number, biome?: string) {
  const { data } = await API.post('/api/reset', { seed, biome })
  return data as { ok: boolean, state: any, assets: {height8:string,height16:string,splat:string} }
}

export async function regenerateTerrain(voxel: boolean = false, voxel_resolution: number = 256) {
  const { data } = await API.post('/api/regenerate', { voxel, voxel_resolution })
  return data as { ok: boolean, state: any, assets: {height8:string,height16:string,splat:string,voxel_obj?:string,voxel_bin?:string} }
}

// Template system
export interface Template {
  id: string
  name: string
  description: string
  category: string
  tags: string[]
  thumbnail_hint: string
  format: 'commands' | 'actions'
  command_count?: number
  action_count?: number
}

export interface TemplateListResponse {
  ok: boolean
  templates: Template[]
  categories: string[]
  count: number
}

export interface TemplateDetailResponse {
  ok: boolean
  template: Template & { commands: string[] }
}

export async function listTemplates(category?: string, tag?: string): Promise<TemplateListResponse> {
  const params = new URLSearchParams()
  if (category) params.append('category', category)
  if (tag) params.append('tag', tag)
  
  const { data } = await API.get(`/api/templates?${params.toString()}`)
  return data as TemplateListResponse
}

export async function getTemplate(templateId: string): Promise<TemplateDetailResponse> {
  const { data } = await API.get(`/api/templates/${templateId}`)
  return data as TemplateDetailResponse
}

export async function applyTemplate(templateId: string, seed?: number, biome?: string) {
  const { data } = await API.post(`/api/templates/${templateId}/apply`, { seed, biome })
  return data as { ok: boolean, template_id: string, template_name: string, state: any, assets: {height8:string,height16:string,splat:string} }
}

// Server status
export interface ServerStatus {
  ok: boolean
  cerebras_api_key_configured: boolean
  llm_parser_available: boolean
  server_ready: boolean
  error?: string
}

export async function getServerStatus(): Promise<ServerStatus> {
  const { data } = await API.get('/api/status')
  return data as ServerStatus
}

