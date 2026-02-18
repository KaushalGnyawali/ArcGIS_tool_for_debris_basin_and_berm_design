# Platform Designer - Volume Calculation Guide

## Enhanced Volume Reporting

The Platform Designer tool provides comprehensive cut and fill volume calculations with detailed earthwork statistics.

---

## Volume Output Example

```
=============================================================
PLATFORM STATISTICS
=============================================================

PLATFORM GEOMETRY:
  Total platform area: 450.0 m2
  Total platform area: 0.045 hectares
  Cut area: 275.5 m2 (61.2% of platform)
  Fill area: 174.5 m2 (38.8% of platform)

CUT VOLUME (Excavation):
  Total cut: 1,250.5 m3
  Total cut: 1.25 thousand m3
  Average cut depth: 4.54 m
  Maximum cut depth: 7.20 m
  Truck loads (15 m3): 83 loads
  Weight (1.8 t/m3): 2,251 tonnes

FILL VOLUME (Embankment):
  Total fill: 985.3 m3
  Total fill: 0.99 thousand m3
  Average fill depth: 5.65 m
  Maximum fill depth: 8.10 m
  Compacted volume: 985.3 m3
  Loose volume (1.25 factor): 1,231.6 m3
  Truck loads (15 m3): 82 loads

NET EARTHWORK:
  Cut volume: 1,250.5 m3
  Fill volume: 985.3 m3
  Net volume: 265.2 m3
  STATUS: 265.2 m3 EXCESS CUT (remove from site)
          18 truck loads to haul away

EARTHWORK SUMMARY:
  Total earthwork: 2,235.8 m3
  Cut/Fill ratio: 1.27
  Volume per m2: 4.97 m3/m2

=============================================================
```

---

## What Gets Calculated

### 1. Platform Geometry

**Total Platform Area**
- Area of the polygon boundary (m² and hectares)
- Defines the extent of grading work

**Cut Area vs Fill Area**
- Cut area: Where excavation occurs
- Fill area: Where material is placed
- Percentage of each relative to total platform

### 2. Cut Volume (Excavation)

**Total Cut Volume**
- Volume of material excavated (m³)
- Reported in m³ and thousand m³

**Average Cut Depth**
- Mean depth across cut areas
- Indicates typical excavation depth

**Maximum Cut Depth**
- Deepest excavation point
- Important for equipment selection

**Material Quantities**
- Truck loads needed (15 m³ trucks standard)
- Weight in tonnes (1.8 t/m³ typical soil)

### 3. Fill Volume (Embankment)

**Total Fill Volume**
- Volume of compacted fill (m³)
- Reported in m³ and thousand m³

**Average Fill Depth**
- Mean height across fill areas
- Indicates typical fill thickness

**Maximum Fill Depth**
- Highest fill point
- Critical for stability analysis

**Material Quantities**
- Compacted volume (in-place)
- Loose volume (1.25 bulking factor)
- Truck loads needed for import

### 4. Net Earthwork

**Net Volume**
```
Net = Cut - Fill

Positive net = Excess cut (surplus to remove)
Negative net = Deficit (need to import)
Zero net = Balanced cut/fill
```

**Status Messages**

Three possible outcomes:

**Balanced:**
```
STATUS: Balanced cut/fill
→ Cut and fill volumes approximately equal
→ Minimal hauling required
```

**Excess Cut:**
```
STATUS: 265.2 m3 EXCESS CUT (remove from site)
        18 truck loads to haul away
→ More cut than fill
→ Need to dispose of surplus
```

**Excess Fill:**
```
STATUS: 450.0 m3 EXCESS FILL (import to site)
        38 truck loads to bring in
→ More fill than cut
→ Need to import material
```

### 5. Earthwork Summary

**Total Earthwork**
- Sum of all cut and fill
- Total volume moved on site

**Cut/Fill Ratio**
- Cut ÷ Fill
- Ratio > 1: More cut than fill
- Ratio < 1: More fill than cut
- Ratio = 1: Balanced

**Volume per m²**
- Total earthwork ÷ Platform area
- Intensity of grading work
- Higher values = more intensive earthwork

---

## Calculation Method

### Step 1: Create Platform Surface

