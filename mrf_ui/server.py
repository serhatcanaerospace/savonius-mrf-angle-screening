#!/usr/bin/env python3
"""Local web UI to edit savonius_mrf OpenFOAM case parameters and run it.

Stdlib only (no Flask). Binds to 127.0.0.1. Reads/writes the dict files
in-place with targeted regex substitutions - it does not rewrite whole
files, so anything not exposed as a field is left untouched.
"""
import re
import subprocess
import os
import signal
import html
import math
import tempfile
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parent.parent
CASE = Path(os.environ.get("SAVONIUS_CASE", ROOT / "savonius_mrf")).resolve()
R_ROTOR = 0.4511
PORT = 8877
SOLVERS = ("simpleFoam", "pimpleFoam")

FILES = {
    "controlDict": CASE / "system/controlDict",
    "fvSolution": CASE / "system/fvSolution",
    "snappy": CASE / "system/snappyHexMeshDict",
    "blockMesh": CASE / "system/blockMeshDict",
    "mrf": CASE / "constant/MRFProperties",
    "initialConditions": CASE / "0/include/initialConditions",
    "forceCoeffs": CASE / "system/forceCoeffs",
}

# Known-good baseline, validated during this session (364K cells, 2.5
# layers / 64.9% coverage, stable simpleFoam convergence, Cm_R~=0.0357).
DEFAULTS = {
    "U": "6",
    "omega": "10.6336",
    "endTime": "2000",
    "writeInterval": "100",
    "purgeWrite": "5",
    "relaxP": "0.3",
    "relaxU": "0.6",
    "relaxKOmega": "0.6",
    "refineRadius": "0.5",
    "refineLevel": "4",
    "wakeLevel": "2",
    "nSurfaceLayers": "2",
    "minThickness": "0.002",
    "gridNx": "200",
    "gridNy": "100",
}


def read(key):
    with open(FILES[key]) as f:
        return f.read()


def write(key, content):
    """Atomically replace a dictionary so interrupted saves cannot corrupt it."""
    target = FILES[key]
    fd, tmp_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent, text=True)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, target)
    except Exception:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


def get1(pattern, text, default="?"):
    m = re.search(pattern, text)
    return m.group(1) if m else default


FIELDS = [
    # (id, label, unit, section, file, get_regex)
    ("U", "Giris hizi (U_inf)", "m/s", "Akis", "initialConditions",
     r"flowVelocity\s+(?:uniform\s+)?\(([\d.eE+-]+) 0 0\);"),
    ("omega", "Rotor acisal hizi (omega)", "rad/s", "Akis", "mrf",
     r"omega\s+([\d.eE+-]+);"),
    ("tsrInput", "TSR (opsiyonel - doldurursan omega'yi hesaplar)", "", "Akis", None, None),
    ("endTime", "endTime (iterasyon sayisi)", "", "Zaman", "controlDict",
     r"endTime\s+([\d.eE+-]+);"),
    ("writeInterval", "writeInterval", "iterasyon/sn", "Zaman", "controlDict",
     r"writeInterval\s+([\d.eE+-]+);"),
    ("purgeWrite", "purgeWrite (0=hepsini tut)", "", "Zaman", "controlDict",
     r"purgeWrite\s+([\d.eE+-]+);"),
    ("relaxP", "Relaxation - p", "", "Sayisal cozum", "fvSolution",
     r"relaxationFactors[\s\S]*?fields\s*\{\s*p\s+([\d.eE+-]+);"),
    ("relaxU", "Relaxation - U", "", "Sayisal cozum", "fvSolution",
     r"relaxationFactors[\s\S]*?equations\s*\{\s*U\s+([\d.eE+-]+);"),
    ("relaxKOmega", "Relaxation - k/omega", "", "Sayisal cozum", "fvSolution",
     r'relaxationFactors[\s\S]*?"\(k\|omega\)"\s+([\d.eE+-]+);'),
    ("refineRadius", "Kanat refine bolgesi yaricapi", "m", "Mesh", "snappy",
     r"refineZone\s*\{\s*type searchableCylinder;[\s\S]*?radius\s+([\d.eE+-]+);"),
    ("refineLevel", "Kanat refine seviyesi (0-6 onerilir)", "", "Mesh", "snappy",
     r"refineZone\s*\{\s*mode inside;\s*levels\s*\(\((\d+)\s+\d+\)\);"),
    ("wakeLevel", "Wake (iz) refine seviyesi (0-4 onerilir)", "", "Mesh", "snappy",
     r"wakeZone\s*\{\s*mode inside;\s*levels\s*\(\((\d+)\s+\d+\)\);"),
    ("nSurfaceLayers", "Sinir tabaka katman sayisi", "", "Mesh", "snappy",
     r"nSurfaceLayers\s+(\d+);"),
    ("minThickness", "Min katman kalinligi", "", "Mesh", "snappy",
     r"minThickness\s+([\d.eE+-]+);"),
    ("gridNx", "Arka plan grid - x boluntu (200 onerilir, >400 COK AGIR)", "", "Mesh", "blockMesh",
     r"hex \(0 1 2 3 4 5 6 7\) \((\d+) \d+ \d+\)"),
    ("gridNy", "Arka plan grid - y boluntu (100 onerilir, >200 COK AGIR)", "", "Mesh", "blockMesh",
     r"hex \(0 1 2 3 4 5 6 7\) \(\d+ (\d+) \d+\)"),
]

