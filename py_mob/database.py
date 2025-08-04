import pandas as pd
import geopandas as gpd
import os


def export_gdf(meas, overwrite, crs):

    if overwrite == "full":
        keep = "last"
    else:
        keep = overwrite

    data = pd.DataFrame()
    extents = pd.DataFrame()
    path = pd.DataFrame()
    current = pd.DataFrame()

    for m in meas:
        data = pd.concat([data, m.data.set_crs(crs)], axis=0).reset_index(drop=True)
        extents = pd.concat([extents, m.extents.set_crs(crs)], axis=0).reset_index(
            drop=True
        )
        path = pd.concat([path, m.path.set_crs(crs)], axis=0).reset_index(drop=True)
        current = pd.concat([current, m.current.set_crs(crs)], axis=0).reset_index(
            drop=True
        )

    fps = [f"qfield/{db}.gpkg" for db in ["data", "extents", "path", "current"]]
    ids = ["ID", "ID_area", "ID_line", "ID_area"]
    dbs = [data, extents, path, current]

    for fp, id, db in zip(fps, ids, dbs):
        print(f"exporting\t{fp}")
        db = pd.DataFrame(db)
        if not os.path.exists(fp):
            gpd.GeoDataFrame(geometry=[], data={id: []}, crs=crs).to_file(fp)
        if overwrite == "full":
            master = gpd.GeoDataFrame(data={id: [None]}, crs=crs, geometry=[None])
        else:
            master = gpd.read_file(fp)
        master = pd.DataFrame(master)
        master = pd.concat([master, db], axis=0)
        master = master.drop_duplicates(subset=id, keep=keep).reset_index(drop=True)
        master = master.dropna(subset="x")
        master = gpd.GeoDataFrame(master, geometry=master["geometry"], crs=crs)
        master.to_file(fp, engine="pyogrio")

    # df = data.groupby("ID_line")["line_hdg_fwd"].agg("median")
    # path = pd.merge(path, df, how="left", left_on="ID_line", right_index=True)
    # path.to_file("tmp/test.gpkg")
    return data, extents, path
