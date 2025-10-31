"""Slope generation primitives - Gradual directional inclines."""
import numpy as np
from ..utils import clamp01
from scipy.ndimage import gaussian_filter

RES = 512

def generate_slope(start: tuple, end: tuple, width: int, height: float,
                   falloff: float = 0.3) -> np.ndarray:
    """
    Generate a slope (gradual incline) heightmap stamp.
    
    Args:
        start: (x, y) start coordinates (lower elevation)
        end: (x, y) end coordinates (higher elevation)
        width: Width of slope perpendicular to direction
        height: Maximum height difference (0-1)
        falloff: How quickly slope blends at edges (0.0 = sharp, 1.0 = gradual)
        
    Returns:
        512x512 heightmap stamp
    """
    sx, sy = start
    ex, ey = end
    
    # Vector along slope
    dx_line = ex - sx
    dy_line = ey - sy
    length = np.sqrt(dx_line*dx_line + dy_line*dy_line)
    
    if length < 1.0:
        return np.zeros((RES, RES), dtype=np.float32)
    
    # Unit vector along slope
    ux = dx_line / length
    uy = dy_line / length
    
    # Perpendicular vector
    px = -uy
    py = ux
    
    yy, xx = np.mgrid[0:RES, 0:RES]
    
    # Distance along slope (0 = start, 1 = end)
    dx = xx - sx
    dy = yy - sy
    along = dx * ux + dy * uy
    
    # Distance perpendicular to slope
    perp = dx * px + dy * py
    
    # Height increases linearly along slope
    along_normalized = np.clip(along / length, 0.0, 1.0)
    height_gradient = height * along_normalized
    
    # Perpendicular falloff
    perp_normalized = np.abs(perp) / (width / 2.0)
    perp_factor = np.exp(-perp_normalized / (falloff + 0.1))
    
    # Edge falloff at start/end
    edge_blend = 40.0
    edge_factor = np.ones_like(along)
    
    # Start edge
    start_mask = (along >= 0) & (along < edge_blend)
    if np.any(start_mask):
        edge_factor[start_mask] = np.clip(along[start_mask] / edge_blend, 0.0, 1.0)
    
    # End edge
    end_mask = (along <= length) & (along > length - edge_blend)
    if np.any(end_mask):
        edge_factor[end_mask] = np.clip((length - along[end_mask]) / edge_blend, 0.0, 1.0)
    
    # Combine
    stamp = height_gradient * perp_factor * edge_factor
    
    # Smooth slightly
    stamp = gaussian_filter(stamp, sigma=1.0)
    
    return stamp


def generate_slope_radial(cx: int, cy: int, radius: int, height: float,
                          direction: float = 0.0, steepness: float = 0.5) -> np.ndarray:
    """
    Generate a radial slope (inclined area around a point).
    
    Args:
        cx, cy: Center coordinates
        radius: Radius of slope area
        height: Maximum height at edge (0-1)
        direction: Direction of incline in degrees (0 = north)
        steepness: How steep the slope is (0.0 = flat, 1.0 = very steep)
        
    Returns:
        512x512 heightmap stamp
    """
    yy, xx = np.mgrid[0:RES, 0:RES]
    dx = xx - cx
    dy = yy - cy
    
    # Distance from center
    dist = np.sqrt(dx*dx + dy*dy)
    
    # Angle from center
    angle = np.arctan2(dy, dx)
    dir_rad = np.deg2rad(direction)
    
    # Height varies with distance and angle
    # Maximum height at edge in the specified direction
    angle_factor = 0.5 + 0.5 * np.cos(angle - dir_rad)
    dist_factor = np.clip(dist / radius, 0.0, 1.0)
    
    # Steepness controls how quickly height increases
    height_curve = np.power(dist_factor, 1.0 / (steepness + 0.1))
    
    stamp = height * height_curve * angle_factor
    
    # Falloff at edges
    edge_mask = dist > radius
    if np.any(edge_mask):
        edge_dist = dist[edge_mask] - radius
        edge_blend = 30.0
        edge_factor = np.exp(-edge_dist / edge_blend)
        stamp[edge_mask] *= edge_factor
    
    # Smooth
    stamp = gaussian_filter(stamp, sigma=1.5)
    
    return stamp