SECTIONS = ["Akis", "Zaman", "Sayisal cozum", "Mesh"]

SET_PATTERNS = {
    "U": (r"(flowVelocity\s+(?:uniform\s+)?\()([\d.eE+-]+)( 0 0\);)", "initialConditions"),
    "omega": (r"(omega\s+)([\d.eE+-]+)(;)", "mrf"),
    "endTime": (r"(endTime\s+)([\d.eE+-]+)(;)", "controlDict"),
    "writeInterval": (r"(writeInterval\s+)([\d.eE+-]+)(;)", "controlDict"),
    "purgeWrite": (r"(purgeWrite\s+)([\d.eE+-]+)(;)", "controlDict"),
    "refineRadius": (r"(radius\s+)([\d.eE+-]+)(;)", "snappy"),
    "nSurfaceLayers": (r"(nSurfaceLayers\s+)(\d+)(;)", "snappy"),
    "minThickness": (r"(minThickness\s+)([\d.eE+-]+)(;)", "snappy"),
}


def set_simple(key, value):
    pattern, filekey = SET_PATTERNS[key]
    text = read(filekey)
    new_text, n = re.subn(pattern, lambda m: m.group(1) + value + m.group(3), text, count=1)
    if n == 0:
        raise ValueError(f"{key}: dosyada eslesme bulunamadi, degistirilemedi.")
    write(filekey, new_text)


def set_velocity(value):
    """Update velocity and every quantity whose definition depends on it."""
    initial = read("initialConditions")
    old_u = float(get1(
        r"flowVelocity\s+(?:uniform\s+)?\(([\d.eE+-]+) 0 0\);", initial
    ))
    new_u = float(value)
    if old_u <= 0:
        raise ValueError("Mevcut U sifirdan buyuk olmali.")
    ratio = new_u / old_u
    old_k = float(get1(r"turbulentKE\s+([\d.eE+-]+);", initial))
    old_omega = float(get1(r"turbulentOmega\s+([\d.eE+-]+);", initial))

    replacements = (
        (r"(flowVelocity\s+(?:uniform\s+)?\()([\d.eE+-]+)( 0 0\);)", value),
        (r"(turbulentKE\s+)([\d.eE+-]+)(;)", f"{old_k * ratio**2:.8g}"),
        (r"(turbulentOmega\s+)([\d.eE+-]+)(;)", f"{old_omega * ratio:.8g}"),
    )
    updated = initial
    for pattern, replacement in replacements:
        updated, count = re.subn(
            pattern, lambda m, x=replacement: m.group(1) + x + m.group(3),
            updated, count=1
        )
        if count != 1:
            raise ValueError("U'ya bagli baslangic kosullari guncellenemedi.")

    force_text = read("forceCoeffs")
    force_text, count = re.subn(
        r"(magUInf\s+)([\d.eE+-]+)(;)",
        lambda m: m.group(1) + value + m.group(3), force_text, count=1
    )
    if count != 1:
        raise ValueError("forceCoeffs.magUInf guncellenemedi.")
    write("initialConditions", updated)
    write("forceCoeffs", force_text)


