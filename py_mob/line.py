import numpy as np
from shapely import LineString
import geopandas as gpd
import pandas as pd
from .angles import angle_360, angle_signed


def get_lines(df):
    df["split_k"] = df["d_dst"] * (df["d_hdg"]) ** 2
    df["split"] = 0
    df.loc[df["split_k"] > 1000, "split"] = 1

    mask = np.max(df[["dst_fwd", "dst_bck"]], axis=1) > 4
    df.loc[mask, "split"] = 1

    for i in range(1, len(df)):
        if df["split"][i] == df["split"][i - 1]:
            df.loc[i, "split"] = 0

    l = 0
    line = []
    for s in df["split"]:
        line.append(l)
        if s == 1:
            l += 1
    df["line"] = line

    return df


def split_lines(df):

    gb = df.groupby("ID_line", as_index=False)[["x", "y"]].agg(list)

    geom = []
    for x, y in zip(gb["x"], gb["y"]):
        coords = list(zip(x, y))
        if len(coords) < 2:
            coords.append(coords[0])
        geom.append(LineString(coords))
    gdf = gpd.GeoDataFrame(
        data={"ID_line": gb["ID_line"]},
        geometry=geom,
        crs=3857,
    )
    return gdf


def get_line_data(df, df_path):
    for col in ["hdg_fwd", "compass"]:

        df["cos"] = np.cos(np.deg2rad(df[col]))
        df["sin"] = np.sin(np.deg2rad(df[col]))
        line_data = df.groupby("ID_line")[["cos", "sin"]].agg("median")
        line_data[col] = np.rad2deg(np.atan2(line_data["sin"], line_data["cos"]))
        line_data[col] = angle_360(line_data[col])
        line_data = line_data.add_prefix("line_")
        line_data = line_data[[f"line_{col}"]]
        df = pd.merge(df, line_data, how="left", left_on="ID_line", right_index=True)

    df["line_hdg_diff"] = np.abs(angle_signed(df["line_hdg_fwd"] - df["line_compass"]))

    df_path["line_len"] = [np.round(g.length, 2) for g in df_path["geometry"]]
    df = pd.merge(
        df,
        df_path.set_index("ID_line")["line_len"],
        how="left",
        left_on="ID_line",
        right_index=True,
    )

    return df


def calc_pt_hdg(df, reverse):
    x = df["x"]
    y = df["y"]
    if reverse == True:
        x = x.iloc[::-1]
        y = y.iloc[::-1]

    dx = np.diff(x)
    dy = np.diff(y)
    bearing = np.atan2(dx, dy)
    bearing = np.rad2deg(bearing)
    dist = (dx**2 + dy**2) ** 0.5

    if reverse == True:
        bearing = bearing[::-1]
        bearing += 180
        bearing %= 360
        bearing = np.insert(bearing, 0, np.nan)
        dist = np.nan
    else:
        bearing = np.append(bearing, np.nan)
        dist = np.append(dist, np.nan)
        bearing[bearing < 0] += 360

    bearing = np.round(bearing, 2)
    dist = np.round(dist, 2)

    return bearing, dist


def get_pt_hdg(df):
    df = df.loc[df["attribute"] == "meas"]
    df = df.reset_index(drop=True)
    bearing, dist = calc_pt_hdg(df, reverse=False)
    df["dst_fwd"] = dist
    df["hdg_fwd"] = bearing

    bearing, dist = calc_pt_hdg(df, reverse=True)
    df["dst_bck"] = df["dst_fwd"].shift(1)
    df["hdg_bck"] = bearing

    df["d_hdg"] = np.abs(df["hdg_fwd"] - df["hdg_bck"])
    mask = np.abs(df["d_hdg"]) > 180
    df.loc[mask, "d_hdg"] -= 360
    df["d_hdg"] = np.abs(df["d_hdg"])

    df["d_dst"] = np.min(df[["dst_fwd", "dst_bck"]], axis=1)

    return df


def calc_line_pos(df):
    df = df.dropna(subset="ID_line")
    index = df["ID"]
    line_pos = np.array([])
    line_pts = np.array([])

    for line in df["ID_line"].unique():
        df_line = df.loc[df["ID_line"] == line]
        n = len(df_line)
        tmp = np.arange(0, n, 1)
        tmp = tmp / np.max(tmp)
        line_pos = np.append(line_pos, tmp)

        tmp = np.tile(n, n)
        line_pts = np.append(line_pts, tmp)

    line_pos[np.isnan(line_pos) == True] = 0
    line_pts_norm = line_pts / np.quantile(line_pts, 0.25)
    line_pts_norm = np.clip(line_pts_norm, 0, 1)

    return index, line_pos, line_pts, line_pts_norm
