# Basin Volume Calculator - Method Explanation

## Purpose

Calculates the excavated volume of a debris basin from a DEM where the basin has already been cut into the terrain.

---

## The Challenge

You have a DEM with a basin excavated into it, but you don't have the original "before" DEM. How do you calculate the volume of material that was removed?

---

## The Solution: Boundary Interpolation Method

### Step 1: Extract the Basin Rim

The basin polygon boundary represents the **rim** - the edge where excavation started. This rim follows the original ground surface.

```
    Rim elevation = Original ground elevation
         ↓
    ●---●---●---●  ← Basin boundary (rim)
    |           |
    |  Basin    |  ← Excavated area (lower)
    |           |
    ●-----------●
```

### Step 2: Sample Rim Elevations

Create dense points along the basin boundary and sample DEM elevations at each point. These elevations represent the original ground before excavation.

**Example:**
- North rim: 395 m
- South rim: 387 m (8m lower due to slope)
- East rim: 392 m
- West rim: 390 m

### Step 3: Interpolate Original Surface

Use IDW (Inverse Distance Weighting) interpolation to reconstruct what the ground surface was across the basin area before excavation.

```
Original Surface (interpolated from rim):
    
    395 ---- 392.5 ---- 390  ← High end
     |         |         |
    391 ---- 389.5 ---- 387.5  ← Slope
     |         |         |
    387 ---- 387 ---- 385  ← Low end (outlet)
```

### Step 4: Calculate Excavation Depth

At each cell:
```
Cut Depth = Original Surface (interpolated) - Actual Basin Floor (DEM)
```

### Step 5: Sum to Get Volume

```
Volume = Sum(Cut Depth at each cell) × Cell Area
```

---

## Why This Method Works

**Key Insight:** The basin rim (polygon boundary) lies on the original ground surface. By interpolating from these rim elevations, we reconstruct the pre-excavation terrain.

**For Sloped Basins:**
- Rim naturally captures the slope (high end vs low end)
- Interpolation creates a sloped surface across the basin
- Volume calculation includes the full depth at all locations

**Compared to Other Methods:**
- **Spillway method:** Only calculates storage to outlet level - underestimates total excavation
- **Maximum elevation method:** Uses highest point - overestimates on sloped terrain
- **Buffer method:** Samples far from basin - misses local slope variations

---

## Inputs

| Input | Description |
|-------|-------------|
| DEM with Basin | Modified DEM with excavation already present |
| Basin Polygon | Boundary of the excavated area |

---

## Outputs

```
EXCAVATION VOLUME
Total volume: 2315.0 m3
Total volume: 2.32 thousand m3

EXCAVATION DEPTH
Average depth: 1.85 m
Maximum depth: 3.12 m

MATERIAL QUANTITIES
Material excavated: 2315.0 m3
Truck loads (15 m3): 154 loads
```

---

## Technical Details

**Interpolation Method:** IDW (Inverse Distance Weighting)
- Power: 2
- Sampling: Half cell size spacing along boundary
- Extent: Limited to basin polygon

**Volume Calculation:**
- Cell-by-cell depth summation
- Accounts for NoData values
- Uses numpy arrays for precision

---

## Limitations

1. **Assumes linear interpolation** between rim points
2. **Accuracy depends on** basin polygon accuracy
3. **Best for** basins cut into relatively smooth slopes
4. **May underestimate** if original terrain had significant bumps/ridges inside basin area

---

## When to Use

✓ You have DEM with basin already excavated
✓ You know the basin boundary (polygon)
✓ You need total excavation volume
✓ Basin was cut into sloped terrain

✗ You have both before/after DEMs (use simple subtraction instead)
✗ Basin has complex internal features in original terrain

---

## Accuracy Tips

**For best results:**
- Draw basin polygon precisely along the rim
- Use high-resolution DEM (≤ 1m cell size)
- Ensure rim follows the actual excavation edge
- Check that rim elevations look reasonable

**Validation:**
- Visual check: Does interpolated surface look like original terrain?
- Cross-section check: Compare interpolated vs actual at sample locations
- Order of magnitude: Does volume match expected excavation?

---

## Example Workflow

1. Create basin design with Debris Basin Design Tool
2. Export basin DEM and polygon
3. Run Basin Volume Calculator:
   - Input: Basin DEM
   - Input: Basin polygon
4. Review volume estimate
5. Use for material quantity estimation

---

**Version:** 1.0  
**Date:** February 2026  
**Method:** Boundary interpolation with IDW