def set_relax_p(value):
    text = read("fvSolution")
    new_text, n = re.subn(
        r"(relaxationFactors[\s\S]*?fields\s*\{\s*p\s+)([\d.eE+-]+)(;)",
        lambda m: m.group(1) + value + m.group(3), text, count=1)
    if n != 1:
        raise ValueError("relaxP: dosyada eslesme bulunamadi, degistirilemedi.")
    write("fvSolution", new_text)


def set_relax_u(value):
    text = read("fvSolution")
    new_text, n = re.subn(
        r"(relaxationFactors[\s\S]*?equations\s*\{\s*U\s+)([\d.eE+-]+)(;)",
        lambda m: m.group(1) + value + m.group(3), text, count=1)
    if n != 1:
        raise ValueError("relaxU: dosyada eslesme bulunamadi, degistirilemedi.")
    write("fvSolution", new_text)


def set_relax_komega(value):
    text = read("fvSolution")
    new_text, n = re.subn(
        r'(relaxationFactors[\s\S]*?"\(k\|omega\)"\s+)([\d.eE+-]+)(;)',
        lambda m: m.group(1) + value + m.group(3), text, count=1)
    if n != 1:
        raise ValueError("relaxKOmega: dosyada eslesme bulunamadi, degistirilemedi.")
    write("fvSolution", new_text)


def set_refine_level(value):
    text = read("snappy")
    new_text, n = re.subn(
        r"(refineZone\s*\{\s*mode inside;\s*levels\s*\(\()(\d+)(\s+)(\d+)(\)\);)",
        lambda m: m.group(1) + value + m.group(3) + value + m.group(5), text, count=1)
    if n != 1:
        raise ValueError("refineLevel: dosyada eslesme bulunamadi, degistirilemedi.")
    write("snappy", new_text)


def set_wake_level(value):
    text = read("snappy")
    new_text, n = re.subn(
        r"(wakeZone\s*\{\s*mode inside;\s*levels\s*\(\()(\d+)(\s+)(\d+)(\)\);)",
        lambda m: m.group(1) + value + m.group(3) + value + m.group(5), text, count=1)
    if n != 1:
        raise ValueError("wakeLevel: dosyada eslesme bulunamadi, degistirilemedi.")
    write("snappy", new_text)


def set_grid(nx, ny):
    text = read("blockMesh")
    new_text, n = re.subn(
        r"(hex \(0 1 2 3 4 5 6 7\) \()\d+( )\d+( \d+\))",
        lambda m: m.group(1) + nx + m.group(2) + ny + m.group(3), text, count=1)
    if n != 1:
        raise ValueError("grid: dosyada eslesme bulunamadi, degistirilemedi.")
    write("blockMesh", new_text)


SETTERS = {
    "U": set_velocity,
    "omega": lambda v: set_simple("omega", v),
    "endTime": lambda v: set_simple("endTime", v),
    "writeInterval": lambda v: set_simple("writeInterval", v),
    "purgeWrite": lambda v: set_simple("purgeWrite", v),
    "relaxP": set_relax_p,
    "relaxU": set_relax_u,
    "relaxKOmega": set_relax_komega,
    "refineRadius": lambda v: set_simple("refineRadius", v),
    "refineLevel": set_refine_level,
    "wakeLevel": set_wake_level,
    "nSurfaceLayers": lambda v: set_simple("nSurfaceLayers", v),
    "minThickness": lambda v: set_simple("minThickness", v),
}


