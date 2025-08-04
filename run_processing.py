import traceback


try:
    from py_mob.meas_class import Meas
    from py_mob.database import export_gdf
    from py_mob.get_ld import get_ld
except Exception as error:
    traceback.print_exc()
    input("Press ENTER to continue!")

ld = get_ld("raw", ext=".csv")

meas = []
n = len(ld)
i = 0
zfill = len(str(n))
if n > 0:
    for fp in ld["fp"]:
        i += 1
        print(f"{str(i).zfill(zfill)}/{str(n).zfill(zfill)}")
        try:
            tmp = Meas(fp)
            tmp = tmp.Proc().Export()
            meas.append(tmp)
        except Exception as error:
            traceback.print_exc()
            input("Press ENTER to continue!")

export_gdf(meas, overwrite="full", crs=3857)

input("\n\nProcessing finshed press ENTER to exit!")
