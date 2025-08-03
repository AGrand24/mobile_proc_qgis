import pandas as pd
import numpy as np
from .get_ld import get_ld


def logger_load_from_db(sensor_id):
    df = pd.read_csv("py_mob/sensors.tsv", sep="\t")

    if sensor_id not in df["orig"].values:
        df_new = pd.DataFrame({"orig": [sensor_id], "new": [np.nan]})

        df = pd.concat([df, df_new]).drop_duplicates(subset="orig", keep="first")

        df["new"] = df["new"].interpolate(
            "slinear", fill_value="extrapolate", limit_direction="both"
        )
        df["new"] = df["new"].astype("Int64")
        df["new"] = df["new"].astype(str)
        df.to_csv("sensors.csv", index=False)

    sensor_id = df.loc[df["orig"] == sensor_id, "new"].iloc[0]
    sensor_id = str(sensor_id).zfill(3)
    return sensor_id
