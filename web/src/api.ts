import axios from 'axios'

const API = axios.create({ baseURL: 'http://localhost:8001' })

export async function postCommand(text: string, voxel: boolean = false, voxel_resolution: number = 256) {
  const { data } = await API.post('/api/generate', { text, voxel, voxel_resolution })
  return data as { ok: boolean, state: any, assets: {height8:string,height16:string,splat:string,voxel_obj?:string,voxel_bin?:string} }
}

export async function modifyCommand(text: string, voxel: boolean = false, voxel_resolution: number = 256) {
  const { data } = await API.post('/api/modify', { text, voxel, voxel_resolution })
  return data as { ok: boolean, state: any, assets: {height8:string,height16:string,splat:string,voxel_obj?:string,voxel_bin?:string} }
}

export async function fetchState() {
  const { data } = await API.get('/api/state')
  return data
}

export async function resetTerrain() {
  const { data } = await API.post('/api/reset')
  return data as { ok: boolean, state: any, assets: {height8:string,height16:string,splat:string} }
}

export async function regenerateTerrain(voxel: boolean = false, voxel_resolution: number = 256) {
  const { data } = await API.post('/api/regenerate', { voxel, voxel_resolution })
  return data as { ok: boolean, state: any, assets: {height8:string,height16:string,splat:string,voxel_obj?:string,voxel_bin?:string} }
}

