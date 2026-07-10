import argparse
from pathlib import Path

import vtk
import numpy as np

def latest_blade_vtk(case):
    files = list((case / "VTK/Savonius").glob("Savonius_*.vtk"))
    if not files:
        raise FileNotFoundError(f"VTK kanat verisi bulunamadi: {case}/VTK/Savonius")
    return max(files, key=lambda p: int(p.stem.rsplit("_", 1)[-1]))

parser = argparse.ArgumentParser(description="Savonius kanat basinc dagilimini analiz et")
parser.add_argument("case", nargs="?", type=Path,
                    default=Path(__file__).resolve().parents[1] / "savonius_mrf")
parser.add_argument("--vtk", type=Path, help="Otomatik latestTime yerine belirli Savonius_*.vtk")
args = parser.parse_args()
vtk_path = args.vtk or latest_blade_vtk(args.case.resolve())

r = vtk.vtkPolyDataReader()
r.SetFileName(str(vtk_path))
r.ReadAllScalarsOn(); r.ReadAllVectorsOn()
r.Update()
ug = r.GetOutput()

pdata = ug.GetCellData()
p_arr = pdata.GetArray('p')
if p_arr is None:
    raise RuntimeError(f"VTK dosyasinda cell-data 'p' alani yok: {vtk_path}")

n = ug.GetNumberOfCells()
centers = vtk.vtkCellCenters()
centers.SetInputData(ug)
centers.Update()
pts = centers.GetOutput().GetPoints()

pvals = np.array([p_arr.GetValue(i) for i in range(n)])
cxyz = np.array([pts.GetPoint(i) for i in range(n)])

# rotor origin
origin = np.array([1,1,0])
rel = cxyz - origin

imax = np.argmax(pvals)
imin = np.argmin(pvals)

print("VTK:", vtk_path)
print("Rotor origin:", origin)
print("N faces:", n)
print(f"MAX pressure = {pvals[imax]:.4f} at pos={cxyz[imax]}, rel_to_origin={rel[imax]}, angle_deg={np.degrees(np.arctan2(rel[imax][1], rel[imax][0])):.1f}")
print(f"MIN pressure = {pvals[imin]:.4f} at pos={cxyz[imin]}, rel_to_origin={rel[imin]}, angle_deg={np.degrees(np.arctan2(rel[imin][1], rel[imin][0])):.1f}")

# top 10 highest pressure points -> stagnation region (likely concave/scoop facing flow)
top10 = np.argsort(pvals)[-15:]
print("\nTop 15 highest-pressure face centers (stagnation candidates):")
for i in top10:
    ang = np.degrees(np.arctan2(rel[i][1], rel[i][0]))
    print(f"  p={pvals[i]:.3f} pos=({cxyz[i][0]:.3f},{cxyz[i][1]:.3f}) angle={ang:.1f} deg")

print("\nBottom 15 lowest-pressure (suction/back side):")
bot10 = np.argsort(pvals)[:15]
for i in bot10:
    ang = np.degrees(np.arctan2(rel[i][1], rel[i][0]))
    print(f"  p={pvals[i]:.3f} pos=({cxyz[i][0]:.3f},{cxyz[i][1]:.3f}) angle={ang:.1f} deg")
