# Analiz script'leri

Bu klasördeki script'ler Savonius MRF case'lerinin geometri üretimi,
sonuç doğrulaması ve görselleştirmesi için kullanılıyor. Python + `vtk`
+ `matplotlib` tabanlı araçlar içerir; ayrıca `pvbatch` ile ParaView
ekran görüntüsü üretimi de desteklenir.

- `analyze_blade.py` — bir OpenFOAM case'inin `Savonius` patch'ini
  `foamToVTK` ile VTK'ya çevirip (`foamToVTK -latestTime`), kanat yüzeyindeki
  basınç dağılımını okur, en yüksek/düşük basınç noktalarını (durma/emme
  bölgeleri) ve rotor merkezine göre açılarını yazdırır.
- `plot_blade.py` — aynı veriyi kanat şekli üzerine renkli (basınç) bir
  harita olarak çizer, akış yönü ve omega okunu ekler, PNG olarak kaydeder.
- `plot_force_coeffs.py` — `postProcessing/forceCoeffs1/0/forceCoeffs.dat`
  dosyasından Cm/Cd/Cl grafiği üretir.
- `summarize_mrf_cases.py` — birden fazla case'in `forceCoeffs.dat`
  sonuçlarını okuyup CSV + Markdown tablo + toplu Cm/Cd/Cl grafiği üretir.
- `paraview_blade_pressure.py` — `pvbatch` ile `Savonius_*.vtk` yüzeyini
  ParaView render pipeline'ında renklendirip PNG ekran görüntüsü alır.
- `paraview_case_suite.py` — OpenFOAM reader ile case'i doğrudan açar ve
  orta düzlem hız + streamline, wake deficit, 3D streamtube ve yerel mesh
  görsellerini otomatik üretir.
- `build_paraview_report.py` — ParaView araştırması ve üretilen görselleri
  tek bir `.docx` teknik raporda toplar.
- `rotate_blade.py` — `constant/triSurface/rotorBlade.stl`'i rotor merkezi
  (1,1,0) etrafında istenen açıda döndürüp yeni bir STL dosyası üretir
  (yeni kanat başlangıç açısı denemeleri için, örn. `savonius_mrf_rot90cw`).
- `make_angle_case.py` — mevcut bir template case'i temiz şekilde kopyalar,
  generated çıktıları taşımaz, referans STL'i döndürür ve yeni angle-case'i
  hazırlar.
- `normalize_stl_depth.py` — pseudo-2D OpenFOAM case için STL z kalınlığını
  domain kalınlığına (`-0.1..0.1`) eşler. `empty` front/back patch kullanırken
  geometri tüm kalınlığı kaplamalıdır.

Kullanım (örnek):
```
python3 analyze_blade.py ../savonius_mrf_rot90cw
python3 plot_blade.py ../savonius_mrf_rot90cw/VTK/Savonius/Savonius_125.vtk -o blade_pressure.png
python3 plot_force_coeffs.py ../savonius_mrf -o force_coeffs.png
python3 summarize_mrf_cases.py ../savonius_mrf ../savonius_mrf_rot90cw -o ../analysis_outputs/mrf_angle_summary
pvbatch paraview_blade_pressure.py ../savonius_mrf/VTK/Savonius/Savonius_20.vtk -o paraview_blade_pressure.png
pvbatch paraview_case_suite.py ../savonius_mrf -o ../analysis_outputs/savonius_mrf_paraview_suite
python3 build_paraview_report.py
python3 rotate_blade.py <girdi.stl> <cikti.stl> <aci_derece>  # + saat yönü tersi, - saat yönü
python3 make_angle_case.py ../savonius_mrf ../savonius_mrf_rot45ccw 45
python3 normalize_stl_depth.py <girdi.stl> <cikti.stl> --z-min -0.1 --z-max 0.1
```

`analyze_blade.py` VTK dosyası verilmezse seçilen case içindeki en son
`Savonius_*.vtk` dosyasını otomatik bulur. Ana case varsayılandır. Henüz
`foamToVTK` üretilmemişse anlaşılır bir hata verir. `plot_blade.py` çıktıyı
varsayılan olarak çalışma dizinindeki `blade_pressure.png` dosyasına yazar.

Not: Bu makinede `python3-paraview` kuruldu; `pvbatch` tabanli script
kullanilabilir. Sistem paketi kurulumu sonrasinda analiz tarafinda gerekli
`vtk` ve `paraview.simple` importlari dogrulandi.
