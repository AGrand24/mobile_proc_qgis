import pandas as pd
import geopandas as gpd
import numpy as np
from pyproj import Geod
from shapely import Point, LineString
import os
from .angles import angle_360


def calc_compass(df):
    df["cx"] = df["compass_x"] - (np.min(df["compass_x"]) + np.max(df["compass_x"])) / 2
    df["cy"] = df["compass_y"] - (np.min(df["compass_y"]) + np.max(df["compass_y"])) / 2

    df["compass"] = np.atan2(df["cy"], df["cx"])
    df["compass"] = np.rad2deg(df["compass"])

    df["compass"] += 90
    df["compass"] = angle_360(df["compass"])
    return df


def calc_dv_norm(df):
    df["voltage_raw"] = df["voltage_raw"].replace("nan", 0).astype(float)
    df["voltage_norm"] = df["voltage_raw"].round(3)

    df[["x", "y"]] = df.get_coordinates()
    df_plus = df.loc[df["attribute"] == "ref_plus"]

    df["heading"] = (df["heading"] % 360).round()
    df["ref_facing"] = df["ref_bearing"] - df["heading"]
    df.loc[df["ref_facing"] < 0, "ref_facing"] += 360
    df["ref_facing"] = df["ref_facing"] % 360

    df["k"] = np.cos(np.deg2rad(df["ref_facing"])).round(2)
    df["k"] = np.sign(df["k"])

    df["voltage_norm"] *= df["k"]

    return df
