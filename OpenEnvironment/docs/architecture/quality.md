# Quality Evaluation

**File:** `semantic/evaluation/metrics.py`

The evaluation system scores terrain on two axes: feature composition and texture quality.

## Feature metrics (`compute_feature_metrics`)

Given a list of features, computes:

- **feature_count** / **type_diversity** -- how many features, how many distinct types
- **extent** -- bounding box width/height of all feature positions
- **centroid** -- center of mass of all features
- **height_stats** / **radius_stats** -- min, max, mean, std of height/radius values

## Aesthetic quality (`evaluate_aesthetic_quality`)

Coarse 0-1 score based on feature metrics:

| Criterion | Points | Threshold |
|-----------|--------|-----------|
| Feature count >= 3 | 0.25 | Sparse scene warning |
| Type diversity >= 2 | 0.25 | Low diversity warning |
| Spatial spread >= 40x40 | 0.20 | Cramped scene warning |
| Height std >= 0.05 | 0.15 | Flat scene warning |
| Diagonal >= 80 | 0.15 | Narrow composition warning |

Returns `{score, warnings}`.

## Texture metrics (`compute_texture_metrics`)

Given a heightmap and splatmap (HxWx4 RGBA), computes:

- **channel_coverage** -- mean intensity per channel (grass, rock, sand, snow)
- **coverage_entropy** -- how evenly distributed the texture channels are
- **rock_slope_corr** -- correlation between slope magnitude and rock channel
- **snow_height_corr** -- correlation between height and snow channel
- **sand_low_corr** -- correlation between low elevation and sand channel
- **roughness_mean/std** -- slope magnitude statistics

## Quality rubric (`evaluate_quality_rubric`)

Combines feature and texture metrics against a configurable rubric (`DEFAULT_QUALITY_RUBRIC`):

**Composition checks:**
- feature_count >= 4
- type_diversity >= 3
- extent diagonal >= 110
- height_std >= 0.06

**Texture checks:**
- Per-channel coverage within target ranges (e.g. grass 0.18-0.55)
- Coverage entropy >= 1.2
- Rock-slope correlation >= 0.35
- Snow-height correlation >= 0.45
- Sand-low correlation >= 0.30

Each check is weighted equally. Failed checks generate actionable warning strings. Output: `{overall_score, categories: {composition, textures}, warnings}`.

## Where it's used

- **Narrative pipeline** (`narrative/utils.py`) -- evaluates generated compositions before returning actions
- **terrain.py** -- evaluates final state after `apply_actions` completes
- **ReAct agent tools** (`tools/quality_tools.py`) -- agent can call evaluation during reasoning
- **Multi-agent workflow** -- critic agent evaluates quality between rounds
