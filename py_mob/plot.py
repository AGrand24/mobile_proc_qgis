import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.colors import sample_colorscale
import plotly.io as pio

pio.templates.default = "plotly_dark"

from .colors import get_k_clr


def get_heatmap(meas):
    x0 = np.min(meas.grid_x)
    y0 = np.min(meas.grid_y)

    dx = np.ptp(meas.grid_x) / meas.grid_z.shape[1]
    dy = np.ptp(meas.grid_y) / meas.grid_z.shape[0]
    zmin = meas.cmin
    zmax = meas.cmax
    colorbar = dict(
        title="[V]",
        x=0,
        y=0.01,
        len=0.5,
        xanchor="left",
        yanchor="bottom",
        thickness=10,
    )

    plt = go.Heatmap(
        x0=x0,
        y0=y0,
        dx=dx,
        dy=dy,
        z=meas.grid_z,
        name="grid",
        zmin=zmin,
        zmax=zmax,
        colorscale="RdBu_r",
        colorbar=colorbar,
        showlegend=True,
    )
    return plt


def get_scatter_compass(meas):
    df = meas.Filter_data("meas")
    cd = df[
        [
            "ID_point",
            "datetime",
            "compass",
            "voltage_raw",
            "voltage_norm",
            "voltage_k",
            "line",
        ]
    ]
    cd = cd.values
    df = get_k_clr(df)
    marker = dict(
        symbol="triangle-up",
        angle=df["compass"],
        color=df["clr"],
        size=9,
        line=dict(color="#000000", width=1),
    )
    line = dict(color="#000000", width=1)
    ht = "Point: %{customdata[0]}<br>Time:  %{customdata[1]}<br>Compass: %{customdata[2]}<br>V raw: %{customdata[3]}<br>V norm: %{customdata[4]}<br>V k: %{customdata[5]}<br>Line: %{customdata[6]}"
    plt = go.Scatter(
        x=df["lon"],
        y=df["lat"],
        mode="lines+markers",
        marker=marker,
        name="Compass",
        customdata=cd,
        hovertemplate=ht,
        line=line,
    )
    return plt


def get_scatter_values(meas, values):
    if values == "norm":
        clr = "clr_n_hex"
    else:
        clr = "clr_r_hex"

    df = meas.Filter_data("meas")
    cd = df[
        [
            "ID_point",
            "datetime",
            "compass",
            "voltage_raw",
            "voltage_norm",
            "voltage_k",
            "line",
        ]
    ]
    cd = cd.values
    marker = dict(
        symbol="circle",
        color=df[clr],
        size=10,
        line=dict(color="#000000", width=1),
    )
    ht = "Point: %{customdata[0]}<br>Time:  %{customdata[1]}<br>Compass: %{customdata[2]}<br>V raw: %{customdata[3]}<br>V norm: %{customdata[4]}<br>V k: %{customdata[5]}<br>Line: %{customdata[6]}"
    plt = go.Scatter(
        x=df["lon"],
        y=df["lat"],
        mode="markers",
        marker=marker,
        name=f"Values- {values}",
        customdata=cd,
        hovertemplate=ht,
        visible="legendonly",
    )
    return plt


def get_pt_txt(meas):
    df = meas.Filter_data("meas")
    df = get_k_clr(df)
    textfont = dict(size=10, color=df["clr"])
    plt = go.Scatter(
        x=df["lon"],
        y=df["lat"],
        visible="legendonly",
        name="Point labels",
        mode="text",
        text=df["ID_point"],
        textfont=textfont,
    )
    return plt


def get_scatter_input(meas):

    df = meas.Filter_data("input")
    cd = df[["ID_point", "datetime"]]
    cd = cd.values
    df["symbols"] = "cross"
    df.loc[df["attribute"] == "minus", "symbols"] = "square"

    marker = dict(symbol=df["symbols"], size=8)
    ht = "Point: %{customdata[0]}<br>Time:  %{customdata[1]}"
    plt = go.Scatter(
        x=df["lon"],
        y=df["lat"],
        mode="markers",
        marker=marker,
        name="Input",
        customdata=cd,
        hovertemplate=ht,
    )
    return plt


def get_histogram(meas):
    df = meas.Filter_data("meas")
    df = df.dropna(subset="voltage_norm")
    num_bins = 25
    counts, bin_edges = np.histogram(df["voltage_norm"], bins=num_bins)
    # counts = 100 * counts / len(df["voltage_norm"])
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    plt = go.Bar(
        x=bin_centers,
        y=counts,
        marker_color=bin_centers,
        marker=dict(colorscale="RdBu_r", cmin=meas.cmin, cmax=meas.cmax),
        name="Histogram",
    )

    return plt


def get_k_plot(meas):
    df = meas.Filter_data("meas")
    df = get_k_clr(df)
    marker = dict(color=df["clr"])

    plt = go.Scatter(
        x=df["compass"],
        y=df["voltage_k"],
        mode="markers",
        marker=marker,
        name="Voltage k",
        hovertext=df["ID_point"],
    )
    return plt


def fig_traces(meas):

    fig = go.Figure(make_subplots(rows=2, cols=2))

    if meas.skip_grid == False:
        plt_grid = get_heatmap(meas)
        fig.add_trace(plt_grid, row=1, col=2)

    if len(meas.Filter_data("meas")) > 0:

        plt_k = get_k_plot(meas)
        fig.add_trace(plt_k, row=2, col=1)

        plt_hist = get_histogram(meas)
        fig.add_trace(plt_hist, row=1, col=1)

        plt_compass = get_scatter_compass(meas)
        fig.add_trace(plt_compass, row=1, col=2)

        plt_values_norm = get_scatter_values(meas, "norm")
        fig.add_trace(plt_values_norm, row=1, col=2)

        plt_values_raw = get_scatter_values(meas, "raw")
        fig.add_trace(plt_values_raw, row=1, col=2)

        plt_txt = get_pt_txt(meas)
        fig.add_trace(plt_txt, row=1, col=2)

    if len(meas.Filter_data("input")) > 0:
        plt_input = get_scatter_input(meas)
        fig.add_trace(plt_input, row=1, col=2)

    return fig


def fig_format(fig, width, height):

    fig.update_yaxes(scaleanchor="x2", scaleratio=1, row=1, col=2)
    fig.update_layout(
        xaxis1=(dict(domain=[0, 0.25])),
        xaxis2=(dict(domain=[0.25, 0.95])),
        xaxis3=(dict(domain=[0, 0.25])),
        yaxis1=(dict(domain=[0.75, 1])),
        yaxis2=(dict(domain=[0, 1])),
        yaxis3=(dict(domain=[0.55, 0.7])),
    )

    fig.update_layout(width=width, height=height)
    fig.update_layout(legend=dict(yanchor="bottom", xanchor="right", y=0.01, x=0.25))

    fig.update_layout(showlegend=True, hoverdistance=1)
    fig.update_layout(margin=dict(l=1, r=1, t=1, b=2))
    fig.update_xaxes(row=1, col=2, showticklabels=False, showgrid=False)
    fig.update_yaxes(row=1, col=2, showticklabels=False, showgrid=False)
    fig.update_xaxes(row=1, col=1, showgrid=True)
    fig.update_xaxes(row=1, col=1, title="voltage norm")
    fig.update_yaxes(row=1, col=1, title="n")
    fig.update_yaxes(row=2, col=1, title="voltage k")
    fig.update_xaxes(row=2, col=1, title="compass (deg)")

    return fig