Interpolate from vertex elevations:
```
Vertex A: 100.0 m
Vertex B: 102.0 m
Vertex C: 101.0 m
Vertex D: 101.5 m

→ Interpolated surface across polygon
```

### Step 2: Calculate Difference

```
At each cell:
  Difference = Original_DEM - Platform_Surface
  
  If Difference > 0:  CUT (remove material)
  If Difference < 0:  FILL (add material)
  If Difference = 0:  No change
```

### Step 3: Sum Volumes

```
Cut cells:  Where original > platform
Fill cells: Where platform > original

Cut Volume = Sum(Difference) × Cell_Area  (where Diff > 0)
Fill Volume = Sum(-Difference) × Cell_Area (where Diff < 0)
```

### Step 4: Calculate Statistics

```
Average Depth = Total_Volume / Number_of_Cells / Cell_Area
Maximum Depth = Maximum cell value
Area = Number_of_cells × Cell_Area
```

---

## Understanding the Numbers

### Cut Volume

**What it represents:**
- Material that must be excavated
- Soil, rock, or debris removed

**Use for:**
- Excavation cost estimation
- Haul truck scheduling
- Disposal site planning
- Equipment selection

**Example:**
```
Cut volume: 1,250 m3
Truck loads (15 m3): 83 loads

→ Need 83 truckloads to remove material
→ At 30 loads/day: ~3 days of hauling
```

### Fill Volume

**What it represents:**
- Material that must be placed
- Compacted fill required

**Use for:**
- Fill material procurement
- Compaction planning
- Truck delivery scheduling
- Settlement estimates

**Bulking Factor:**
```
Compacted: 985 m3 (in-place volume)
Loose: 1,232 m3 (as hauled)

Bulking factor: 1.25 typical
→ 25% more volume when loose
```

### Net Volume

**What it represents:**
- Balance between cut and fill
- Surplus or deficit

**Positive Net (Excess Cut):**
```
Net: +265 m3
→ 265 m3 surplus cut material
→ Must be removed from site
→ Disposal cost or spoil area needed
```

**Negative Net (Excess Fill):**
```
Net: -450 m3
→ 450 m3 fill deficit
→ Must import material
→ Borrow pit or purchase needed
```

**Near Zero (Balanced):**
```
Net: ±10 m3
→ Approximately balanced
→ Minimal import/export
→ Cost-effective grading
```

---

## Platform Type Effects on Volumes

### Cut and Fill (Default)

**All changes allowed:**
- Cut where platform < ground
- Fill where platform > ground
- Maximum earthwork volume

**Typical output:**
```
Cut: 1,250 m3
Fill: 985 m3
Net: +265 m3 (excess cut)
```

### Cut Only

**Only excavation allowed:**
- Cut where platform < ground
- No fill (keep ground where platform > ground)
- Lower total volumes

**Typical output:**
```
Cut: 750 m3
Fill: 0 m3
Net: +750 m3 (all cut)
```

### Fill Only

**Only embankment allowed:**
- Fill where platform > ground
- No cut (keep ground where platform < ground)
- Lower total volumes

**Typical output:**
```
Cut: 0 m3
Fill: 620 m3
Net: -620 m3 (all fill)
```

---

## Practical Applications

### Cost Estimation

```
Cut volume: 1,250 m3
Fill volume: 985 m3
Net: +265 m3 excess cut

Costs:
  Excavation: 1,250 m3 × $15/m3 = $18,750
  Fill placement: 985 m3 × $12/m3 = $11,820
  Haul away: 265 m3 × $8/m3 = $2,120
  
  Total earthwork cost: $32,690
```

### Material Management

**Balanced Site:**
```
Cut: 1,000 m3
Fill: 980 m3
Net: +20 m3

Strategy:
→ Use cut material for fill
→ Stockpile 20 m3 on site
→ Minimize import/export
→ Lowest cost option
```

**Import Required:**
```
Cut: 500 m3
Fill: 900 m3
Net: -400 m3

Strategy:
→ Use 500 m3 cut for fill
→ Import 400 m3 (500 m3 loose)
→ 33 truckloads to bring in
→ Source: Borrow pit or purchase
```

**Export Required:**
```
Cut: 1,500 m3
Fill: 800 m3
Net: +700 m3

Strategy:
→ Use 800 m3 cut for fill
→ Export 700 m3
→ 47 truckloads to haul away
→ Disposal site required
```

