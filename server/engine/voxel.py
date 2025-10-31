"""Voxel terrain generation - Converts heightmap to 3D voxel representation."""
import numpy as np
from typing import Tuple, Optional

def heightmap_to_voxels(heightmap: np.ndarray, resolution: int = 256,
                        voxel_size: float = 1.0, 
                        height_scale: float = 50.0) -> np.ndarray:
    """
    Convert heightmap to voxel grid representation.
    
    This enables features like caves, overhangs, and tunnels that aren't
    possible with heightmap-based terrain.
    
    Args:
        heightmap: 2D heightmap array (0-1 normalized, H x W)
        resolution: Voxel grid resolution (cubic, resolution³ voxels)
        voxel_size: Size of each voxel in world units
        height_scale: Scale factor for heightmap to voxel height
        
    Returns:
        3D boolean array (resolution x resolution x resolution) where
        True = solid voxel, False = air
    """
    h, w = heightmap.shape
    
    # Scale heightmap to voxel grid resolution
    # Map heightmap coordinates to voxel grid coordinates
    voxel_grid = np.zeros((resolution, resolution, resolution), dtype=bool)
    
    # For each (x, z) position in the voxel grid, check if y < height
    for z in range(resolution):
        for x in range(resolution):
            # Map voxel coordinates to heightmap coordinates
            hm_x = int((x / resolution) * w)
            hm_z = int((z / resolution) * h)
            hm_x = min(hm_x, w - 1)
            hm_z = min(hm_z, h - 1)
            
            # Get height from heightmap
            height_value = heightmap[hm_z, hm_x]
            
            # Convert to voxel height
            voxel_height = int(height_value * height_scale)
            voxel_height = min(voxel_height, resolution - 1)
            
            # Fill voxels from bottom to height
            voxel_grid[:voxel_height+1, z, x] = True
    
    return voxel_grid


def export_voxels_mesh(voxel_grid: np.ndarray, output_path: str):
    """
    Export voxel grid as OBJ mesh file.
    
    Uses naive surface extraction (voxel faces visible from outside).
    
    Args:
        voxel_grid: 3D boolean array (solid=True, air=False)
        output_path: Path to save OBJ file
    """
    res = voxel_grid.shape[0]
    vertices = []
    faces = []
    vertex_count = 0
    
    # Generate mesh by checking each voxel face
    for z in range(res):
        for y in range(res):
            for x in range(res):
                if not voxel_grid[y, z, x]:
                    continue  # Skip air voxels
                
                # Check each face (6 directions)
                # Only add face if neighbor is air or out of bounds
                directions = [
                    (1, 0, 0), (-1, 0, 0),  # +x, -x
                    (0, 1, 0), (0, -1, 0),  # +y, -y
                    (0, 0, 1), (0, 0, -1),  # +z, -z
                ]
                
                for dx, dy, dz in directions:
                    nx, ny, nz = x + dx, y + dy, z + dz
                    
                    # Check if neighbor is air or out of bounds
                    if (nx < 0 or nx >= res or ny < 0 or ny >= res or 
                        nz < 0 or nz >= res or not voxel_grid[ny, nz, nx]):
                        
                        # Add face vertices
                        # Face vertices depend on direction
                        v_base = vertex_count
                        
                        if dx == 1:  # +x face
                            v0 = (x+1, y, z)
                            v1 = (x+1, y+1, z)
                            v2 = (x+1, y+1, z+1)
                            v3 = (x+1, y, z+1)
                        elif dx == -1:  # -x face
                            v0 = (x, y, z+1)
                            v1 = (x, y+1, z+1)
                            v2 = (x, y+1, z)
                            v3 = (x, y, z)
                        elif dy == 1:  # +y face
                            v0 = (x, y+1, z)
                            v1 = (x+1, y+1, z)
                            v2 = (x+1, y+1, z+1)
                            v3 = (x, y+1, z+1)
                        elif dy == -1:  # -y face
                            v0 = (x, y, z+1)
                            v1 = (x+1, y, z+1)
                            v2 = (x+1, y, z)
                            v3 = (x, y, z)
                        elif dz == 1:  # +z face
                            v0 = (x, y, z+1)
                            v1 = (x, y+1, z+1)
                            v2 = (x+1, y+1, z+1)
                            v3 = (x+1, y, z+1)
                        else:  # -z face
                            v0 = (x+1, y, z)
                            v1 = (x+1, y+1, z)
                            v2 = (x, y+1, z)
                            v3 = (x, y, z)
                        
                        # Store vertices
                        vertices.extend([v0, v1, v2, v3])
                        
                        # Triangulate quad: split into two triangles
                        # Triangle 1: v0, v1, v2
                        # Triangle 2: v0, v2, v3
                        faces.append((v_base, v_base+1, v_base+2))
                        faces.append((v_base, v_base+2, v_base+3))
                        vertex_count += 4
    
    # Write OBJ file
    with open(output_path, 'w') as f:
        f.write("# Voxel terrain mesh\n")
        for v in vertices:
            f.write(f"v {v[0]} {v[1]} {v[2]}\n")
        
        # Write triangulated faces (OBJ indices are 1-based)
        for face in faces:
            f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")


def export_voxels_binary(voxel_grid: np.ndarray, output_path: str):
    """
    Export voxel grid as binary format (simple format for Unity/Minecraft-like use).
    
    Format: uint32 width, uint32 height, uint32 depth, then bool array.
    
    Args:
        voxel_grid: 3D boolean array
        output_path: Path to save binary file
    """
    res = voxel_grid.shape[0]
    
    with open(output_path, 'wb') as f:
        # Write header
        f.write(np.array([res, res, res], dtype=np.uint32).tobytes())
        
        # Write voxel data (as uint8: 0=air, 1=solid)
        voxel_bytes = voxel_grid.astype(np.uint8).tobytes()
        f.write(voxel_bytes)

