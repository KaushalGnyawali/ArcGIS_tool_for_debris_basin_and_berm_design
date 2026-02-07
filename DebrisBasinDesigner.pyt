import arcpy
from arcpy.sa import Con, IsNull, CellStatistics, ExtractByMask, EucAllocation, EucDistance, ExtractValuesToPoints


class Toolbox(object):
    def __init__(self):
        self.label = "Ditch Design Toolbox"
        self.alias = "ditchdesign"
        self.tools = [DitchDesignTool]


class DitchDesignTool(object):
    def __init__(self):
        self.label = "Ditch Design Tool"
        self.description = "Cuts trapezoidal debris basin with side slopes from boundary"
        self.canRunInBackground = False

    def getParameterInfo(self):
        # Parameter 0: Input DEM
        param0 = arcpy.Parameter(
            displayName="Input DEM",
            name="in_dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        # Parameter 1: Centreline
        param1 = arcpy.Parameter(
            displayName="Creek Centreline",
            name="in_line",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["Polyline"]

        # Parameter 2: Polygon
        param2 = arcpy.Parameter(
            displayName="Basin Polygon",
            name="in_poly",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param2.filter.list = ["Polygon"]

        # Parameter 3: Cut Depth at Centreline
        param3 = arcpy.Parameter(
            displayName="Cut Depth at Creek Centreline (m)",
            name="cut_depth",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param3.value = 2.0

        # Parameter 4: Longitudinal Grade
        param4 = arcpy.Parameter(
            displayName="Creek Longitudinal Grade (%)",
            name="grade_percent",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param4.value = -3.5

        # Parameter 5: Side Slope
        param5 = arcpy.Parameter(
            displayName="Side Slope (H:V) - From Boundary Inward",
            name="side_slope_hv",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param5.value = 1.5

        # Parameter 6: Point Spacing
        param6 = arcpy.Parameter(
            displayName="Point Spacing (m)",
            name="pt_spacing",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param6.value = 2.0

        # Parameter 7: Processing Buffer
        param7 = arcpy.Parameter(
            displayName="Processing Buffer (m)",
            name="proc_buffer_m",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param7.value = 25.0

        # Parameter 8: Output DEM
        param8 = arcpy.Parameter(
            displayName="Output DEM",
            name="out_dem",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Output")

        # Parameter 9: Output Design Surface
        param9 = arcpy.Parameter(
            displayName="Output Design Surface",
            name="out_design",
            datatype="DERasterDataset",
            parameterType="Optional",
            direction="Output")

        # Parameter 10: Output Points
        param10 = arcpy.Parameter(
            displayName="Output Control Points",
            name="out_points",
            datatype="DEFeatureClass",
            parameterType="Optional",
            direction="Output")

        params = [param0, param1, param2, param3, param4, param5, 
                  param6, param7, param8, param9, param10]
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
        in_poly = parameters[2].valueAsText
        cut_depth = parameters[3].value
        grade_percent = parameters[4].value
        side_slope_hv = parameters[5].value
        pt_spacing = parameters[6].value
        proc_buffer_m = parameters[7].value
        out_dem = parameters[8].valueAsText
        out_design = parameters[9].valueAsText
        out_points = parameters[10].valueAsText

        # Workspace
        arcpy.env.workspace = arcpy.env.scratchGDB
        arcpy.env.scratchWorkspace = arcpy.env.scratchGDB
        tmp_gdb = arcpy.env.scratchGDB
        arcpy.env.snapRaster = in_dem
        arcpy.env.cellSize = in_dem
        dem_sr = arcpy.Describe(in_dem).spatialReference
        arcpy.env.outputCoordinateSystem = dem_sr

        arcpy.AddMessage("=" * 60)
        arcpy.AddMessage("TRAPEZOIDAL DEBRIS BASIN DESIGN")
        arcpy.AddMessage("=" * 60)

        # Copy inputs
        arcpy.AddMessage("Copying input features...")
        tmp_line = arcpy.management.CopyFeatures(in_line, f"{tmp_gdb}\\cline")[0]
        tmp_poly = arcpy.management.CopyFeatures(in_poly, f"{tmp_gdb}\\poly")[0]

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
            tmp_poly, f"{tmp_gdb}\\mask", f"{proc_buffer_m} Meters"
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

        # Extract ground elevations at centreline points
        arcpy.AddMessage("Extracting ground elevations...")
        tmp_pts_z = f"{tmp_gdb}\\pts_z"
        ExtractValuesToPoints(tmp_pts, in_dem, tmp_pts_z)

        # Add fields
        arcpy.AddMessage("Adding fields...")
        for f, t in [("CHAIN_M", "DOUBLE"), ("Z_GROUND", "DOUBLE"), ("ZINV", "DOUBLE"), 
                     ("SRC_ID", "LONG"), ("ZINV_INT", "LONG")]:
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

        z_invert_start = z_ground_start - cut_depth

        arcpy.AddMessage("-" * 60)
        arcpy.AddMessage("DESIGN PARAMETERS:")
        arcpy.AddMessage(f"  Centreline length: {line_length:.1f} m")
        arcpy.AddMessage(f"  Ground at upstream: {start_elev:.2f} m")
        arcpy.AddMessage(f"  Ground at downstream: {end_elev:.2f} m")
        arcpy.AddMessage(f"  Design invert at start: {z_invert_start:.2f} m")
        arcpy.AddMessage(f"  Cut depth at centreline: {cut_depth:.2f} m")
        arcpy.AddMessage(f"  Longitudinal grade: {grade_percent:.2f}%")
        arcpy.AddMessage(f"  Side slope: {side_slope_hv:.1f}H:1V")
        arcpy.AddMessage("-" * 60)

        # Calculate invert elevations along centreline
        arcpy.AddMessage("Calculating design inverts along centreline...")
        
        with arcpy.da.UpdateCursor(tmp_pts_z, 
                                   ["OID@", "SHAPE@", "RASTERVALU", "CHAIN_M", 
                                    "Z_GROUND", "ZINV", "SRC_ID", "ZINV_INT"]) as uc:
            for oid, shp, raster_val, _, _, _, _, _ in uc:
                s = line_geom.measureOnLine(shp)
                z_ground = raster_val if raster_val else z_ground_start
                z_invert = z_invert_start + grade_dec * s
                z_int = int(round(z_invert * 10000))
                uc.updateRow((oid, shp, z_ground, s, z_ground, z_invert, oid, z_int))

        z_invert_end = z_invert_start + grade_dec * line_length
        arcpy.AddMessage(f"Design invert at end: {z_invert_end:.2f} m")

        # Save control points
        if out_points:
            arcpy.management.CopyFeatures(tmp_pts_z, out_points)
            arcpy.AddMessage("Control points saved")

        # Get creek invert surface (allocated from centreline points)
        arcpy.AddMessage("Creating creek invert surface...")
        alloc_zinv_int = EucAllocation(
            in_source_data=tmp_pts_z,
            source_field="ZINV_INT",
            cell_size=in_dem
        )
        
        z_creek_invert = alloc_zinv_int / 10000.0

        # Get distance from polygon boundary (INWARD)
        arcpy.AddMessage("Calculating distances from basin boundary...")
        tmp_poly_line = f"{tmp_gdb}\\poly_line"
        arcpy.management.PolygonToLine(tmp_poly, tmp_poly_line)
        
        dist_from_boundary = EucDistance(
            in_source_data=tmp_poly_line,
            cell_size=in_dem
        )

        # Sample ground elevation across entire basin
        arcpy.AddMessage("Sampling ground elevations across basin...")
        dem_raster = arcpy.sa.Raster(in_dem)
        z_ground_basin = ExtractByMask(dem_raster, tmp_poly)

        # Create trapezoidal design surface
        arcpy.AddMessage("Creating trapezoidal design surface...")
        
        # Elevation sloping down from boundary: z_ground - (distance_inward / H:V)
        z_from_boundary = z_ground_basin - (dist_from_boundary / side_slope_hv)
        
        # Design surface = MAX of (creek invert, sloped surface from boundary)
        # This creates flat bottom where slopes meet creek invert
        zdesign = Con(z_from_boundary > z_creek_invert, 
                     z_from_boundary,  # Still on side slope
                     z_creek_invert)   # Reached flat bottom at creek invert
        
        # Limit to polygon
        zdesign = ExtractByMask(zdesign, tmp_poly)

        # Save design surface
        if out_design:
            zdesign.save(out_design)
            arcpy.AddMessage("Design surface saved")

        # Cut DEM
        arcpy.AddMessage("Cutting DEM with design surface...")
        dem_new = Con(IsNull(zdesign), dem_raster, 
                     Con(zdesign < dem_raster, zdesign, dem_raster))
        
        dem_new.save(out_dem)
        arcpy.AddMessage("Output DEM saved")

        # Calculate statistics
        arcpy.AddMessage("Calculating cut volume...")
        cut_depth_raster = Con(dem_raster > zdesign, dem_raster - zdesign, 0)
        cut_depth_masked = ExtractByMask(cut_depth_raster, tmp_poly)
        
        try:
            cell_size_val = float(arcpy.env.cellSize)
            cell_area = cell_size_val ** 2
            mean_cut = float(arcpy.management.GetRasterProperties(cut_depth_masked, "MEAN").getOutput(0))
            max_cut_raster = float(arcpy.management.GetRasterProperties(cut_depth_masked, "MAXIMUM").getOutput(0))
            cell_count = float(arcpy.management.GetRasterProperties(cut_depth_masked, "VALUECOUNT").getOutput(0))
            cut_volume = mean_cut * cell_count * cell_area
            basin_area = cell_count * cell_area
            
            arcpy.AddMessage("-" * 60)
            arcpy.AddMessage("RESULTS:")
            arcpy.AddMessage(f"  Cut volume: {cut_volume:.1f} m³")
            arcpy.AddMessage(f"  Basin area: {basin_area:.1f} m²")
            arcpy.AddMessage(f"  Average cut depth: {mean_cut:.2f} m")
            arcpy.AddMessage(f"  Maximum cut depth: {max_cut_raster:.2f} m")
            arcpy.AddMessage("-" * 60)
        except Exception as e:
            arcpy.AddMessage(f"Could not calculate statistics: {str(e)}")

        arcpy.AddMessage("=" * 60)
        arcpy.AddMessage("PROCESS COMPLETE")
        arcpy.AddMessage("=" * 60)
        
        arcpy.CheckInExtension("Spatial")
        return