### Equipment Selection

**Cut depth determines equipment:**

```
Average cut: 2.5 m
Maximum cut: 4.0 m
→ Standard excavator suitable

Average cut: 6.0 m
Maximum cut: 10.5 m
→ Large excavator or dozer required
→ May need benching
```

**Fill depth determines compaction:**

```
Average fill: 1.5 m
Maximum fill: 3.0 m
→ Standard compaction in lifts

Average fill: 8.0 m
Maximum fill: 12.0 m
→ Thick fill, stability analysis needed
→ Compaction testing required
```

---

## Volume Verification

### Check Reasonableness

**Volume per m² check:**
```
Platform area: 450 m2
Total earthwork: 2,236 m3
Volume per m2: 4.97 m3/m2

Reasonable ranges:
  Light grading: 0.5 - 2.0 m3/m2
  Moderate: 2.0 - 5.0 m3/m2
  Heavy: 5.0 - 10.0 m3/m2
  Extreme: > 10.0 m3/m2
  
→ 4.97 is moderate to heavy grading
```

**Average depth check:**
```
Cut: Average 4.5 m, Maximum 7.2 m
Fill: Average 5.7 m, Maximum 8.1 m

Max should be 1.5-2× average
→ 7.2 / 4.5 = 1.6 ✓ Reasonable
→ 8.1 / 5.7 = 1.4 ✓ Reasonable
```

### Cross-Check Methods

1. **Extract cross-sections**
   - Verify depths visually
   - Check platform grades

2. **Compare to polygon area**
   - Calculate theoretical volume
   - Verify against reported volume

3. **Review cut/fill ratio**
   - Should match terrain/design
   - Balanced: Ratio near 1.0
   - Hillside cut: Ratio > 1.5
   - Valley fill: Ratio < 0.7

---

## Report Interpretation

### Example 1: Balanced Site

```
Cut: 800 m3
Fill: 780 m3
Net: +20 m3
Cut/Fill ratio: 1.03

Interpretation:
→ Nearly balanced earthwork
→ Minimal import/export
→ Cost-effective design
→ Good site utilization
```

### Example 2: Cut Platform

```
Cut: 2,100 m3
Fill: 450 m3
Net: +1,650 m3
Cut/Fill ratio: 4.67

Interpretation:
→ Primarily excavation
→ Large surplus to remove
→ Hillside or elevated site
→ Need disposal plan
```

### Example 3: Fill Platform

```
Cut: 300 m3
Fill: 1,850 m3
Net: -1,550 m3
Cut/Fill ratio: 0.16

Interpretation:
→ Primarily fill work
→ Large import needed
→ Valley or low-lying site
→ Need material source
```

---

## Tips for Optimizing Earthwork

### Minimize Net Volume

**Adjust platform elevation:**
- Raise platform → More cut, less fill
- Lower platform → More fill, less cut
- Iterate to balance

**Example:**
```
Design 1: Platform at 100.0 m
  Cut: 1,500 m3, Fill: 800 m3, Net: +700 m3

Design 2: Platform at 99.5 m (lowered 0.5 m)
  Cut: 1,200 m3, Fill: 1,100 m3, Net: +100 m3
  
→ Design 2 more balanced
```

### Use Cut for Fill

**On-site balance:**
- Plan haul routes
- Stockpile cut material
- Use for fill areas
- Minimize import/export

### Consider Disposal Costs

**If excess cut:**
- On-site spoil area cheaper than haul-away
- Can excess be used elsewhere?
- Landscaping, berms, other projects

**If excess fill needed:**
- On-site source cheaper than import
- Can cut areas be deepened?
- Alternative material sources

---

## Volume Reporting Summary

The tool reports:
✓ Cut volume (m³, loads, weight)
✓ Fill volume (m³, loads, compaction)
✓ Net volume (surplus/deficit)
✓ Areas (cut, fill, platform)
✓ Depths (average, maximum)
✓ Earthwork summary (ratio, intensity)

Use volumes for:
✓ Cost estimation
✓ Material management
✓ Equipment selection
✓ Schedule planning
✓ Design optimization
✓ Site logistics

---

**Version:** 2.0  
**Tool:** Platform Designer  
**Feature:** Comprehensive Volume Reporting
