# Savonius OpenFOAM CFD Teknik Raporu — 2026-07-10

## 1. Kapsam

Bu çalışma klasöründeki üç OpenFOAM case'i incelendi, temizlendi, yeniden
mesh'lendi ve kısa çalıştırma testlerinden geçirildi:

- `savonius_mrf`: steady MRF / `simpleFoam`
- `savonius_mrf_rot90cw`: -90° döndürülmüş rotor konumu / `simpleFoam`
- `savonius_mrf_transient`: donuk rotor geometrili transient MRF / `pimpleFoam`

Amaç, case'leri "çalışıyor görünüyor" seviyesinden çıkarıp tekrarlanabilir,
kontrollü, hataya daha dayanıklı ve raporlanabilir bir OpenFOAM iş akışına
getirmekti.

Raporun bu güncellemesinde ayrıca açı taramasını ölçeklemek için otomasyon
araçları eklendi ve yeni bir 45 derece case iskeleti üretildi:

- `savonius_mrf_rot45ccw`: +45 deg döndürülmüş rotor / mesh hazırlanmış

## 2. Kullanılan teknik dayanaklar

Yerel OpenFOAM sözlükleri ve tutorial örnekleri kontrol edildi. Ayrıca ilgili
OpenFOAM dokümantasyonu internetten doğrulandı:

- OpenFOAM mesh boundary dokümantasyonu: `empty` patch'lerin 1D/2D modellerde
  kullanıldığı, `symmetryPlane` patch'in ise düzlemsel simetri sınırı olduğu
  açıkça belirtiliyor.
  <https://doc.cfd.direct/openfoam/user-guide-v13/boundaries>
- `snappyHexMesh`, STL/OBJ tri-surface geometrilerden 3 boyutlu hex/split-hex
  mesh üreten bir araçtır; castellated mesh, snapping ve opsiyonel layer
  aşamalarını içerir.
  <https://doc.cfd.direct/openfoam/user-guide-v13/snappyhexmesh>
- `forceCoeffs`, kuvvet ve moment katsayılarını yazan `forces` functionObject
  uzantısıdır; `patches`, `liftDir`, `dragDir`, `pitchAxis`, `magUInf`, `lRef`,
  `Aref` gibi girdiler gerektirir.
  <https://cpp.openfoam.org/v13/classFoam_1_1functionObjects_1_1forceCoeffs.html>
- MRF örneğinde `MRFProperties` içinde `cellZone rotor`, `origin`, `axis` ve
  `omega` yapısı resmi OpenFOAM tutorial mantığıyla uyumludur.
  <https://raw.githubusercontent.com/OpenFOAM/OpenFOAM-4.x/master/tutorials/compressible/rhoPimpleFoam/ras/mixerVessel2D/constant/MRFProperties>

## 3. Yapılan ana düzeltmeler

### 3.1 Eski ve kirli sonuçlar arşivlendi

Önceden üretilmiş mesh, zaman klasörleri, VTK çıktıları, `postProcessing`
verileri ve loglar yeni validasyonla karışmasın diye şu klasöre taşındı:

`archive/generated_before_remesh_20260710_095241/`

Kaynak case dosyaları korunarak yalnız generated/çalıştırma çıktıları
arşivlendi.

### 3.2 Geometri z-derinliği düzeltildi

Eski STL geometri yaklaşık `z=0..0.1` aralığındaydı; domain ise
`z=-0.1..0.1` idi. Bu, 2D/empty yaklaşımı ve snappy sonrası patch topolojisi
için tutarsız bir kurulum üretiyordu.

Yapılanlar:

- Orijinal STL yedeklendi:
  `geometry/original/rotorBlade_horizontal_z0_0p1.stl`
- Yeni geometri `z=-0.11..0.11` aralığına normalize edildi:
  `geometry/rotorBlade_horizontal.stl`
- `savonius_mrf`, `savonius_mrf_transient` ve `savonius_mrf_rot90cw` geometrileri
  bu yeni mantıkla yeniden üretildi.
