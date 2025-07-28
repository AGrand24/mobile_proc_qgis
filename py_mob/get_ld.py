import pandas as pd
import os


def get_ld(dir_path, **kwargs):
    file_list = []
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_list.append({"fn": file, "fp": file_path})

    df = pd.DataFrame(file_list)

    if len(df) > 0:
        if kwargs.get("ext", None) != None:
            df = df.loc[df["fn"].str.endswith(kwargs.get("ext", None))]

        df["ext"] = df["fn"].str.findall("[^.]*$")
        df["ext"] = [l[0] for l in df["ext"]]
        df["f"] = df["fn"].str.findall("^[^.]*")
        df["f"] = [l[0] for l in df["f"]]
    return df.reset_index(drop=True)
