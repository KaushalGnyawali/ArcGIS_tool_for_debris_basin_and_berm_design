import arcpy
from arcpy.sa import Con, ExtractByMask, Raster
import numpy as np


class Toolbox(object):
    def __init__(self):
        self.label = "Basin Volume Calculator"
        self.alias = "basinvol"
        self.tools = [BasinVolume]


class BasinVolume(object):
    def __init__(self):
        self.label = "Basin Storage Volume"
        self.description = "Calculate basin excavation volume"
        self.canRunInBackground = False

    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName="DEM with Basin",
            name="basin_dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param1 = arcpy.Parameter(
            displayName="Basin Polygon",
            name="basin_poly",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["Polygon"]

        params = [param0, param1]
        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        arcpy.CheckOutExtension("Spatial")
        arcpy.CheckOutExtension("3D")
        arcpy.env.overwriteOutput = True

        basin_dem = parameters[0].valueAsText
        basin_poly = parameters[1].valueAsText

        arcpy.AddMessage("=" * 60)
        arcpy.AddMessage("BASIN VOLUME CALCULATOR")
        arcpy.AddMessage("=" * 60)

        # Workspace
        arcpy.env.workspace = arcpy.env.scratchGDB
        arcpy.env.snapRaster = basin_dem
        arcpy.env.cellSize = basin_dem
        
        dem_raster = Raster(basin_dem)
        cell_size = float(arcpy.management.GetRasterProperties(basin_dem, "CELLSIZEX").getOutput(0))
        cell_area = cell_size * cell_size

        # Convert polygon boundary to line
        arcpy.AddMessage("Extracting basin boundary...")
        boundary_line = arcpy.management.PolygonToLine(basin_poly, "boundary_line")[0]

        # Create dense points along boundary
        arcpy.AddMessage("Creating boundary sample points...")
        spacing = cell_size / 2.0  # Half cell size for dense sampling
        boundary_points = arcpy.management.GeneratePointsAlongLines(
            boundary_line, "boundary_pts", "DISTANCE", str(spacing) + " Meters"
        )[0]

        # Sample DEM elevations at boundary points
        arcpy.AddMessage("Sampling rim elevations...")
        from arcpy.sa import ExtractValuesToPoints
        boundary_pts_z = ExtractValuesToPoints(boundary_points, basin_dem, "boundary_pts_z")

        # Interpolate original surface from boundary points using IDW
        arcpy.AddMessage("Interpolating original surface from rim...")
        arcpy.env.extent = basin_poly
        
        # Use IDW with power=2 for smooth interpolation
        original_surface = arcpy.sa.Idw(
            boundary_pts_z, 
            "RASTERVALU",
            cell_size,
            2  # power
        )

        # Mask both surfaces to basin
        arcpy.AddMessage("Calculating cut depth...")
        original_basin = ExtractByMask(original_surface, basin_poly)
        actual_basin = ExtractByMask(dem_raster, basin_poly)

        # Calculate cut depth
        cut_depth = original_basin - actual_basin
        cut_depth = Con(cut_depth > 0, cut_depth, 0)

        # Get statistics
        arcpy.AddMessage("Calculating volume...")
        mean_depth = float(arcpy.management.GetRasterProperties(cut_depth, "MEAN").getOutput(0))
        max_depth = float(arcpy.management.GetRasterProperties(cut_depth, "MAXIMUM").getOutput(0))
        
        # Convert to numpy for accurate sum
        depth_array = arcpy.RasterToNumPyArray(cut_depth, nodata_to_value=0)
        valid_depths = depth_array[depth_array > 0]
        
        sum_depth = float(np.sum(valid_depths))
        cell_count = float(len(valid_depths))
        
        volume = sum_depth * cell_area
        area = cell_count * cell_area

        # Display results
        arcpy.AddMessage("")
        arcpy.AddMessage("=" * 60)
        arcpy.AddMessage("BASIN GEOMETRY")
        arcpy.AddMessage("=" * 60)
        arcpy.AddMessage("Excavation area: " + str(round(area, 1)) + " m2")
        arcpy.AddMessage("Excavation area: " + str(round(area/10000, 3)) + " ha")
        arcpy.AddMessage("")
        arcpy.AddMessage("=" * 60)
        arcpy.AddMessage("EXCAVATION DEPTH")
        arcpy.AddMessage("=" * 60)
        arcpy.AddMessage("Average depth: " + str(round(mean_depth, 2)) + " m")
        arcpy.AddMessage("Maximum depth: " + str(round(max_depth, 2)) + " m")
        arcpy.AddMessage("")
        arcpy.AddMessage("=" * 60)
        arcpy.AddMessage("EXCAVATION VOLUME")
        arcpy.AddMessage("=" * 60)
        arcpy.AddMessage("Total volume: " + str(round(volume, 1)) + " m3")
        arcpy.AddMessage("Total volume: " + str(round(volume/1000, 2)) + " thousand m3")
        arcpy.AddMessage("")
        arcpy.AddMessage("VOLUME PER UNIT:")
        arcpy.AddMessage("  Per m2: " + str(round(volume/area, 2)) + " m3/m2")
        arcpy.AddMessage("  Per hectare: " + str(round(volume/(area/10000), 0)) + " m3/ha")
        arcpy.AddMessage("")
        arcpy.AddMessage("=" * 60)
        arcpy.AddMessage("MATERIAL QUANTITIES")
        arcpy.AddMessage("=" * 60)
        arcpy.AddMessage("Material excavated: " + str(round(volume, 1)) + " m3")
        arcpy.AddMessage("Truck loads (15 m3): " + str(int(round(volume/15))) + " loads")
        arcpy.AddMessage("Weight (1.8 t/m3): " + str(int(round(volume * 1.8))) + " tonnes")
        arcpy.AddMessage("")
        arcpy.AddMessage("METHOD: Interpolated from basin rim elevations")
        arcpy.AddMessage("=" * 60)

        arcpy.CheckInExtension("Spatial")
        arcpy.CheckInExtension("3D")
        return