def collect_values():
    vals = {}
    for fid, label, unit, section, filekey, pattern in FIELDS:
        if filekey is None:
            vals[fid] = ""
            continue
        vals[fid] = get1(pattern, read(filekey))
    return vals


def apply_defaults():
    for k, v in DEFAULTS.items():
        if k == "gridNx" or k == "gridNy":
            continue
        SETTERS[k](v)
    set_grid(DEFAULTS["gridNx"], DEFAULTS["gridNy"])


# ---------------------------------------------------------------- dashboard

def mesh_cell_count():
    owner = CASE / "constant/polyMesh/owner"
    if not os.path.exists(owner):
        return None
    try:
        with open(owner) as f:
            for _ in range(30):
                line = f.readline()
                if not line:
                    break
                m = re.search(r"nCells:(\d+)", line)
                if m:
                    return int(m.group(1))
    except Exception:
        pass
    return None


def solver_running():
    """Return a solver PID only when its working directory is this case."""
    try:
        for solver in SOLVERS:
            out = subprocess.run(
                ["pgrep", "-x", solver], capture_output=True, text=True, check=False
            )
            for raw_pid in out.stdout.split():
                try:
                    if Path(f"/proc/{raw_pid}/cwd").resolve() == CASE:
                        return raw_pid
                except (FileNotFoundError, PermissionError):
                    continue
    except Exception:
        pass
    return None


def last_force_coeffs():
    path = CASE / "postProcessing/forceCoeffs1/0/forceCoeffs.dat"
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            lines = [l for l in f if l.strip() and not l.startswith("#")]
        if not lines:
            return None
        parts = lines[-1].split()
        # Time Cm Cd Cl Cl(f) Cl(r)
        return {
            "time": parts[0],
            "Cm": parts[1],
            "Cd": parts[2],
            "Cl": parts[3],
        }
    except Exception:
        return None


def mesh_quality_summary():
    path = CASE / "log.checkMesh"
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            text = f.read()
        failed = get1(r"(Failed \d+ mesh checks)", text, "")
        if not failed:
            if "Mesh OK" in text:
                failed = "Mesh OK"
        return failed or None
    except Exception:
        return None


def dashboard_html():
    cells = mesh_cell_count()
    pid = solver_running()
    fc = last_force_coeffs()
    quality = mesh_quality_summary()

    cells_txt = f"{cells:,}".replace(",", ".") if cells else "mesh yok / uretilmedi"
    solver_txt = f'<span class="ok">calisiyor (PID {pid})</span>' if pid else '<span class="idle">bos (calismiyor)</span>'
    quality_txt = html.escape(quality) if quality else "checkMesh sonucu yok"

    if fc:
        fc_txt = f"iterasyon {fc['time']}: Cm={fc['Cm']}, Cd={fc['Cd']}, Cl={fc['Cl']}"
    else:
        fc_txt = "henuz sonuc yok"

    return f"""
    <div class="dash">
      <div><b>Hucre sayisi:</b> {cells_txt}</div>
      <div><b>checkMesh:</b> {quality_txt}</div>
      <div><b>Cozucu durumu:</b> {solver_txt}</div>
      <div><b>Son Cm/Cd/Cl:</b> {html.escape(fc_txt)}</div>
    </div>"""


