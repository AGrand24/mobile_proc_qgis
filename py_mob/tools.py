import plotly.graph_objects as go
import pandas as pd


def plot_paths(df):
    fig = go.Figure()

    for line in df.line.unique():
        gb = df.loc[df["line"] == line]
        mk = dict(symbol="arrow", angle=gb["heading"])
        cd = gb[
            ["hdg_fwd", "hdg_bck", "d_hdg", "d_dst", "ID_point", "split", "split_k"]
        ].values
        ht = "%{customdata[0]}<br>%{customdata[1]}<br>%{customdata[2]}<br>%{customdata[3]}<br>%{customdata[4]}<br>%{customdata[5]}<br>%{customdata[6]}<extra></extra>"
        sc = go.Scatter(
            x=gb["x"],
            y=gb["y"],
            mode="markers",
            customdata=cd,
            hovertemplate=ht,
            marker=mk,
        )
        fig.add_trace(sc)
    fig.update_yaxes(scaleanchor="x1")
    fig.update_layout(width=800, height=800)


from exif import Image
from py_mob.get_ld import get_ld
import geopandas as gpd
from pathlib import Path


def decimal_coords(coords, ref):
    decimal_degrees = coords[0] + coords[1] / 60 + coords[2] / 3600
    if ref == "S" or ref == "W":
        decimal_degrees = -decimal_degrees
    return decimal_degrees


def image_coordinates(image_path):

    with open(image_path, "rb") as src:
        img = Image(src)
    if img.has_exif:
        try:
            img.gps_longitude
            coords = (
                decimal_coords(img.gps_latitude, img.gps_latitude_ref),
                decimal_coords(img.gps_longitude, img.gps_longitude_ref),
            )
        except AttributeError:
            print("No Coordinates")
    else:
        print("The Image has no EXIF information")

    return {
        "t": img.datetime_original,
        "lat": coords[0],
        "lon": coords[1],
    }


def photos2gpkg():
    time = []
    lon = []
    lat = []
    id = []
    for fp in get_ld("doc/photo/", ext="jpg")["fp"]:
        print(fp)
        ex = image_coordinates(fp)
        time.append(ex["t"])
        lon.append(ex["lon"])
        lat.append(ex["lat"])
        id.append(Path(fp).name[:2])

    geom = gpd.points_from_xy(lon, lat)
    data = {"time": time, "lon": lon, "lat": lat, "name": id}
    gdf = gpd.GeoDataFrame(data=data, geometry=geom, crs=4326)
    gdf.to_file("tmp/photos.gpkg")
