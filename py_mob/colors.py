from plotly.colors import sample_colorscale
import pandas as pd
import numpy as np


def rgb_to_hex(rgb_string):
    rgb_string = rgb_string.replace("rgb(", "").replace(")", "")
    rgb_string = rgb_string.split(",")
    rgb_string = [int(s.strip()) for s in rgb_string]
    r = rgb_string[0]
    g = rgb_string[1]
    b = rgb_string[2]

    return f"#{r:02x}{g:02x}{b:02x}"


def get_color(value, cmin, cmax, colorscale):
    if value >= cmax:
        value = cmax
    if value <= cmin:
        value = cmin

    normalized_val = (value - cmin) / (cmax - cmin)
    try:
        clr = sample_colorscale(colorscale, normalized_val)[0]
    except:
        clr = "rgb(255, 0, 255)"
    return clr


def get_k_clr(df):
    df["clr"] = "#15FF92"
    df.loc[df["voltage_k"] < 0, "clr"] = "#FF10D7"
    return df


def get_default_crange(df, cmin, cmax):
    df = df.loc[df["attribute"] == "meas"]
    df = df.dropna(subset="voltage_norm")
    if len(df) > 0:
        if cmin == "def" or cmax == "def":
            qmin = np.quantile(df["voltage_norm"], 0.4)
            qmax = np.quantile(df["voltage_norm"], 0.6)

            cmax = max(np.abs([qmin, qmax]))
            cmin = -cmax
    else:
        cmin = -0.5
        cmax = +0.5

    return cmin, cmax
