# BERM DESIGN TOOL - QUICK REFERENCE

## One-Page Guide for Field Engineers

### Purpose
Creates trapezoidal berm (deflection structure) with:
- Centreline at constant grade above ground
- Fill material added to raise terrain
- Different left/right side slopes
- Automatic footprint calculation

---

### Inputs Required

| Input | Type | Notes |
|-------|------|-------|
| DEM | Raster | Existing ground, metres |
| Berm Centreline | Polyline | Single line defining berm alignment |
| Berm Height | Number (m) | Height above ground at upstream |
| Grade | Number (%) | Negative = drops downstream |
| Top Width | Number (m) | Flat crest width |
| Left Side Slope | Number (H:V) | Left side slope ratio |
| Right Side Slope | Number (H:V) | Right side slope ratio |

---

### Typical Parameter Values

**Deflection Berm (debris flow):**
- Berm Height: 1.5-3 m
- Grade: -2% to -5%
- Top Width: 2-4 m
- Side Slopes: 1.5:1 to 2:1
- Point Spacing: 1-2 m

**Containment Berm (sediment pond):**
- Berm Height: 1-2 m
- Grade: 0% to -2%
- Top Width: 3-5 m
- Side Slopes: 2:1 to 3:1
- Point Spacing: 2 m

---

### How It Works (3 Steps)

**1. BERM CREST**
```
z_crest = z_ground + Berm_Height + (Grade/100) × distance
```
- Starts at specified height above ground
- Follows constant grade downstream

**2. SIDE SLOPES**
```
z_left = z_crest - (distance - Top_Width/2) / Left_Slope
z_right = z_crest - (distance - Top_Width/2) / Right_Slope
```
- Flat top at crest width
- Slopes down at different rates left/right

**3. FILL DEM**
```
DEM_new = MAX(DEM_original, z_design)
```
- Raises terrain where berm is above ground
- Does not cut anywhere

---

### Output Files

- **Output DEM**: Terrain with berm added
- **Design Surface** (optional): Berm elevations
- **Footprint Polygon** (optional): Berm footprint boundary
- **Control Points** (optional): Check crest elevations

---

### Quick Checks

✓ **Centreline Direction**: Tool auto-reverses if needed
✓ **Fill Volume**: Shown in tool messages
✓ **Berm Height Range**: Check min/max in messages
✓ **Control Points**: Verify Z_CREST values look correct

---

### Common Issues

| Problem | Solution |
|---------|----------|
| Berm too narrow | Increase side slope H:V ratios |
| Excessive fill volume | Reduce berm height or grade |
| Asymmetric footprint | Adjust left/right slopes separately |
| Gaps in berm | Decrease point spacing |

---

### Design Equations Summary

**Footprint Width (approximate):**
```
Width_left = Top_Width/2 + Berm_Height × Left_Slope
Width_right = Top_Width/2 + Berm_Height × Right_Slope
Total_Width = Width_left + Width_right
```

**Fill Volume (estimate):**
```
Volume ≈ Footprint_Length × Average_Width × Average_Height / 2
```

**Maximum Berm Height:**
```
Max_Height = Berm_Height + |Grade| × Centreline_Length
```

---

### Workflow

1. **Prepare Data**
   - Digitize centreline along desired alignment
   - Check DEM coverage and resolution
   - Determine design heights and slopes

2. **Set Parameters**
   - Start with conservative berm height
   - Use steeper slopes for narrow footprint
   - Test with coarse spacing (5m)

3. **Run Tool**
   - Review messages for berm height range
   - Check if line was reversed
   - Note fill volume estimate

4. **Verify Results**
   - View control points
   - Check cross-sections
   - Inspect footprint polygon

5. **Iterate**
   - Adjust height/slopes as needed
   - Re-run with finer spacing (1m)
   - Export for hydraulic modeling

---

### Left vs Right Side Slopes

**How Sides are Determined:**
- Tool creates small buffers on left/right of centreline
- Each cell is assigned to nearest buffer
- Left = buffer created to left of digitizing direction
- Right = buffer created to right of digitizing direction

**When to Use Different Slopes:**
- **Channel side steeper (1.5:1)**: Minimize erosion risk
- **Field side gentler (2:1 or 3:1)**: Easier access, stability
- **Both same**: Symmetric berm, typical for containment

---

### Cross-Section Example

```
        ←Left Slope    Right Slope→
            1.5:1         2:1
              ╲           ╱
               ╲_________╱  ← Top Width (flat)
                ↑ Berm Height
    ___________/          \____________
         Ground Surface
```

---

### Integration with Hydraulic Models

**HEC-RAS Setup:**
1. Export output DEM as terrain
2. Import into HEC-RAS 2D mesh
3. Model debris flow over/around berm
4. Verify berm height is adequate
5. Iterate design if needed

**Design Checks:**
- Flow depth at berm should not overtop
- Velocity reduction across berm
- Deposition pattern behind berm
- Erosion potential on berm faces

---

### Safety Notes

⚠ **Design Requirements:**
- Berms must meet local geotechnical standards
- Consider foundation stability
- Account for seismic loading where applicable
- Professional engineer review required

⚠ **Construction:**
- Compaction specifications critical
- Erosion protection may be needed
- Drainage provisions required
- Maintenance access essential

---

### For More Information

**Related Tools:**
- Debris Basin Design Tool (companion tool for excavation)

**Design Guidance:**
- USDA Forest Service Engineering Handbook
- FEMA debris flow mitigation guidelines
- Provincial/state slope stability requirements

---

**Tool Version:** 1.0  
**Date:** February 2026  
**Application:** Debris flow deflection and containment structures
