# DEBRIS BASIN DESIGN TOOL - QUICK REFERENCE

## One-Page Guide for Field Engineers

### Purpose
Creates trapezoidal debris basin design with:
- Creek centreline at constant grade
- Side slopes from basin boundary edges
- Automatic flat bottom calculation

---

### Inputs Required

| Input | Type | Notes |
|-------|------|-------|
| DEM | Raster | Existing ground, metres |
| Creek Centreline | Polyline | Single line, flows through basin |
| Basin Polygon | Polygon | Excavation footprint |
| Cut Depth | Number (m) | Depth below ground at creek |
| Grade | Number (%) | Negative = drops downstream |
| Side Slope | Number (H:V) | E.g., 1.5 = 1.5m horiz per 1m vert |

---

### Typical Parameter Values

**Small Basin (< 5 hectares):**
- Cut Depth: 1.5-2.5 m
- Grade: -3% to -5%
- Side Slope: 1.5:1 to 2:1
- Point Spacing: 2 m

**Large Basin (> 5 hectares):**
- Cut Depth: 2-3 m
- Grade: -2% to -4%
- Side Slope: 2:1 to 3:1
- Point Spacing: 3-5 m

---

### How It Works (3 Steps)

**1. CREEK INVERT**
```
z_invert = z_ground - Cut_Depth + (Grade/100) × distance
```
- Cuts down by specified depth at upstream
- Follows constant grade downstream

**2. SIDE SLOPES**
```
z_slope = z_ground - distance_from_boundary / Side_Slope
```
- Starts at basin boundary (at ground elevation)
- Slopes inward at H:V ratio

**3. TRAPEZOIDAL SECTION**
```
z_design = MAX(z_slope, z_creek_invert)
```
- Where slope meets invert = flat bottom
- Automatically creates trapezoidal cross-section

---

### Output Files

- **Output DEM**: Cut terrain with basin excavated
- **Design Surface** (optional): Design elevations before cutting
- **Control Points** (optional): Check design inverts along centreline

---

### Quick Checks

✓ **Centreline Direction**: Tool auto-reverses if needed
✓ **Cut Volume**: Shown in tool messages
✓ **Design Range**: Check min/max elevations in messages
✓ **Control Points**: Verify ZINV values look correct

---

### Common Issues

| Problem | Solution |
|---------|----------|
| No cut downstream | Tool will auto-reverse - check messages |
| Design above ground | Increase cut depth or reduce grade |
| Narrow cut only | Increase side slope H:V ratio |
| Jagged surface | Decrease point spacing |

---

### Design Equations Summary

**Flat Bottom Width (auto-calculated):**
```
Width ≈ 2 × Cut_Depth × Side_Slope_HV
```

**Cut Volume (estimate):**
```
Volume ≈ Basin_Area × Average_Cut_Depth
```

**Maximum Side Slope Height:**
```
Max_Height = Cut_Depth + (Basin_Width/2) / Side_Slope_HV
```

---

### Workflow

1. **Prepare Data**
   - Digitize centreline (flow direction)
   - Draw basin polygon
   - Check DEM coverage

2. **Set Parameters**
   - Start with conservative values
   - Test with coarse spacing (5m)

3. **Run Tool**
   - Review messages
   - Check if line was reversed

4. **Verify Results**
   - View control points
   - Check cross-sections
   - Calculate volumes

5. **Iterate**
   - Adjust parameters
   - Re-run with finer spacing (1-2m)
   - Export for hydraulic modeling

---

### For More Information
See full README.md for detailed documentation

---

**Tool Version:** 1.0  
**Date:** February 2026  
**Application:** Post-wildfire debris flow mitigation