def render_page(msg=""):
    v = collect_values()
    try:
        tsr = float(v["omega"]) * R_ROTOR / float(v["U"])
        tsr_txt = f"{tsr:.3f}"
    except Exception:
        tsr_txt = "?"

    sections_html = ""
    for sec in SECTIONS:
        rows = ""
        for fid, label, unit, section, filekey, pattern in FIELDS:
            if section != sec:
                continue
            if fid == "tsrInput":
                rows += f"""
                <tr class="tsr-row">
                  <td>{html.escape(label)}</td>
                  <td><input type="text" name="{fid}" placeholder="orn. 0.8"></td>
                  <td></td>
                </tr>"""
                continue
            rows += f"""
            <tr>
              <td>{html.escape(label)}</td>
              <td><input type="text" name="{fid}" value="{html.escape(v[fid])}"></td>
              <td>{html.escape(unit)}</td>
            </tr>"""
        sections_html += f"""
        <h3>{sec}</h3>
        <table>{rows}</table>"""

    msg_html = f'<div class="msg">{html.escape(msg)}</div>' if msg else ""

    return f"""<!doctype html>
<html><head><meta charset="utf-8">
<title>savonius_mrf - kontrol paneli</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 820px; margin: 2em auto; padding: 0 1em; }}
h1 {{ font-size: 1.3em; }}
h3 {{ margin-top: 1.3em; margin-bottom: 0.3em; color: #333; border-bottom: 1px solid #ccc; padding-bottom: 2px;}}
table {{ border-collapse: collapse; width: 100%; margin-bottom: 0.5em; }}
td {{ padding: 4px 8px; border-bottom: 1px solid #eee; font-size: 14px; }}
input[type=text] {{ width: 160px; padding: 3px; }}
.tsr-row td {{ color: #555; font-style: italic; }}
.actions button {{ margin: 4px 6px 4px 0; padding: 8px 14px; cursor: pointer; }}
.danger {{ background: #fdd; }}
.primary {{ background: #cfe8ff; font-weight: bold; }}
.msg {{ background: #eef; padding: 8px; margin-bottom: 1em; border-radius: 4px; white-space: pre-line; }}
.tsr {{ color: #555; font-size: 0.9em; }}
pre {{ background: #111; color: #0f0; padding: 10px; height: 240px; overflow: auto; font-size: 12px; }}
.section {{ margin-top: 1.5em; }}
.dash {{ background: #f5f5f5; border: 1px solid #ddd; border-radius: 6px; padding: 10px 14px; margin-bottom: 1em; font-size: 14px; display: grid; grid-template-columns: 1fr 1fr; gap: 4px 12px; }}
.ok {{ color: #0a0; font-weight: bold; }}
.idle {{ color: #888; }}
</style>
</head>
<body>
<h1>savonius_mrf - kontrol paneli</h1>
<p class="tsr">Hesaplanan TSR (omega*R/U, R={R_ROTOR} m): <b>{tsr_txt}</b></p>

<div id="dash">{dashboard_html()}</div>

{msg_html}
<form method="POST" action="/save">
{sections_html}
<button type="submit" class="primary">Kaydet</button>
</form>

<div class="section actions">
<h2>Calistir</h2>
<form method="POST" action="/run" style="display:inline">
<button name="action" value="Allclean">Allclean</button>
<button name="action" value="Allrun-pre">Allrun-pre (mesh)</button>
<button name="action" value="Allrun">Allrun (mesh+cozum)</button>
<button name="action" value="paraview">ParaView ac</button>
<button name="action" value="stop" class="danger">Durdur (cozucuyu kill et)</button>
</form>
<form method="POST" action="/reset" style="display:inline" onsubmit="return confirm('Tum parametreler dogrulanmis varsayilan degerlere donecek. Emin misin?');">
<button class="danger">Varsayilana Don</button>
</form>
</div>

<div class="section">
<h2>Durum (canli log kuyrugu)</h2>
<pre id="log">yukleniyor...</pre>
</div>

<script>
async function refresh() {{
  try {{
    const r = await fetch('/status');
    const t = await r.text();
    document.getElementById('log').textContent = t;
    const d = await fetch('/dash');
    document.getElementById('dash').innerHTML = await d.text();
  }} catch (e) {{}}
}}
refresh();
setInterval(refresh, 2000);
</script>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _send_html(self, body, code=200):
        b = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _send_text(self, text, code=200):
        b = text.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/index"):
            self._send_html(render_page())
        elif self.path == "/status":
            self._send_text(self._tail_status())
        elif self.path == "/dash":
            self._send_html(dashboard_html())
        else:
            self.send_response(404)
            self.end_headers()

    def _tail_status(self, n=40):
        candidates = [
            CASE / "log.simpleFoam",
            CASE / "Allrun.out",
            CASE / "Allrun-pre.out",
            CASE / "log.checkMesh",
        ]
        newest = None
        newest_mtime = -1
        for c in candidates:
            if os.path.exists(c):
                m = os.path.getmtime(c)
                if m > newest_mtime:
                    newest_mtime = m
                    newest = c
        if not newest:
            return "(henuz log yok)"
        try:
            with open(newest, errors="replace") as f:
                lines = f.readlines()
            return f"== {newest.name} ==\n" + "".join(lines[-n:])
        except Exception as e:
            return f"okuma hatasi: {e}"

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        params = parse_qs(body)

        if self.path == "/save":
            msg = self._handle_save(params)
            self._send_html(render_page(msg))
        elif self.path == "/run":
            action = params.get("action", [""])[0]
            msg = self._handle_run(action)
            self._send_html(render_page(msg))
        elif self.path == "/reset":
            try:
                apply_defaults()
                msg = "Varsayilan degerlere donuldu. Etkili olmasi icin Allclean + Allrun-pre calistir."
            except Exception as e:
                msg = f"HATA (reset): {e}"
            self._send_html(render_page(msg))
        else:
            self.send_response(404)
            self.end_headers()

    def _validate_numeric(self, key, value, allow_int_only=False):
        try:
            f = float(value)
        except ValueError:
            raise ValueError(f"{key}: '{value}' sayi degil.")
        if not math.isfinite(f):
            raise ValueError(f"{key}: sonlu bir sayi olmali.")
        if allow_int_only and f != int(f):
            raise ValueError(f"{key}: tam sayi olmali.")
        return value

    def _handle_save(self, params):
        def v(key):
            return params.get(key, [""])[0].strip()

        try:
            # Validate the entire form before writing anything. Previously a
            # bad field near the end left earlier fields partially saved.
            numeric = {
                "U": (0, None, False),
                "omega": (None, None, False),
                "endTime": (0, None, False),
                "writeInterval": (0, None, False),
                "purgeWrite": (0, None, True),
                "relaxP": (0, 1, False),
                "relaxU": (0, 1, False),
                "relaxKOmega": (0, 1, False),
                "refineRadius": (0, None, False),
                "refineLevel": (0, 6, True),
                "wakeLevel": (0, 4, True),
                "nSurfaceLayers": (0, None, True),
                "minThickness": (0, None, False),
                "gridNx": (1, None, True),
                "gridNy": (1, None, True),
            }
            for key, (minimum, maximum, integer) in numeric.items():
                if not v(key):
                    continue
                self._validate_numeric(key, v(key), allow_int_only=integer)
                number = float(v(key))
                if minimum is not None and number <= minimum:
                    op = ">=" if minimum == 0 and key in {"purgeWrite", "refineLevel", "wakeLevel", "nSurfaceLayers"} else ">"
                    if op == ">=" and number == minimum:
                        pass
                    else:
                        raise ValueError(f"{key}: {op} {minimum} olmali.")
                if maximum is not None and number > maximum:
                    raise ValueError(f"{key}: en fazla {maximum} olabilir.")

            tsr_in = v("tsrInput")
            if tsr_in:
                self._validate_numeric("TSR", tsr_in)
                if float(tsr_in) < 0:
                    raise ValueError("TSR: negatif olamaz.")
                u_for_tsr = v("U") or collect_values()["U"]
                self._validate_numeric("U", u_for_tsr)
                if float(u_for_tsr) <= 0:
                    raise ValueError("U: TSR hesabi icin sifirdan buyuk olmali.")

            if bool(v("gridNx")) != bool(v("gridNy")):
                raise ValueError("gridNx ve gridNy birlikte girilmeli.")
            if v("gridNx"):
                nx, ny = int(float(v("gridNx"))), int(float(v("gridNy")))
                if nx * ny > 60000:
                    raise ValueError(
                        f"grid: {nx}x{ny}={nx*ny:,} taban hucre cok agir; "
                        "60.000 veya altinda tut."
                    )

            if tsr_in:
                u_val = v("U") or collect_values()["U"]
                omega_calc = float(tsr_in) * float(u_val) / R_ROTOR
                set_simple("omega", f"{omega_calc:.6g}")
            elif v("omega"):
                self._validate_numeric("omega", v("omega"))
                set_simple("omega", v("omega"))

            if v("U"):
                self._validate_numeric("U", v("U"))
                set_velocity(v("U"))
            if v("endTime"):
                self._validate_numeric("endTime", v("endTime"))
                set_simple("endTime", v("endTime"))
            if v("writeInterval"):
                self._validate_numeric("writeInterval", v("writeInterval"))
                set_simple("writeInterval", v("writeInterval"))
            if v("purgeWrite"):
                self._validate_numeric("purgeWrite", v("purgeWrite"))
                set_simple("purgeWrite", v("purgeWrite"))
            if v("relaxP"):
                self._validate_numeric("relaxP", v("relaxP"))
                set_relax_p(v("relaxP"))
            if v("relaxU"):
                self._validate_numeric("relaxU", v("relaxU"))
                set_relax_u(v("relaxU"))
            if v("relaxKOmega"):
                self._validate_numeric("relaxKOmega", v("relaxKOmega"))
                set_relax_komega(v("relaxKOmega"))
            if v("refineRadius"):
                self._validate_numeric("refineRadius", v("refineRadius"))
                set_simple("refineRadius", v("refineRadius"))
            if v("refineLevel"):
                set_refine_level(v("refineLevel"))
            if v("wakeLevel"):
                set_wake_level(v("wakeLevel"))
            if v("nSurfaceLayers"):
                self._validate_numeric("nSurfaceLayers", v("nSurfaceLayers"), allow_int_only=True)
                set_simple("nSurfaceLayers", v("nSurfaceLayers"))
            if v("minThickness"):
                self._validate_numeric("minThickness", v("minThickness"))
                set_simple("minThickness", v("minThickness"))
            if v("gridNx") and v("gridNy"):
                set_grid(v("gridNx"), v("gridNy"))
        except ValueError as e:
            return f"HATA: {e}"
        except Exception as e:
            return f"HATA: {e}"
        return "Kaydedildi. Degisikliklerin etkili olmasi icin Allclean + Allrun-pre calistirman gerekebilir."

    def _handle_run(self, action):
        env = os.environ.copy()
        if action == "Allclean":
            subprocess.run(["./Allclean"], cwd=CASE, env=env, check=False)
            return "Allclean calistirildi."
        elif action == "Allrun-pre":
            self._start_background("Allrun-pre", "Allrun-pre.out", env)
            return "Allrun-pre arka planda baslatildi (birkac dakika surer, asagidaki durum kutusundan izleyebilirsin)."
        elif action == "Allrun":
            self._start_background("Allrun", "Allrun.out", env)
            return "Allrun arka planda baslatildi."
        elif action == "paraview":
            env["DISPLAY"] = ":1"
            with open("/tmp/paraFoam.log", "ab") as log:
                subprocess.Popen(
                    ["paraFoam", "-builtin", "-case", str(CASE)], env=env,
                    stdout=log, stderr=subprocess.STDOUT, start_new_session=True
                )
            return "ParaView baslatildi (masaustunde acilacak)."
        elif action == "stop":
            pid = solver_running()
            if pid:
                try:
                    os.kill(int(pid), signal.SIGTERM)
                    return f"Cozucu durduruldu (PID {pid})."
                except Exception as e:
                    return f"Durdurma hatasi: {e}"
            return "Calisan bir cozucu bulunamadi."
        return "Bilinmeyen aksiyon."

    @staticmethod
    def _start_background(script, log_name, env):
        with open(CASE / log_name, "ab") as log:
            subprocess.Popen(
                [f"./{script}"], cwd=CASE, env=env, stdout=log,
                stderr=subprocess.STDOUT, start_new_session=True
            )


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"savonius_mrf kontrol paneli: http://127.0.0.1:{PORT}")
    server.serve_forever()