- `surfaceCheck` ile yüzeylerin kapalı olduğu ve illegal triangle içermediği
  doğrulandı.

İlgili yardımcı script:

`analysis_scripts/normalize_stl_depth.py`

### 3.3 Pseudo-2D `empty` modelden ince 3D/symmetry modele geçildi

`snappyHexMesh` 3D bir mesher olduğu ve kapalı STL ile 1 hücre kalınlığında
`empty` topolojisini güvenilir şekilde korumadığı için case'ler ince 3D /
quasi-3D modele çevrildi.

Yapılan model değişikliği:

- `front` ve `back`: `symmetryPlane`
- `topAndBottom`: `slip`
- z-yönü hücre sayısı: `1` yerine `4`

Bu seçim, otomatik ve tekrarlanabilir pipeline için daha sağlamdır. Bedeli:
tam 2D idealizasyon yerine ince 3D simetri modeli çözülür. Bu Savonius gibi
zamana bağlı iz/vorteks davranışı olan bir problemde hâlâ yaklaşık modeldir.
Yüksek doğruluk için nihai öneri, CAD/Salome tabanlı temiz 3D mesh veya AMI /
sliding-mesh iş akışıdır.

### 3.4 Boundary-layer katmanları kontrollü olarak kapatıldı

Layer üretimi birkaç alternatifle test edildi. 4 layer ve 2 layer denemeleri
temel `checkMesh` açısından çalışsa da ayrıntılı `checkMesh -allTopology
-allGeometry` kontrolünde concave-cell sayısını azaltmak yerine korudu.

Otomatik ve stabil baseline için:

- `addLayers false`

olarak bırakıldı. `addLayersControls` sözlükleri dosyalarda duruyor ancak aktif
değil. Bu bilinçli bir mühendislik tercihidir: mevcut STL/surface kalitesiyle
çözücüyü güvenli başlatan, tekrarlanabilir mesh önceliklendirildi. Sınır tabaka
doğruluğu için sonraki doğru adım STL üzerinde zorlayarak layer basmak değil,
geometriyi/CAD'i temizleyip layer mesh'i yeniden tasarlamaktır.

### 3.5 Allrun-pre / Allrun iş akışı sertleştirildi

Case hazırlama ve koşu script'leri şu mantığa getirildi:

- eski zaman/mesh/VTK/postProcessing/log çıktıları temizlenir,
- `surfaceCheck` çalışır,
- `blockMesh` çalışır,
- `snappyHexMesh -overwrite` çalışır,
- `topoSet` ile rotor `cellZone` oluşturulur,
- `createPatch` ile patch adları ve tipleri düzenlenir,
- temel `checkMesh` çalışır,
- kritik mesh hataları yakalanırsa solver başlatılmaz.

Fatal kabul edilen mesh hataları:

- boş/topolojik olarak geçersiz mesh,
- çoklu bağlantısız region,
- negatif hacim/alan,
- küçük determinant,
- yüksek skewness,
- ciddi face/cell volume hataları.

`checkMesh -allTopology -allGeometry` içinde yalnız concave-cell tanısı kalırsa
bu raporda ayrıca belirtilir; otomatik solver smoke testini tek başına
durduracak fatal kategoriye alınmadı.

### 3.6 Çıktı ve disk kullanımı düzenlendi

Steady case'lerde:

- `writeInterval 100`
- `purgeWrite 5`
- `writeFormat binary`

Transient case'te:

- `writeInterval 0.02`
- `purgeWrite 20`
- `writeFormat binary`

Amaç, uzun koşularda klasörün kontrolsüz şişmesini önlemek ve yalnız gerekli
sonuçları tutmaktır.

### 3.7 UI ve analiz script'leri iyileştirildi

Önceki UI/script düzeltmeleriyle birlikte:

- hız değişince `k`, `omega` ve `forceCoeffs.magUInf` tutarlı ölçekleniyor,
- form doğrulaması yazmadan önce bütün alanlarda yapılıyor,
- solver proses tespiti seçili case dizinine göre yapılıyor,
- shell-string bazlı riskli çağrılar kaldırıldı,
- analiz script'leri case yolunu parametre alabilir hale getirildi,
- yeni görselleştirme script'leri eklendi:
  - `analysis_scripts/make_angle_case.py`
  - `analysis_scripts/plot_force_coeffs.py`
  - `analysis_scripts/summarize_mrf_cases.py`
  - `analysis_scripts/paraview_blade_pressure.py`

### 3.8 Açı taraması otomasyonu eklendi

Elle kopyalama/döndürme yerine iki yeni araç eklendi:

- `analysis_scripts/make_angle_case.py`
  Mevcut bir template case'i kopyalar, generated çıktıları atar, referans STL'i
  verilen açı kadar döndürür ve yeni case içine `ANGLE_INFO.txt` metadata'sı
  yazar.
- `analysis_scripts/summarize_mrf_cases.py`
  Birden fazla case'in `forceCoeffs.dat` dosyasını okuyup CSV, Markdown tablo ve
  toplu Cm/Cd/Cl grafiği üretir.

Bu sayede MRF frozen-rotor açı taraması artık tekrarlanabilir ve raporlanabilir
bir iş akışına dönüştürüldü.

## 4. Final mesh validasyonu

### 4.1 `savonius_mrf`

Temel `checkMesh` sonucu:

- Durum: `Mesh OK`
- Hücre sayısı: `965040`
- Region sayısı: `1 (OK)`
- Maksimum aspect ratio: `4.341597`
- Maksimum non-orthogonality: `44.95766`
- Ortalama non-orthogonality: `3.415993`
- Maksimum skewness: `1.535327`

Ayrıntılı `checkMesh -allTopology -allGeometry` sonucu:

- `Failed 1 mesh checks`
- Kalan tanı: concave cells
- Concave cell sayısı: `8584`
- Concave face sayısı: `63`
- Maksimum concave angle: `64.85598°`

Değerlendirme: temel OpenFOAM kalite kontrolü çözücü başlatmaya izin veriyor.
Kalan concave tanısı yüksek doğruluk çalışması için iyileştirme hedefi olarak
duruyor; mevcut baseline smoke/ön analiz için kabul edilebilir.

### 4.2 `savonius_mrf_rot90cw`

Temel `checkMesh` sonucu:

- Durum: `Mesh OK`
- Hücre sayısı: `971968`
- Region sayısı: `1 (OK)`
- Maksimum aspect ratio: `4.046879`
- Maksimum non-orthogonality: `39.23003`
- Ortalama non-orthogonality: `3.27662`
- Maksimum skewness: `1.014329`

Ayrıntılı `checkMesh -allTopology -allGeometry` sonucu:

- `Failed 1 mesh checks`
- Kalan tanı: concave cells
- Concave cell sayısı: `8432`

Değerlendirme: rot90 mesh, temel kalite metriklerinde ana case'ten biraz daha
temizdir. Kalan sınırlayıcı konu yine concave-cell tanısıdır.

### 4.3 `savonius_mrf_transient`

Transient case aynı geometri/mesh mantığını kullandığı için ana case mesh'i
ile hizalandı.

Temel `checkMesh` sonucu:

- Durum: `Mesh OK`
- Hücre sayısı: `965040`
- Region sayısı: `1 (OK)`
- Maksimum aspect ratio: `4.341597`
- Maksimum non-orthogonality: `44.95766`
- Ortalama non-orthogonality: `3.415993`
- Maksimum skewness: `1.535327`

Ayrıntılı kontrol:

- `Failed 1 mesh checks`
- Kalan tanı: concave cells
- Concave cell sayısı: `8584`

### 4.4 `savonius_mrf_rot45ccw`

Bu case yeni otomasyon script'i ile üretildi ve `./Allrun-pre` çalıştırılarak
mesh pipeline'ı doğrulandı.

`checkMesh -allTopology -allGeometry` sonucu:

- Hücre sayısı: `969648`
- Region sayısı: `1 (OK)`
- Maksimum aspect ratio: `3.983356`
- Maksimum non-orthogonality: `40.50979`
- Ortalama non-orthogonality: `3.287344`
- Maksimum skewness: `2.259522`
- Minimum determinant: `0.3481278`
- Concave cell sayısı: `7980`
- Sonuç: `Failed 1 mesh checks` (kalan tanı: concave cells)

Değerlendirme: 45 derece geometri de mevcut baseline kalite mantığı içinde
başarılı şekilde üretildi. Mesh metrikleri, ana case ve `rot90` case ile aynı
sınıfta ve bazı ölçütlerde daha iyidir.

## 5. Solver smoke testleri

Bu koşular nihai CFD sonucu değildir. Amaç; case kurulumu, boundary condition,
MRF zone, turbulence fields, `forceCoeffs`, solver stabilitesi ve post-processing
pipeline'ının fatal hata vermeden çalıştığını doğrulamaktır.

### 5.1 `savonius_mrf` / `simpleFoam`

- Test süresi: `endTime 20`
- Durum: tamamlandı
- Fatal error / NaN / floating point hatası: yok
- Son kayıt:
  - `Cm = 0.176796`
  - `Cd = 0.880712`
  - `Cl = -0.412627`
- Son 10 kayıt ortalaması:
  - `Cm = 0.467505`
  - `Cd = 0.453202`
  - `Cl = -1.066948`

Not: Bu kısa test kuvvet katsayılarını fiziksel performans sonucu olarak
kullanmak için yeterli değildir. Yakınsama/ortalama analizi için daha uzun koşu
gerekir.

### 5.2 `savonius_mrf_rot90cw` / `simpleFoam`

- Test süresi: `endTime 20`
- Durum: tamamlandı
- Fatal error / NaN / floating point hatası: yok
- Son kayıt:
  - `Cm = -0.096108`
  - `Cd = 3.237397`
  - `Cl = 0.824956`

Not: Tek açılı MRF sonucu, Savonius rotorunun tur ortalamasıyla doğrudan
karşılaştırılmamalıdır. MRF burada açısal tarama / frozen-rotor ön analiz
aracıdır.

### 5.3 `savonius_mrf_transient` / `pimpleFoam`

- Test süresi: `endTime 0.001`
- Durum: tamamlandı
- Fatal error / NaN / floating point hatası: yok
- Maksimum Courant sayısı: yaklaşık `0.765` ile `maxCo=1` altında kaldı
- Son kayıt:
  - `Cm = 0.069630`
  - `Cd = 4.777630`
  - `Cl = -1.545478`

Not: Bu yalnız transient kurulumun stabil başladığını gösterir. Akış fiziği,
periyodik vorteks davranışı veya moment ortalaması için çok daha uzun fiziksel
zaman çözülmelidir.

## 6. Görselleştirme ve post-processing çıktıları

Üretilen ana çıktılar:

- `analysis_outputs/force_coeffs_smoke.png`
- `analysis_outputs/blade_pressure_smoke.png`
- `analysis_outputs/paraview_blade_pressure_smoke.png`
- `analysis_outputs/mrf_angle_summary.csv`
- `analysis_outputs/mrf_angle_summary.md`
- `analysis_outputs/mrf_angle_summary.png`

Ana case için `foamToVTK -latestTime -fields '(p U)' -noInternal` çalıştırıldı.
Kanat yüzeyi VTK çıktısından basınç dağılımı analiz edildi:

- Yüz sayısı: `21248`
- Maksimum basınç: `25.9302`
- Maksimum basınç konumu yaklaşık:
  `(0.75847, 0.75401, -0.0987)`
- Maksimum basınç açısı: yaklaşık `-134.5°`
- Minimum basınç: `-83.5240`
- Minimum basınç konumu yaklaşık:
  `(0.95101, 1.0124, -0.0985)`
- Minimum basınç açısı: yaklaşık `165.8°`

ParaView batch görselleştirmesi için `python3-paraview` kuruldu ve
`pvbatch` tabanlı screenshot üretimi doğrulandı.

