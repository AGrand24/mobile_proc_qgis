import numpy as np
import pandas as pd
import geopandas as gpd
import struct
from pykrige.ok import OrdinaryKriging
from shapely import Point, MultiPoint


def kriging(meas):
    data = meas.data.copy()
    data = data.dropna(subset="voltage_norm")
    data = data.query("attribute == 'meas'")

    x = data["x"].values
    y = data["y"].values
    z = data["voltage_norm"].values

    x0 = min(x) - 5
    y0 = min(y) - 5
    x100 = max(x) + 5
    y100 = max(y) + 5

    cell_size = 0.25
    cells_x = int((x100 - x0) / cell_size)
    cells_y = int((y100 - y0) / cell_size)

    grid_x = np.linspace(x0, x100, cells_x)
    grid_y = np.linspace(y0, y100, cells_y)

    ok = OrdinaryKriging(x, y, z, variogram_model="exponential", exact_values=True)

    grid_z, ss = ok.execute("grid", grid_x, grid_y)
    grid_z = np.round(grid_z, 3)
    mesh = np.meshgrid(grid_x, grid_y)

    # mesh[2] = grid_z.data
    return mesh[0], mesh[1], grid_z.data


def mask_grid(meas):

    grid_x = meas.grid_x
    grid_y = meas.grid_y
    grid_z = meas.grid_z_full

    polygon = meas.extents
    z_flat = grid_z.flatten()

    points = gpd.GeoSeries(gpd.points_from_xy(grid_x.flatten(), grid_y.flatten()))
    polygon = meas.extents["geometry"].iloc[0]
    mask = polygon.contains(points)
    mask = np.where(mask == False)
    z_flat[mask] = np.nan
    grid_z_masked = z_flat.reshape(grid_z.shape)
    return grid_z_masked


# def mask_grid(df, grid, x, y):
#     df = df[[x, y, "dV_norm"]]
#     df = df.dropna().reset_index(drop=True)

#     gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[x], df[y], crs=4326))

#     polygon = gpd.GeoSeries(MultiPoint(gdf["geometry"])).concave_hull(0.2)

#     xx, yy = np.meshgrid(grid.easting, grid.northing)
#     coords = list(zip(xx.flatten(), yy.flatten()))
#     coords = [Point(c) for c in coords]

#     mask = []
#     for points in coords:
#         mask.append(polygon.contains(points))

#     z = np.array(grid.elevation).flatten()
#     for i, m in enumerate(mask):
#         if m[0] == False:
#             z[i] = np.nan

#     grid_z_masked = z.reshape(grid.elevation.shape)
#     return grid_z_masked


def export_surfer_grid(data_array, x_coords, y_coords, output_file):
    """
    Saves a NumPy 2D array to a Surfer 6 Binary Grid file.

    Args:
        data_array (np.ndarray): The 2D NumPy array of grid values.
                                 The shape should be (ny, nx).
        x_coords (np.ndarray): 1D array of the X-coordinates for the columns.
        y_coords (np.ndarray): 1D array of the Y-coordinates for the rows.
        output_file (str): Path to the output .grd file.
    """
    # Surfer's NoData value
    no_data_value = 1.70141e38

    # Get grid dimensions from the array shape
    ny, nx = data_array.shape

    # Get spatial extents from coordinate arrays
    xlo, xhi = x_coords.min(), x_coords.max()
    ylo, yhi = y_coords.min(), y_coords.max()

    # Handle NaN values and find Z extents
    # Replace any np.nan with Surfer's NoData value
    grid_data = np.nan_to_num(data_array, nan=no_data_value)

    # Find min/max Z values, ignoring the NoData value
    zlo = grid_data[grid_data != no_data_value].min()
    zhi = grid_data[grid_data != no_data_value].max()

    # Open the file for binary writing
    with open(output_file, "wb") as f:
        # --- Write the Header ---
        # Pack the header values into a binary string.
        # '<' denotes little-endian byte order.
        # '4s' = 4-char string
        # 'h' = short integer (2 bytes)
        # 'd' = double (8 bytes)
        header_format = "<4shh6d"
        header = struct.pack(
            header_format,
            b"DSBB",  # Binary file identifier
            nx,
            ny,
            xlo,
            xhi,
            ylo,
            yhi,
            zlo,
            zhi,
        )
        f.write(header)

        # --- Write the Data ---
        # Ensure data is in 4-byte float format and flatten it.
        # Surfer grids are written from bottom-left, row by row.
        # NumPy arrays are indexed from top-left, so we don't need to flip.
        flat_data = grid_data.astype(np.float32).flatten()

        # Write the flattened array to the file
        f.write(flat_data.tobytes())
