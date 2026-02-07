import arcpy
from arcpy.sa import Con, IsNull, CellStatistics, ExtractByMask, EucAllocation, EucDistance, ExtractValuesToPoints


class Toolbox(object):
    def __init__(self):
        self.label = "Berm Design Toolbox"
        self.alias = "bermdesign"
        self.tools = [BermDesignTool]


class BermDesignTool(object):
    def __init__(self):
        self.label = "Berm Design Tool"
        self.description = "Creates trapezoidal berm with fill above existing ground"
        self.canRunInBackground = False

    def getParameterInfo(self):
        # Parameter 0: Input DEM
        param0 = arcpy.Parameter(
            displayName="Input DEM",
            name="in_dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        # Parameter 1: Berm Centreline
        param1 = arcpy.Parameter(
            displayName="Berm Centreline",
            name="in_line",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["Polyline"]

        # Parameter 2: Berm Height at Start
        param2 = arcpy.Parameter(
            displayName="Berm Height at Start (m)",
            name="berm_height",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param2.value = 2.0

        # Parameter 3: Longitudinal Grade
        param3 = arcpy.Parameter(
            displayName="Centreline Grade (%) - Negative = Drops Downstream",
            name="grade_percent",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param3.value = -2.0

        # Parameter 4: Top Width
        param4 = arcpy.Parameter(
            displayName="Berm Top Width (m)",
            name="top_width",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param4.value = 3.0

        # Parameter 5: Left Side Slope
        param5 = arcpy.Parameter(
            displayName="Left Side Slope (H:V)",
            name="left_slope_hv",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param5.value = 2.0

        # Parameter 6: Right Side Slope
        param6 = arcpy.Parameter(
            displayName="Right Side Slope (H:V)",
            name="right_slope_hv",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param6.value = 2.0

        # Parameter 7: Maximum Footprint Width
        param7 = arcpy.Parameter(
            displayName="Maximum Footprint Width (m) - Optional",
            name="max_footprint_width",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input")

        # Parameter 8: Point Spacing
        param8 = arcpy.Parameter(
            displayName="Point Spacing (m)",
            name="pt_spacing",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param8.value = 2.0

        # Parameter 9: Processing Buffer
        param9 = arcpy.Parameter(
            displayName="Processing Buffer (m)",
            name="proc_buffer_m",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param9.value = 50.0

        # Parameter 10: Output DEM
        param10 = arcpy.Parameter(
            displayName="Output DEM",
            name="out_dem",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Output")

        # Parameter 11: Output Design Surface
        param11 = arcpy.Parameter(
            displayName="Output Design Surface",
            name="out_design",
            datatype="DERasterDataset",
            parameterType="Optional",
            direction="Output")

        # Parameter 12: Output Footprint
        param12 = arcpy.Parameter(
            displayName="Output Berm Footprint Polygon",
            name="out_footprint",
            datatype="DEFeatureClass",
            parameterType="Optional",
            direction="Output")

        # Parameter 13: Output Points
        param13 = arcpy.Parameter(
            displayName="Output Control Points",
            name="out_points",
            datatype="DEFeatureClass",
            parameterType="Optional",
            direction="Output")

        params = [param0, param1, param2, param3, param4, param5, param6,
                  param7, param8, param9, param10, param11, param12, param13]
        return params

    def isLicensed(self):
        try:
            if arcpy.CheckExtension("Spatial") == "Available":
                return True
            else:
                return False
        except:
            return False

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        # Check out extension
        arcpy.CheckOutExtension("Spatial")
        arcpy.env.overwriteOutput = True

        # Get parameters
        in_dem = parameters[0].valueAsText
        in_line = parameters[1].valueAsText
        berm_height = parameters[2].value
        grade_percent = parameters[3].value
        top_width = parameters[4].value
        left_slope_hv = parameters[5].value
        right_slope_hv = parameters[6].value
        max_footprint_width = parameters[7].value
        pt_spacing = parameters[8].value
        proc_buffer_m = parameters[9].value
        out_dem = parameters[10].valueAsText
        out_design = parameters[11].valueAsText
        out_footprint = parameters[12].valueAsText
        out_points = parameters[13].valueAsText

        # Workspace
        arcpy.env.workspace = arcpy.env.scratchGDB
        arcpy.env.scratchWorkspace = arcpy.env.scratchGDB
        tmp_gdb = arcpy.env.scratchGDB
        arcpy.env.snapRaster = in_dem
        arcpy.env.cellSize = in_dem
        dem_sr = arcpy.Describe(in_dem).spatialReference
        arcpy.env.outputCoordinateSystem = dem_sr

        arcpy.AddMessage("=" * 60)
        arcpy.AddMessage("BERM DESIGN TOOL")
        arcpy.AddMessage("=" * 60)

        # Copy inputs
        arcpy.AddMessage("Copying input features...")
        tmp_line = arcpy.management.CopyFeatures(in_line, f"{tmp_gdb}\\cline")[0]

        # Check flow direction
        arcpy.AddMessage("Checking centreline flow direction...")
        tmp_endpoints = f"{tmp_gdb}\\endpoints"
        arcpy.management.FeatureVerticesToPoints(tmp_line, tmp_endpoints, "BOTH_ENDS")
        tmp_endpoints_z = f"{tmp_gdb}\\endpoints_z"
        ExtractValuesToPoints(tmp_endpoints, in_dem, tmp_endpoints_z)
        
        elevations = []
        with arcpy.da.SearchCursor(tmp_endpoints_z, ["RASTERVALU"]) as cursor:
            for row in cursor:
                elevations.append(row[0])
        
        start_elev = elevations[0]
        end_elev = elevations[1]
        
        arcpy.AddMessage(f"Start vertex elevation: {start_elev:.2f} m")
        arcpy.AddMessage(f"End vertex elevation: {end_elev:.2f} m")
        
        # Flip line if flowing uphill
        if start_elev < end_elev:
            arcpy.AddMessage("Reversing centreline to flow downhill...")
            arcpy.edit.FlipLine(tmp_line)
            start_elev, end_elev = end_elev, start_elev

        # Mask
        arcpy.AddMessage("Creating processing mask...")
        tmp_mask = arcpy.analysis.Buffer(
            tmp_line, f"{tmp_gdb}\\mask", f"{proc_buffer_m} Meters"
        )[0]
        arcpy.env.extent = tmp_mask
        arcpy.env.mask = tmp_mask

        # Densify + points
        arcpy.AddMessage("Densifying centreline...")
        arcpy.edit.Densify(tmp_line, "DISTANCE", f"{pt_spacing} Meters")
        tmp_pts = f"{tmp_gdb}\\pts"
        arcpy.management.GeneratePointsAlongLines(
            tmp_line, tmp_pts, "DISTANCE", f"{pt_spacing} Meters", None, "END_POINTS"
        )

        # Extract ground elevations
        arcpy.AddMessage("Extracting ground elevations...")
        tmp_pts_z = f"{tmp_gdb}\\pts_z"
        ExtractValuesToPoints(tmp_pts, in_dem, tmp_pts_z)

        # Add fields
        arcpy.AddMessage("Adding fields...")
        for f, t in [("CHAIN_M", "DOUBLE"), ("Z_GROUND", "DOUBLE"), ("Z_CREST", "DOUBLE"), 
                     ("SRC_ID", "LONG"), ("ZCREST_INT", "LONG"), ("BERM_HT", "DOUBLE")]:
            if f not in [x.name.upper() for x in arcpy.ListFields(tmp_pts_z)]:
                arcpy.management.AddField(tmp_pts_z, f, t)

        # Get line geometry
        with arcpy.da.SearchCursor(tmp_line, ["SHAPE@"]) as sc:
            line_geom = next(sc)[0]

        line_length = line_geom.length
        grade_dec = grade_percent / 100.0

        # Get starting ground elevation
        with arcpy.da.SearchCursor(tmp_pts_z, ["RASTERVALU"], 
                                   sql_clause=(None, "ORDER BY OBJECTID")) as cursor:
            z_ground_start = next(cursor)[0]

        z_crest_start = z_ground_start + berm_height

        arcpy.AddMessage("-" * 60)
        arcpy.AddMessage("DESIGN PARAMETERS:")
        arcpy.AddMessage(f"  Centreline length: {line_length:.1f} m")
        arcpy.AddMessage(f"  Ground at upstream: {start_elev:.2f} m")
        arcpy.AddMessage(f"  Ground at downstream: {end_elev:.2f} m")
        arcpy.AddMessage(f"  Berm crest at start: {z_crest_start:.2f} m")
        arcpy.AddMessage(f"  Berm height at start: {berm_height:.2f} m")
        arcpy.AddMessage(f"  Crest grade: {grade_percent:.2f}%")
        arcpy.AddMessage(f"  Top width: {top_width:.1f} m")
        arcpy.AddMessage(f"  Left side slope: {left_slope_hv:.1f}H:1V")
        arcpy.AddMessage(f"  Right side slope: {right_slope_hv:.1f}H:1V")
        if max_footprint_width:
            arcpy.AddMessage(f"  Max footprint width: {max_footprint_width:.1f} m")
        arcpy.AddMessage("-" * 60)

        # Calculate crest elevations
        arcpy.AddMessage("Calculating berm crest elevations...")
        
        min_zcrest = float('inf')
        max_zcrest = float('-inf')
        min_height = float('inf')
        max_height = float('-inf')
        
        with arcpy.da.UpdateCursor(tmp_pts_z, 
                                   ["OID@", "SHAPE@", "RASTERVALU", "CHAIN_M", 
                                    "Z_GROUND", "Z_CREST", "SRC_ID", "ZCREST_INT", "BERM_HT"]) as uc:
            for oid, shp, raster_val, _, _, _, _, _, _ in uc:
                s = line_geom.measureOnLine(shp)
                z_ground = raster_val if raster_val else z_ground_start
                
                # Crest elevation following constant grade from start
                z_crest = z_crest_start + grade_dec * s
                
                # Actual berm height at this location
                actual_height = z_crest - z_ground
                
                z_int = int(round(z_crest * 10000))
                uc.updateRow((oid, shp, z_ground, s, z_ground, z_crest, oid, z_int, actual_height))
                
                min_zcrest = min(min_zcrest, z_crest)
                max_zcrest = max(max_zcrest, z_crest)
                min_height = min(min_height, actual_height)
                max_height = max(max_height, actual_height)

        z_crest_end = z_crest_start + grade_dec * line_length

        arcpy.AddMessage(f"Berm crest at end: {z_crest_end:.2f} m")
        arcpy.AddMessage(f"Crest elevation range: {min_zcrest:.2f} to {max_zcrest:.2f} m")
        arcpy.AddMessage(f"Berm height range: {min_height:.2f} to {max_height:.2f} m")

        # Save control points
        if out_points:
            arcpy.management.CopyFeatures(tmp_pts_z, out_points)
            arcpy.AddMessage("Control points saved")

        # Euclidean allocation - get crest elevation at each cell
        arcpy.AddMessage("Allocating crest elevations...")
        alloc_zcrest_int = EucAllocation(
            in_source_data=tmp_pts_z,
            source_field="ZCREST_INT",
            cell_size=in_dem
        )
        
        z_crest = alloc_zcrest_int / 10000.0

        # Perpendicular distance from centreline
        arcpy.AddMessage("Calculating perpendicular distances...")
        dperp = EucDistance(
            in_source_data=tmp_line,
            cell_size=in_dem
        )

        # Determine left/right sides using buffer
        arcpy.AddMessage("Determining left and right sides...")
        tmp_left_buffer = f"{tmp_gdb}\\left_buffer"
        tmp_right_buffer = f"{tmp_gdb}\\right_buffer"
        
        # Create left and right side buffers
        arcpy.analysis.Buffer(tmp_line, tmp_left_buffer, "0.5 Meters", 
                            "LEFT", "FLAT", "NONE")
        arcpy.analysis.Buffer(tmp_line, tmp_right_buffer, "0.5 Meters", 
                            "RIGHT", "FLAT", "NONE")
        
        # Calculate distance to left and right buffers
        dist_to_left = EucDistance(tmp_left_buffer, cell_size=in_dem)
        dist_to_right = EucDistance(tmp_right_buffer, cell_size=in_dem)
        
        # Cell is on left side if closer to left buffer
        is_left_side = Con(dist_to_left < dist_to_right, 1, 0)

        # Create design surface - trapezoidal berm with different left/right slopes
        arcpy.AddMessage("Creating trapezoidal berm design...")
        
        halfW = top_width / 2.0
        
        # Get ground surface
        dem_raster = arcpy.sa.Raster(in_dem)
        
        # Design surface based on distance from centreline and side
        # Within top width: flat at crest elevation
        # Beyond top width: slope down at side-specific slope ratio
        
        zdesign = Con(dperp <= halfW,
                     z_crest,  # Flat top
                     Con(is_left_side == 1,
                         z_crest - ((dperp - halfW) / left_slope_hv),  # Left side
                         z_crest - ((dperp - halfW) / right_slope_hv)))  # Right side
        
        # Only where design is above ground
        zdesign_above_ground = Con(zdesign > dem_raster, zdesign)
        
        # Apply maximum footprint width constraint if specified
        if max_footprint_width:
            arcpy.AddMessage(f"Applying maximum footprint width: {max_footprint_width:.1f} m")
            zdesign_above_ground = Con(dperp <= max_footprint_width/2, zdesign_above_ground)

        # Save design surface
        if out_design:
            zdesign_above_ground.save(out_design)
            arcpy.AddMessage("Design surface saved")

        # Create footprint polygon
        if out_footprint:
            arcpy.AddMessage("Creating berm footprint polygon...")
            tmp_footprint_raster = Con(~IsNull(zdesign_above_ground), 1)
            tmp_footprint_poly = f"{tmp_gdb}\\footprint_poly"
            arcpy.conversion.RasterToPolygon(tmp_footprint_raster, tmp_footprint_poly, 
                                            "NO_SIMPLIFY")
            arcpy.management.Dissolve(tmp_footprint_poly, out_footprint)
            arcpy.AddMessage("Footprint polygon saved")

        # Raise DEM with berm
        arcpy.AddMessage("Adding berm to DEM...")
        dem_new = Con(IsNull(zdesign_above_ground), dem_raster, 
                     Con(zdesign_above_ground > dem_raster, zdesign_above_ground, dem_raster))
        
        dem_new.save(out_dem)
        arcpy.AddMessage("Output DEM saved")

        # Calculate statistics
        arcpy.AddMessage("Calculating fill volume...")
        fill_depth_raster = Con(zdesign_above_ground > dem_raster, 
                               zdesign_above_ground - dem_raster, 0)
        
        try:
            cell_size_val = float(arcpy.env.cellSize)
            cell_area = cell_size_val ** 2
            mean_fill = float(arcpy.management.GetRasterProperties(fill_depth_raster, "MEAN").getOutput(0))
            max_fill = float(arcpy.management.GetRasterProperties(fill_depth_raster, "MAXIMUM").getOutput(0))
            cell_count = float(arcpy.management.GetRasterProperties(fill_depth_raster, "VALUECOUNT").getOutput(0))
            fill_volume = mean_fill * cell_count * cell_area
            footprint_area = cell_count * cell_area
            footprint_length = line_length
            avg_footprint_width = footprint_area / footprint_length if footprint_length > 0 else 0
            
            arcpy.AddMessage("-" * 60)
            arcpy.AddMessage("RESULTS:")
            arcpy.AddMessage(f"  Fill volume: {fill_volume:.1f} m³")
            arcpy.AddMessage(f"  Footprint area: {footprint_area:.1f} m²")
            arcpy.AddMessage(f"  Footprint length: {footprint_length:.1f} m")
            arcpy.AddMessage(f"  Average footprint width: {avg_footprint_width:.1f} m")
            arcpy.AddMessage(f"  Average fill height: {mean_fill:.2f} m")
            arcpy.AddMessage(f"  Maximum fill height: {max_fill:.2f} m")
            arcpy.AddMessage("-" * 60)
        except Exception as e:
            arcpy.AddMessage(f"Could not calculate statistics: {str(e)}")

        arcpy.AddMessage("=" * 60)
        arcpy.AddMessage("PROCESS COMPLETE")
        arcpy.AddMessage("=" * 60)
        
        arcpy.CheckInExtension("Spatial")
        return