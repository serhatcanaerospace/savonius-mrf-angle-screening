# 03 Script Catalog

## 1. Geometri Script'leri

- `../analysis_scripts/rotate_blade.py`
  Rotor STL'ini acisal olarak dondurur.
- `../analysis_scripts/normalize_stl_depth.py`
  STL z-kalinligini pseudo-2D/quasi-3D domain kalinligina esler.
- `../analysis_scripts/make_angle_case.py`
  Bir template case'ten yeni aci case'i uretir.

## 2. Sonuc Ozetleme Script'leri

- `../analysis_scripts/plot_force_coeffs.py`
  Cm/Cd/Cl grafigi uretir.
- `../analysis_scripts/summarize_mrf_cases.py`
  Birden fazla case icin ozet CSV/Markdown/PNG uretir.

## 3. Yuzey ve Akis Analizi

- `../analysis_scripts/analyze_blade.py`
  Yuzey basinc dagilimini ve kritik noktalarini analiz eder.
- `../analysis_scripts/plot_blade.py`
  Blade pressure haritasi uretir.
- `../analysis_scripts/analyze_blade_rot90cw.py`
  `rot90` varyasyonu icin yardimci analiz girisi.

## 4. ParaView Script'leri

- `../analysis_scripts/paraview_blade_pressure.py`
  Yuzey VTK dosyasindan hizli screenshot alir.
- `../analysis_scripts/paraview_case_suite.py`
  OpenFOAM reader ile case tabanli coklu teknik gorsel uretir.
- `../analysis_scripts/build_paraview_report.py`
  ParaView bulgularini `.docx` rapora toplar.

## 5. UI

- `../mrf_ui/server.py`
  Parametre duzenleme ve solver kontrolu icin hafif web arayuzu.
