import pandas as pd
import geopandas as gpd
import os
from pathlib import Path
from io import StringIO
import numpy as np
from shapely import Point, MultiPoint, LineString, get_coordinates
from plotly.colors import sample_colorscale


from .angles import angle_full, angle_360, angle_points, angle_signed, angle_dx_dy
from .proc import calc_compass

from .line import get_line_data, get_pt_hdg, split_lines, get_lines

from .colors import rgb_to_hex, get_default_crange
from .sensors import sensors_load_from_db
from .gridding import kriging, mask_grid, export_surfer_grid
from .plot import fig_traces, fig_format


class Meas:
    def __init__(self, fp, **kwargs):
        self.fp_csv = fp
        self.id_sensor_long = Path(self.fp_csv).name.split("_")[0]
        self.id_sensor = sensors_load_from_db(self.id_sensor_long)
        self.id = Path(self.fp_csv).name[:39]
        self.id = self.id.replace(self.id_sensor_long, self.id_sensor)
        self.id_datetime = Path(self.fp_csv).name[22:39]
        self.overwrite_gpkg = kwargs.get("overwrite_gpkg", False)
        self.Get_fps()
        print(self.fp_csv[4:])

    def __call__(self, **kwargs):
        if kwargs.get("f", None) == "meas":
            df = self.data.loc[self.data["attribute"] == "meas"]
        else:
            df = self.data
        return pd.DataFrame(df)

    def Proc(self):
        self.Read_csv()
        self.data = calc_compass(self.data)
        self.Get_meas_extents()
        self.Get_current()
        self.Get_meas_path()
        self.Get_ref_pt()
        self.Calc_ref_bearing()
        self.Calc_hdg_avg()
        self.Calc_ref_facing()
        self.Calc_voltage_norm()
        self.Get_crange()
        self.Get_colors()
        self.data = self.data.sort_index(axis=1)
        return self

    def Export(self):
        self.Export_excel()
        self.Export_grid(wgs=True)
        self.Export_html()
        self.Export_bln()
        return self

    def Get_fps(self):
        self.directory = f"output/{self.id_sensor}/{self.id_datetime}"
        self.filename = f"{self.id_sensor}_{self.id_datetime}"

        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

        self.fp = {}
        for ext in ["html", "xlsx", "grd", "bln"]:
            self.fp[ext] = os.path.join(self.directory, self.filename + f".{ext}")
        return self

    def Read_csv(self):
        self.get_header_data()
        with open(self.fp_csv, "r") as file:
            txt = file.read()

        txt = txt.replace(":", ",")

        df = pd.read_csv(StringIO(txt), skiprows=self.skiprows)
        new_cols = [
            "lon",
            "lat",
            "voltage_raw",
            "ID_point",
            "attribute",
            "attribute_counter",
            "date",
            "time_hour",
            "time_minute",
            "time_sec",
            "compass_x",
            "compass_y",
            "compass_z",
            "lat_int",
            "lon_int",
            "hdop",
            "gnss_status",
            "gnss_fix",
            "fw",
            "ser_num",
        ]

        df = df.rename(columns=dict(zip(df.columns, new_cols)))
        df["attribute"] = list(map(lambda x: x.strip(), df["attribute"]))
        df["attribute"] = df["attribute"].replace("", "meas")

        df["time"] = (
            df["time_hour"].astype(str).str.zfill(2)
            + ":"
            + df["time_minute"].astype(str).str.zfill(2)
            + ":"
            + df["time_sec"].astype(str).str.zfill(2)
        )
        df["datetime"] = pd.to_datetime(df["date"] + "T" + df["time"])

        geom = gpd.points_from_xy(df["lon"], df["lat"])
        gdf = gpd.GeoDataFrame(df, geometry=geom, crs=4326)
        gdf = gdf.to_crs(3857)
        gdf[["x", "y"]] = gdf.get_coordinates()
        gdf = gdf.replace("nan ", np.nan)
        gdf["ID"] = self.id + "_" + gdf["ID_point"].astype(str)
        gdf["ID_area"] = self.id
        gdf["voltage_raw"] = gdf["voltage_raw"].astype(float)
        self.data = gdf
        return self

    def get_header_data(self):
        cmin = "def"
        cmax = "def"

        with open(self.fp_csv) as file:
            lines = file.readlines()

        lines = [l.strip() for l in lines]

        if len(lines) > 0:
            if lines[0].startswith("long"):
                self.skiprows = 0
            else:
                self.skiprows = 1
                header = lines[0].split(",")
                header = [h.strip() for h in header]
                header = pd.Series(header)
                cmin, cmax = header[[0, 1]].astype(float)
        else:
            self.skiprows = -1
        self.cmin = cmin
        self.cmax = cmax
        return self

    def Format_cols(self):
        cols = {
            "ID": str,
            "ID_point": "Int64",
            "ID_area": str,
            "voltage_raw": float,
            "voltage_norm": float,
            "voltage_k": float,
            "datetime": "datetime64[ns]",
            "attribute": str,
            "compass": float,
            "ref_bearing": float,
            "ref_facing": float,
            "compass_x": float,
            "compass_y": float,
            "compass_z": float,
            "hdop": float,
            "gnss_status": str,
            "gnss_fix": str,
            "ser_num": str,
            "geometry": "geometry",
            "lon": float,
            "lat": float,
            "x": float,
            "y": float,
        }

        for col, dtype in cols.items():
            if col in self.data.columns:
                self.data[col] = self.data[col].astype(dtype)

        for col in self.data.columns:
            if not col in cols.keys():
                self.data = self.data.drop(columns=col)

        return self

    def Split_data(self):
        self.positions = self.data.loc[self.data["attribute"] == "position"]
        self.input = self.data.loc[self.data["attribute"].isin(["plus", "minus"])]
        self.data = self.data.loc[self.data["attribute"] == "meas"]
        self.data = self.data.dropna(subset=["voltage_raw"])
        self.Format_cols()
        return self

    def Get_meas_extents(self):
        gdf = self.data[self.data["attribute"] == "meas"]
        gdf = gdf.dropna(subset="voltage_raw").reset_index(drop=True)
        geom = gpd.GeoSeries(MultiPoint(gdf["geometry"])).concave_hull(0.2).buffer(1)
        data = data = {"ID_area": [self.id], "sensor": [self.id_sensor]}
        self.extents = gpd.GeoDataFrame(data=data, geometry=geom, crs=3857)
        self.extents["start"] = gdf["datetime"].min()
        self.extents["end"] = gdf["datetime"].max()
        self.extents["fp"] = self.fp_csv
        return self

    def Calc_ref_facing(self):
        df = self.data.copy()
        df["ref_facing"] = angle_signed(df["ref_bearing"] - df["hdg_avg"])
        self.data = df
        return self

    def Calc_ref_bearing(self):
        dx = self.data["x"] - self.ref_pt.x
        dy = self.data["y"] - self.ref_pt.y

        self.data["ref_dist"] = (dx**2 + dy**2) ** 0.5
        self.data["ref_dist"] = self.data["ref_dist"].round(2)

        self.data["ref_bearing"] = np.atan2(dx, dy)
        self.data["ref_bearing"] = np.rad2deg(self.data["ref_bearing"])
        self.data["ref_bearing"] = angle_full(self.data["ref_bearing"] + 180)

        return self

    def Get_meas_path(self):
        mask = self.data["attribute"] == "meas"
        if len(self.data.loc[mask]) > 2:
            meas = get_pt_hdg(self.data)
            meas = get_lines(meas)
            meas["ID_line"] = self.id + "_" + meas["line"].astype(str).str.zfill(3)
            self.path = split_lines(meas)
            points = self.data.loc[self.data["attribute"] != "meas"]
            self.data = pd.concat([meas, points], axis=0, ignore_index=True)
            self.data = self.data.reset_index(drop=True)

        else:
            self.path = gpd.GeoDataFrame(geometry=[], crs=3857)
        if len(self.path) > 0:
            self.data = get_line_data(self.data, self.path)

        return self

    def Load_clim(self):
        gdf = gpd.read_file("vector/extents.gpkg", engine="pyogrio")
        if len(gdf) > 1:
            gdf = gdf.loc[gdf["ID_area"] == self.id]
            gdf = gdf.dropna(subset=["cmin", "cmax"])

        if len(gdf) > 1:
            self.cmin = gdf.iloc[0]["cmin"]
            self.cmax = gdf.iloc[0]["cmax"]
        else:
            self.cmin = -1
            self.cmax = 1
        return self

    def Get_colors(self):
        # colorscale = "Portland"
        # colorscale = "Balance"
        colorscale = "RdBu_r"
        for voltage, type in zip(["voltage_raw", "voltage_norm"], ["r", "n"]):

            values = self.data[voltage].clip(lower=self.cmin, upper=self.cmax)
            values = values.fillna(0)
            values = (values - self.cmin) / (self.cmax - self.cmin)

            clr_rgb = sample_colorscale(colorscale=colorscale, samplepoints=values)

            self.data[f"clr_{type}_rgb"] = clr_rgb
            mask = self.data[voltage].isnull()
            self.data.loc[mask, [f"clr_{type}_rgb"]] = "rgb(255, 0, 255)"

            # clr_hex = self.data[f"clr_{type}_rgb"].str.replace("rgb(|","")
            clr_hex = [rgb_to_hex(c) for c in clr_rgb]

            self.data[f"clr_{type}_hex"] = clr_hex

        return self

    def Get_current(self):
        gb = self.data.groupby("attribute", as_index=False).agg("first")
        gb = gb.loc[gb["attribute"].isin(["minus", "plus"])]

        if len(gb) > 0:
            cnt = self.extents.centroid
            p0 = Point(cnt.x, cnt.y)

            pt = []
            for x, y in zip(gb["x"], gb["y"]):
                p1 = Point(x, y)
                pt.extend([p0, p1, p0])

            geom = LineString(pt)

            gdf = gpd.GeoDataFrame(geometry=[geom], crs=3857)
            gdf["ID_area"] = self.id
        else:
            gdf = gpd.GeoDataFrame(geometry=[], columns=["ID_area"], crs=3857)

        self.current = gdf
        return self

    def Calc_voltage_norm(self):
        df = self.data.copy()
        df["voltage_norm"] = df["voltage_raw"].round(3)
        df["voltage_raw"] = df["voltage_raw"].astype(float)
        df["voltage_k"] = np.cos(np.deg2rad(df["ref_facing"]))
        df["voltage_k"] = -np.sign(df["voltage_k"])

        df["voltage_norm"] *= df["voltage_k"]
        if df["voltage_norm"].median() < 0:
            df["voltage_norm"] *= -1
            df["voltage_k"] *= 1

        self.data = df
        return self

    def Get_ref_pt(self):
        cnt = self.extents.centroid
        self.Calc_ref_angle()
        x = cnt.x + 1000 * np.sin(np.deg2rad(self.ref_angle))
        y = cnt.y + 1000 * np.cos(np.deg2rad(self.ref_angle))
        self.ref_pt = Point(x, y)

        insert_cols = ["geometry", "attribute", "ID", "ID_area"]
        insert_data = [self.ref_pt, "ref", self.id + "_ref", self.id]

        self.data.loc[len(self.data), insert_cols] = insert_data
        return self

    def Calc_ref_angle(self):
        if len(self.path) > 0:

            dx = []
            dy = []
            for geom in self.path["geometry"]:
                coords = get_coordinates(geom)
                dx.append(coords[-1, 0] - coords[0, 0])
                dy.append(coords[-1, 1] - coords[0, 1])

            self.path["angle"] = angle_dx_dy(dx, dy) % 180
            sin = np.sin(np.deg2rad(self.path["angle"]))
            cos = np.cos(np.deg2rad(self.path["angle"]))
            sin = np.average(sin, weights=self.path["line_len"])
            cos = np.average(cos, weights=self.path["line_len"])
            self.ref_angle = np.rad2deg(np.atan2(sin, cos))
        else:
            self.path["angle"] = np.nan
            self.ref_angle = np.nan
        return self

    def Calc_hdg_avg(self):
        if len(self.path) > 0:
            angle_diff = angle_signed(self.data["line_hdg_fwd"] - self.data["compass"])
            self.data["hdg_avg"] = angle_diff / 2
            self.data["hdg_avg"] += self.data["compass"]
            self.data["d_angle"] = angle_diff
        else:
            self.data["hdg_avg"] = np.nan
            self.data["d_angle"] = np.nan
        return self

    def Export_excel(self):

        cols = pd.read_csv("py_mob/cols_excel.tsv", sep="\t").iloc[:, 0]
        cols = [col for col in cols if col in self.data.columns]
        data = self.data.copy()[cols]
        meas = data.loc[data["attribute"] == "meas"]
        anomaly = data.loc[data["attribute"] == "anomaly"]
        area = data.loc[data["attribute"] == "area"]
        input = data.loc[data["attribute"].isin(["minus", "plus"])]

        fp = self.fp["xlsx"]

        with pd.ExcelWriter(fp, engine="openpyxl") as writer:
            meas.to_excel(writer, sheet_name="meas", index=False)
            anomaly.to_excel(writer, sheet_name="anomaly", index=False)
            area.to_excel(writer, sheet_name="area", index=False)
            input.to_excel(writer, sheet_name="input", index=False)

    def Export_grid(self, **kwargs):
        if len(self.Filter_data("meas").dropna(subset="voltage_norm")) > 0:
            self.grid_x, self.grid_y, self.grid_z_full = kriging(self)
            self.grid_z = mask_grid(self)
            if kwargs.get("wgs", False) == True:
                self.Convert_grid_coordinates()
            if pd.Series(self.grid_z.flatten()).dropna().count() > 0:
                export_surfer_grid(
                    self.grid_z, self.grid_x, self.grid_y, self.fp["grd"]
                )
            else:
                print("Grid not exported - masked grid is empty!")
            self.skip_grid = False
        else:
            self.skip_grid = True

        return self

    def Export_html(self):
        fig = fig_traces(self)
        fig = fig_format(fig)
        fig.write_html(self.fp["html"])
        self.fig = fig
        return self

    def Convert_grid_coordinates(self):
        x = self.grid_x.flatten()
        y = self.grid_y.flatten()

        geom = gpd.points_from_xy(x, y)
        gs = gpd.GeoSeries(geom).set_crs(3857)
        gs = gs.to_crs(4326)
        coords = gs.get_coordinates()
        self.grid_x = np.reshape(coords["x"], self.grid_x.shape)
        self.grid_y = np.reshape(coords["y"], self.grid_x.shape)
        return self

    def Filter_data(self, filter):
        df = self.data.copy()
        if filter == "meas":
            mask = df["attribute"] == "meas"
        if filter == "input":
            mask = df["attribute"].isin(["minus", "plus"])
        df = df.loc[mask]
        return df

    def Get_crange(self):
        self.cmin, self.cmax = get_default_crange(self.data, self.cmin, self.cmax)
        self.extents["cmin"] = self.cmin
        self.extents["cmax"] = self.cmax
        return self

    def Export_bln(self):
        coords = self.extents.get_coordinates()
        lines = [f"{len(coords)},0\n"]

        for x, y in zip(coords["x"], coords["y"]):
            lines.append(f"{x},{y}\n")

        with open(self.fp["bln"], "w") as file:
            file.writelines(lines)