Sistem paketi notu: `python3-paraview` kurulumu sırasında paket yöneticisi bazı
VTK/ROS/PCL geliştirme paketlerini kaldırdı (`python3-vtk9`,
`libvtk9-dev`, `libvtk9-qt-dev`, `libpcl-dev`, `ros-jazzy-desktop`,
`ros-jazzy-pcl-conversions`). Kurulum sonrası bu çalışma için gerekli
`vtk`, `vtkmodules`, `paraview.simple`, `numpy` ve `matplotlib` importları
başarılıdır.

## 7. Mevcut teknik sınırlamalar

1. **MRF, gerçek dönen rotor değildir.** Kanat konumu dondurulur. Savonius gibi
   güçlü zamana bağlı ve açıya duyarlı rotorlar için tek MRF açısı, AMI/sliding
   mesh tur ortalamasının yerine geçmez.
2. **Boundary-layer kapalıdır.** Mevcut baseline stabil ve tekrarlanabilir,
   fakat duvar-shear / y+ / separation doğruluğu için ideal değildir.
3. **Concave-cell tanısı kalmıştır.** Temel kalite metrikleri iyi olsa da
   yüksek doğruluk mesh çalışmasında bu azaltılmalıdır.
4. **Smoke testler kısa tutulmuştur.** Kuvvet katsayıları pipeline tanısıdır,
   nihai performans sonucu değildir.

## 8. Sonraki mühendislik adımları

Öncelik sırasına göre:

1. Salome/FreeCAD ile rotor geometrisini temiz CAD/surface olarak yeniden
   üretmek.
2. Temiz geometri üzerinde boundary-layer mesh'i yeniden açmak ve concave-cell
   sayısını düşürmek.
3. MRF açı taraması yapmak: örneğin 0°, 45°, 90°, 135°... ayrı case'ler veya
   otomasyon script'i.
4. Her açı için `Cm` ortalaması almak; bunu AMI/sliding-mesh sonucu ile yalnız
   "yaklaşık frozen-rotor tarama" olarak karşılaştırmak.
5. Nihai performans için AMI/sliding-mesh transient case kurmak veya mevcut
   AMI case ile aynı referans alan/hız/mesh kalite seviyesinde karşılaştırmak.

## 9. Tekrarlanabilir komutlar

Mesh hazırlama:

```bash
cd savonius_mrf
./Allrun-pre
```

Steady smoke/full koşu:

```bash
cd savonius_mrf
./Allrun
```

Rot90 case:

```bash
cd savonius_mrf_rot90cw
./Allrun-pre
./Allrun
```

Transient case:

```bash
cd savonius_mrf_transient
./Allrun
```

Force coefficient plot:

```bash
python3 analysis_scripts/plot_force_coeffs.py savonius_mrf \
  -o analysis_outputs/force_coeffs.png
```

Kanat yüzeyi VTK:

```bash
cd savonius_mrf
foamToVTK -latestTime -fields '(p U)' -noInternal
```

ParaView batch screenshot:

```bash
pvbatch analysis_scripts/paraview_blade_pressure.py \
  savonius_mrf/VTK/Savonius/Savonius_20.vtk \
  analysis_outputs/paraview_blade_pressure.png
```

## 10. Sonuç

Case'ler artık eski üretilmiş çıktılardan arındırılmış, geometrisi düzeltilmiş,
tekrarlanabilir mesh pipeline'ı olan ve kısa solver testlerinden geçmiş bir
baseline halindedir.

Bu baseline'ın mühendislik değeri: hızlı, çalışır ve hata yakalayan bir MRF
ön analiz altyapısıdır.

Bu baseline'ın fiziksel sınırlaması: boundary-layer kapalı ve MRF frozen-rotor
yaklaşımı olduğu için nihai Savonius performans sayısı olarak raporlanmamalıdır.
Nihai doğruluk için bir sonraki ciddi adım, temiz CAD + layer mesh + uzun
transient/AMI karşılaştırmasıdır.
