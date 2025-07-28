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
