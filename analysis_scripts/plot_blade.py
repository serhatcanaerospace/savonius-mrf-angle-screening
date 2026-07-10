import argparse
from pathlib import Path

import vtk
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

parser = argparse.ArgumentParser(description="Savonius kanat basinc haritasi ciz")
parser.add_argument("vtk", nargs="?", type=Path,
                    default=Path(__file__).resolve().parents[1] / "savonius_mrf/VTK/Savonius/Savonius_230.vtk")
parser.add_argument("-o", "--output", type=Path, default=Path("blade_pressure.png"))
args = parser.parse_args()
if not args.vtk.is_file():
    candidates = list(args.vtk.parent.glob("Savonius_*.vtk"))
    if not candidates:
        raise FileNotFoundError(f"VTK kanat verisi bulunamadi: {args.vtk}")
    args.vtk = max(candidates, key=lambda p: int(p.stem.rsplit("_", 1)[-1]))

r = vtk.vtkPolyDataReader()
r.SetFileName(str(args.vtk))
r.ReadAllScalarsOn()
r.Update()
pd = r.GetOutput()
pdata = pd.GetCellData()
p_arr = pdata.GetArray('p')
if p_arr is None:
    raise RuntimeError(f"VTK dosyasinda cell-data 'p' alani yok: {args.vtk}")
n = pd.GetNumberOfCells()

# get triangle vertex coords for polygon plotting
pts = pd.GetPoints()
tris = []
pvals = []
for i in range(n):
    cell = pd.GetCell(i)
    ids = cell.GetPointIds()
    coords = [pts.GetPoint(ids.GetId(k))[:2] for k in range(ids.GetNumberOfIds())]
    tris.append(coords)
    pvals.append(p_arr.GetValue(i))
pvals = np.array(pvals)

from matplotlib.collections import PolyCollection
fig, ax = plt.subplots(figsize=(9,9))
coll = PolyCollection(tris, array=pvals, cmap='coolwarm', edgecolors='none')
vmin, vmax = np.percentile(pvals, [2, 98])
if np.isclose(vmin, vmax):
    vmin, vmax = float(pvals.min()), float(pvals.max())
coll.set_clim(vmin, vmax)
ax.add_collection(coll)
ax.autoscale()
ax.set_aspect('equal')
cb = fig.colorbar(coll, ax=ax, label='p (basinc)')

origin = (1,1)
# flow direction arrow (inlet -> +x)
ax.annotate('', xy=(origin[0]-0.15, origin[1]+0.55), xytext=(origin[0]-0.6, origin[1]+0.55),
            arrowprops=dict(arrowstyle='-|>', color='black', lw=3))
ax.text(origin[0]-0.6, origin[1]+0.58, 'AKIS YONU (U_inf, +x)', fontsize=11, color='black')

# rotation direction arrow (omega +z => CCW when viewed from +z, standard math convention)
theta = np.linspace(0.3, 1.8, 30)
rr = 0.55
ax.plot(origin[0]+rr*np.cos(theta), origin[1]+rr*np.sin(theta), color='green', lw=2)
# arrowhead at end of curve
ax.annotate('', xy=(origin[0]+rr*np.cos(1.8), origin[1]+rr*np.sin(1.8)),
            xytext=(origin[0]+rr*np.cos(1.6), origin[1]+rr*np.sin(1.6)),
            arrowprops=dict(arrowstyle='-|>', color='green', lw=2))
ax.text(origin[0]-0.35, origin[1]+0.35, 'omega (+z, sag-el kurali\nile SAAT YONU TERSI)', color='green', fontsize=10)

ax.plot(*origin, 'k+', markersize=12)
ax.set_xlim(origin[0]-0.65, origin[0]+0.65)
ax.set_ylim(origin[1]-0.65, origin[1]+0.65)
ax.set_title('Savonius kanadi - basinc dagilimi (MRF, donuk aci)\nkirmizi=yuksek basinc (durma noktasi), mavi=dusuk basinc (emme)')
plt.tight_layout()
plt.savefig(args.output, dpi=130)
print(f"saved: {args.output}")
