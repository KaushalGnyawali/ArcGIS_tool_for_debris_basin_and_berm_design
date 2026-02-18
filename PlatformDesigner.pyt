import arcpy
from arcpy.sa import Con, IsNull, ExtractByMask, Spline, Idw, TopoToRaster, EucDistance
import numpy as np


class Toolbox(object):
    def __init__(self):
        self.label = "Platform Designer Toolbox"
        self.alias = "platformdesigner"
        self.tools = [PlatformDesignerTool]


class PlatformDesignerTool(object):
    def __init__(self):
        self.label = "Platform Designer"
        self.description = "Creates platform on terrain from vertex elevations"
        self.canRunInBackground = False

    def getParameterInfo(self):
        # Parameter 0: Input DEM
        param0 = arcpy.Parameter(
            displayName="Input DEM",
            name="in_dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        # Parameter 1: Platform Vertices (Points)
        param1 = arcpy.Parameter(
            displayName="Platform Vertices (Points)",
            name="in_points",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["Point"]

        # Parameter 2: Elevation Field
        param2 = arcpy.Parameter(
            displayName="Elevation Field",
            name="elev_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param2.parameterDependencies = [param1.name]
        param2.filter.list = ["Short", "Long", "Float", "Double"]

        # Parameter 3: Point Order Field (Optional)
        param3 = arcpy.Parameter(
            displayName="Point Order Field (Optional - for ordered polygon)",
            name="order_field",
            datatype="Field",
            parameterType="Optional",
            direction="Input")
        param3.parameterDependencies = [param1.name]
        param3.filter.list = ["Short", "Long"]

        # Parameter 4: Interpolation Method
        param4 = arcpy.Parameter(
            displayName="Interpolation Method",
            name="interp_method",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param4.filter.type = "ValueList"
        param4.filter.list = ["Spline", "IDW", "Natural Neighbor"]
        param4.value = "Spline"

        # Parameter 5: Platform Type
        param5 = arcpy.Parameter(
            displayName="Platform Type",
            name="platform_type",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param5.filter.type = "ValueList"
        param5.filter.list = ["Cut and Fill", "Cut Only", "Fill Only"]
        param5.value = "Cut and Fill"

        # Parameter 6: Edge Buffer (m)
        param6 = arcpy.Parameter(
            displayName="Edge Transition Buffer (m)",
            name="edge_buffer",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input")
        param6.value = 2.0

        # Parameter 7: Output DEM
        param7 = arcpy.Parameter(
            displayName="Output DEM",
            name="out_dem",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Output")

        # Parameter 8: Output Platform Polygon
        param8 = arcpy.Parameter(
            displayName="Output Platform Polygon (Optional)",
            name="out_polygon",
            datatype="DEFeatureClass",
            parameterType="Optional",
            direction="Output")

        # Parameter 9: Output Platform Surface
        param9 = arcpy.Parameter(
            displayName="Output Platform Surface (Optional)",
            name="out_surface",
            datatype="DERasterDataset",
            parameterType="Optional",
            direction="Output")

        params = [param0, param1, param2, param3, param4, param5, param6, 
                  param7, param8, param9]
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
        arcpy.CheckOutExtension("3D")
        arcpy.env.overwriteOutput = True

        # Get parameters
        in_dem = parameters[0].valueAsText
        in_points = parameters[1].valueAsText
        elev_field = parameters[2].valueAsText
        order_field = parameters[3].valueAsText
        interp_method = parameters[4].valueAsText
        platform_type = parameters[5].valueAsText
        edge_buffer = parameters[6].value if parameters[6].value else 0.0
        out_dem = parameters[7].valueAsText
        out_polygon = parameters[8].valueAsText
        out_surface = parameters[9].valueAsText

        # Workspace
        arcpy.env.workspace = arcpy.env.scratchGDB
        tmp_gdb = arcpy.env.scratchGDB
        arcpy.env.snapRaster = in_dem
        arcpy.env.cellSize = in_dem

        arcpy.AddMessage("=" * 60)
        arcpy.AddMessage("PLATFORM DESIGNER")
        arcpy.AddMessage("=" * 60)

        # Copy input points
        arcpy.AddMessage("Copying input vertices...")
        tmp_points = arcpy.management.CopyFeatures(in_points, f"{tmp_gdb}\\platform_pts")[0]

        # Count points
        point_count = int(arcpy.management.GetCount(tmp_points)[0])
        arcpy.AddMessage(f"Number of vertices: {point_count}")

        if point_count < 3:
            arcpy.AddError("Error: Need at least 3 points to create polygon")
            return

        # Check elevation field exists and has valid values
        arcpy.AddMessage(f"Using elevation field: {elev_field}")
        
        elevations = []
        with arcpy.da.SearchCursor(tmp_points, [elev_field]) as cursor:
            for row in cursor:
                if row[0] is not None:
                    elevations.append(row[0])

        if len(elevations) == 0:
            arcpy.AddError(f"Error: No valid elevation values in field {elev_field}")
            return

        min_elev = min(elevations)
        max_elev = max(elevations)
        avg_elev = sum(elevations) / len(elevations)

        arcpy.AddMessage(f"Elevation range: {min_elev:.2f} to {max_elev:.2f} m")
        arcpy.AddMessage(f"Average elevation: {avg_elev:.2f} m")

        # Create polygon from points
        arcpy.AddMessage("Creating platform polygon...")
        
        if order_field:
            arcpy.AddMessage(f"Using point order from field: {order_field}")
            # Sort points by order field
            tmp_points_sorted = arcpy.management.Sort(
                tmp_points, f"{tmp_gdb}\\pts_sorted", [[order_field, "ASCENDING"]]
            )[0]
            
            # Create line from ordered points
            tmp_line = arcpy.management.PointsToLine(
                tmp_points_sorted, f"{tmp_gdb}\\platform_line"
            )[0]
            
            # Close the polygon
            arcpy.edit.Densify(tmp_line, "DISTANCE", "0.1 Meters")
            
            # Convert to polygon
            tmp_polygon = arcpy.management.FeatureToPolygon(
                tmp_line, f"{tmp_gdb}\\platform_poly"
            )[0]
        else:
            arcpy.AddMessage("Creating convex hull polygon...")
            # Create minimum bounding geometry (convex hull)
            tmp_polygon = arcpy.management.MinimumBoundingGeometry(
                tmp_points, f"{tmp_gdb}\\platform_poly", "CONVEX_HULL"
            )[0]

        # Get polygon area
        with arcpy.da.SearchCursor(tmp_polygon, ["SHAPE@AREA"]) as cursor:
            poly_area = next(cursor)[0]
        
        arcpy.AddMessage(f"Platform area: {poly_area:.1f} m2 ({poly_area/10000:.3f} ha)")

        # Save polygon if requested
        if out_polygon:
            arcpy.management.CopyFeatures(tmp_polygon, out_polygon)
            arcpy.AddMessage("Platform polygon saved")

        # Set extent to polygon with buffer
        buffer_dist = max(edge_buffer * 2, 10.0)
        tmp_extent = arcpy.analysis.Buffer(
            tmp_polygon, f"{tmp_gdb}\\extent_buffer", f"{buffer_dist} Meters"
        )[0]
        arcpy.env.extent = tmp_extent
        arcpy.env.mask = tmp_extent

        # Interpolate platform surface from vertices
        arcpy.AddMessage(f"Interpolating platform surface using {interp_method}...")
        
        cell_size = float(arcpy.management.GetRasterProperties(in_dem, "CELLSIZEX").getOutput(0))
        
        try:
            if interp_method == "Spline":
                platform_surface = Spline(tmp_points, elev_field, cell_size)
            elif interp_method == "IDW":
                platform_surface = Idw(tmp_points, elev_field, cell_size, 2)
            else:  # Natural Neighbor
                platform_surface = TopoToRaster(
                    [[tmp_points, elev_field, "PointElevation"]],
                    cell_size
                )
        except Exception as e:
            arcpy.AddWarning(f"Primary interpolation failed: {str(e)}")
            arcpy.AddMessage("Falling back to IDW interpolation...")
            platform_surface = Idw(tmp_points, elev_field, cell_size, 2)

        # Load original DEM
        arcpy.AddMessage("Loading original DEM...")
        dem_raster = arcpy.sa.Raster(in_dem)

        # Extract platform surface to polygon only
        arcpy.AddMessage("Extracting platform surface to polygon area...")
        platform_inside = ExtractByMask(platform_surface, tmp_polygon)

        # Apply edge transition if buffer specified
        if edge_buffer > 0:
            arcpy.AddMessage(f"Creating {edge_buffer}m edge transition zone...")
            
            # Create inner polygon
            tmp_inner = arcpy.analysis.Buffer(
                tmp_polygon, f"{tmp_gdb}\\inner_poly", f"-{edge_buffer} Meters"
            )[0]
            
            # Check if inner polygon exists
            inner_count = int(arcpy.management.GetCount(tmp_inner)[0])
            
            if inner_count > 0:
                # Create transition zone
                tmp_transition = arcpy.analysis.Erase(
                    tmp_polygon, tmp_inner, f"{tmp_gdb}\\transition_zone"
                )[0]
                
                # Extract surfaces
                platform_inner = ExtractByMask(platform_surface, tmp_inner)
                dem_transition = ExtractByMask(dem_raster, tmp_transition)
                platform_transition = ExtractByMask(platform_surface, tmp_transition)
                
                # Blend in transition zone
                dist_from_edge = EucDistance(tmp_inner, cell_size=cell_size)
                dist_from_edge_masked = ExtractByMask(dist_from_edge, tmp_transition)
                
                # Weight: 0 at outer edge, 1 at inner edge
                weight = dist_from_edge_masked / edge_buffer
                weight = Con(weight > 1, 1, weight)
                weight = Con(weight < 0, 0, weight)
                
                blended_transition = dem_transition * (1 - weight) + platform_transition * weight
                
                # Combine
                platform_final = Con(IsNull(platform_inner), blended_transition, platform_inner)
            else:
                arcpy.AddMessage("Polygon too small for edge buffer, using sharp boundary")
                platform_final = platform_inside
        else:
            platform_final = platform_inside

        # Apply platform type logic
        arcpy.AddMessage(f"Applying platform type: {platform_type}...")
        
        dem_at_platform = ExtractByMask(dem_raster, tmp_polygon)
        
        if platform_type == "Cut and Fill":
            modified_surface = platform_final
            
        elif platform_type == "Cut Only":
            modified_surface = Con(platform_final < dem_at_platform, 
                                  platform_final, 
                                  dem_at_platform)
            
        elif platform_type == "Fill Only":
            modified_surface = Con(platform_final > dem_at_platform,
                                  platform_final,
                                  dem_at_platform)

        # Save platform surface if requested
        if out_surface:
            modified_surface.save(out_surface)
            arcpy.AddMessage("Platform surface saved")

        # Create output DEM
        arcpy.AddMessage("Creating output DEM...")
        arcpy.env.extent = in_dem
        arcpy.env.mask = None
        
        dem_output = Con(IsNull(modified_surface), dem_raster, modified_surface)
        dem_output.save(out_dem)
        arcpy.AddMessage("Output DEM saved")

        # Calculate comprehensive cut/fill volumes
        arcpy.AddMessage("Calculating cut and fill volumes...")
        
        try:
            # Calculate difference
            diff = dem_at_platform - modified_surface
            cut_depth = Con(diff > 0, diff, 0)
            fill_depth = Con(diff < 0, -diff, 0)
            
            cell_area = cell_size * cell_size
            
            # Convert to arrays for accurate calculation
            cut_array = arcpy.RasterToNumPyArray(cut_depth, nodata_to_value=0)
            fill_array = arcpy.RasterToNumPyArray(fill_depth, nodata_to_value=0)
            
            # Get cells with cut/fill
            cut_cells = cut_array[cut_array > 0]
            fill_cells = fill_array[fill_array > 0]
            
            # Calculate volumes
            cut_sum = float(np.sum(cut_cells))
            fill_sum = float(np.sum(fill_cells))
            
            cut_volume = cut_sum * cell_area
            fill_volume = fill_sum * cell_area
            net_volume = cut_volume - fill_volume
            
            # Calculate areas and depths
            cut_area = len(cut_cells) * cell_area
            fill_area = len(fill_cells) * cell_area
            
            avg_cut_depth = cut_sum / len(cut_cells) if len(cut_cells) > 0 else 0
            avg_fill_depth = fill_sum / len(fill_cells) if len(fill_cells) > 0 else 0
            
            max_cut = float(np.max(cut_cells)) if len(cut_cells) > 0 else 0
            max_fill = float(np.max(fill_cells)) if len(fill_cells) > 0 else 0
            
            # Display comprehensive results
            arcpy.AddMessage("")
            arcpy.AddMessage("=" * 60)
            arcpy.AddMessage("PLATFORM STATISTICS")
            arcpy.AddMessage("=" * 60)
            
            arcpy.AddMessage("")
            arcpy.AddMessage("PLATFORM GEOMETRY:")
            arcpy.AddMessage(f"  Total platform area: {poly_area:.1f} m2")
            arcpy.AddMessage(f"  Total platform area: {poly_area/10000:.3f} hectares")
            arcpy.AddMessage(f"  Cut area: {cut_area:.1f} m2 ({cut_area/poly_area*100:.1f}% of platform)")
            arcpy.AddMessage(f"  Fill area: {fill_area:.1f} m2 ({fill_area/poly_area*100:.1f}% of platform)")
            
            arcpy.AddMessage("")
            arcpy.AddMessage("CUT VOLUME (Excavation):")
            arcpy.AddMessage(f"  Total cut: {cut_volume:.1f} m3")
            arcpy.AddMessage(f"  Total cut: {cut_volume/1000:.2f} thousand m3")
            arcpy.AddMessage(f"  Average cut depth: {avg_cut_depth:.2f} m")
            arcpy.AddMessage(f"  Maximum cut depth: {max_cut:.2f} m")
            if cut_volume > 0:
                arcpy.AddMessage(f"  Truck loads (15 m3): {int(cut_volume/15)} loads")
                arcpy.AddMessage(f"  Weight (1.8 t/m3): {int(cut_volume * 1.8):,} tonnes")
            
            arcpy.AddMessage("")
            arcpy.AddMessage("FILL VOLUME (Embankment):")
            arcpy.AddMessage(f"  Total fill: {fill_volume:.1f} m3")
            arcpy.AddMessage(f"  Total fill: {fill_volume/1000:.2f} thousand m3")
            arcpy.AddMessage(f"  Average fill depth: {avg_fill_depth:.2f} m")
            arcpy.AddMessage(f"  Maximum fill depth: {max_fill:.2f} m")
            if fill_volume > 0:
                arcpy.AddMessage(f"  Compacted volume: {fill_volume:.1f} m3")
                arcpy.AddMessage(f"  Loose volume (1.25 factor): {fill_volume * 1.25:.1f} m3")
                arcpy.AddMessage(f"  Truck loads (15 m3): {int(fill_volume * 1.25 / 15)} loads")
            
            arcpy.AddMessage("")
            arcpy.AddMessage("NET EARTHWORK:")
            arcpy.AddMessage(f"  Cut volume: {cut_volume:.1f} m3")
            arcpy.AddMessage(f"  Fill volume: {fill_volume:.1f} m3")
            arcpy.AddMessage(f"  Net volume: {net_volume:.1f} m3")
            
            if abs(net_volume) < 1.0:
                arcpy.AddMessage(f"  STATUS: Balanced cut/fill")
            elif net_volume > 0:
                arcpy.AddMessage(f"  STATUS: {abs(net_volume):.1f} m3 EXCESS CUT (remove from site)")
                arcpy.AddMessage(f"         {int(abs(net_volume)/15)} truck loads to haul away")
            else:
                arcpy.AddMessage(f"  STATUS: {abs(net_volume):.1f} m3 EXCESS FILL (import to site)")
                arcpy.AddMessage(f"         {int(abs(net_volume) * 1.25 / 15)} truck loads to bring in")
            
            arcpy.AddMessage("")
            arcpy.AddMessage("EARTHWORK SUMMARY:")
            arcpy.AddMessage(f"  Total earthwork: {cut_volume + fill_volume:.1f} m3")
            arcpy.AddMessage(f"  Cut/Fill ratio: {cut_volume/fill_volume:.2f}" if fill_volume > 0 else "  Cut/Fill ratio: All cut")
            arcpy.AddMessage(f"  Volume per m2: {(cut_volume + fill_volume)/poly_area:.2f} m3/m2")
            
            arcpy.AddMessage("")
            arcpy.AddMessage("=" * 60)
            
        except Exception as e:
            arcpy.AddWarning(f"Could not calculate volumes: {str(e)}")
            import traceback
            arcpy.AddWarning(traceback.format_exc())

        arcpy.AddMessage("")
        arcpy.AddMessage("=" * 60)
        arcpy.AddMessage("PLATFORM DESIGN COMPLETE")
        arcpy.AddMessage("=" * 60)
        
        arcpy.CheckInExtension("Spatial")
        arcpy.CheckInExtension("3D")
        return
