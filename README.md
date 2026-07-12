# Savonius Rotor — OpenFOAM MRF CFD Çalışması

![OpenFOAM](https://img.shields.io/badge/OpenFOAM-CFD-1F6FEB?style=flat) ![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat) ![Status](https://img.shields.io/badge/status-active-brightgreen?style=flat)

Bu depo, bir Savonius tipi dikey eksenli rüzgar rotorunun OpenFOAM ile
**MRF (Multiple Reference Frame)** tabanlı hesaplamalı akışkanlar dinamiği
(CFD) analizini içerir. Amaç, tek bir case'i çalıştırmaktan öte,
**tekrarlanabilir bir mesh/solver iş akışı**, **kanat açısı taramasını
otomatikleştiren araçlar** ve **teknik olarak savunulabilir raporlama**
kurmaktır.

## İçindekiler

- [Yöntem](#yöntem)
- [Klasör yapısı](#klasör-yapısı)
- [Gereksinimler](#gereksinimler)
- [Hızlı başlangıç](#hızlı-başlangıç)
- [Mevcut durum](#mevcut-durum)
- [Ana bulgular](#ana-bulgular)
- [Bilinen sınırlamalar](#bilinen-sınırlamalar)
- [Dokümantasyon haritası](#dokümantasyon-haritası)
- [Atıf / lisans](#atıf--lisans)

## Yöntem

Klasik "gerçek dönen rotor" simülasyonu (AMI / sliding-mesh, `pimpleFoam`)
yerine bu çalışma **MRF ("frozen rotor")** yaklaşımını kullanır:

- Mesh sabit kalır; rotor bölgesine ait `cellZone` içine dönme etkisi
  (Coriolis + merkezkaç kaynak terimi) eklenir, gerçek mesh hareketi yoktur.
- Genelde `simpleFoam` (steady-state) ile çözülür; bir AMI/sliding-mesh
  koşusuna göre çok daha hızlıdır (dakikalar vs. günler mertebesinde).
- Bedeli: kanat konumu **tek bir açıda dondurulur**. Savonius gibi momenti
  açıya göre güçlü değişen bir geometride, tek bir MRF koşusu turun
  ortalamasını temsil etmez. Bu nedenle proje, **birden fazla kanat açısında
  ayrı MRF koşuları** alıp sonuçları karşılaştırma/otomasyon araçları içerir.

Yöntemin literatür karşılığı ve sınırları için bkz.
[`MRF_LITERATUR_ARASTIRMASI.md`](MRF_LITERATUR_ARASTIRMASI.md).

## Klasör yapısı

```
work2/
├── README.md                      # bu dosya
├── docs/                          # merkezi proje dokümantasyonu (00-05)
│   └── internal/                  # oturum-içi çalışma notları (bkz. aşağı)
├── TEKNIK_CFD_RAPORU_2026-07-10.md
├── OPENFOAM_CASE_DENETIMI.md
├── MRF_LITERATUR_ARASTIRMASI.md
├── PARAVIEW_TEKNIK_RAPOR_2026-07-10.docx
├── savonius_mrf/                  # ana steady-state MRF case (referans)
├── savonius_mrf_rot90cw/          # -90° kanat açısı case'i
├── savonius_mrf_rot45ccw/         # +45° kanat açısı case'i
├── savonius_mrf_transient/        # transient MRF (pimpleFoam) case'i
├── analysis_scripts/              # geometri, özetleme, plot, ParaView otomasyonu
├── analysis_outputs/              # üretilmiş grafik/özet/screenshot çıktıları
├── geometry/                      # kullanılan STL geometri dosyaları
├── archive/                       # yeniden mesh'lenmeden önceki eski çıktılar
└── mrf_ui/                        # parametre düzenleme için hafif web arayüzü
```

## Gereksinimler

- **OpenFOAM 8** (case sözlükleri bu sürümün `foamDictionary` parser'ından
  denetlenmiştir; bkz. [`OPENFOAM_CASE_DENETIMI.md`](OPENFOAM_CASE_DENETIMI.md)).
- Python 3 + `vtk`, `matplotlib`, `numpy` (analiz script'leri için).
- (Opsiyonel) `python3-paraview` / `pvbatch` — ParaView tabanlı otomatik
  görselleştirme script'leri için.

## Hızlı başlangıç

En güvenilir başlangıç noktası `savonius_mrf/` case'idir.

```bash
cd savonius_mrf
./Allrun-pre     # surfaceCheck + blockMesh + snappyHexMesh + topoSet + createPatch + checkMesh
./Allrun         # simpleFoam koşusu (kritik mesh hatası varsa solver başlatılmaz)
```

Sonuç grafikleri ve özetleri üretmek için:

```bash
python3 analysis_scripts/plot_force_coeffs.py savonius_mrf \
  -o analysis_outputs/force_coeffs.png

python3 analysis_scripts/summarize_mrf_cases.py \
  savonius_mrf savonius_mrf_rot90cw \
  -o analysis_outputs/mrf_angle_summary
```

Diğer case'ler ve script'lerin tam kullanımı için
[`docs/02_CASE_CATALOG.md`](docs/02_CASE_CATALOG.md) ve
[`docs/03_SCRIPT_CATALOG.md`](docs/03_SCRIPT_CATALOG.md) dosyalarına bakın.

## Mevcut durum

*(2026-07-11 itibarıyla, gerçek case klasörleri ve log dosyaları temel alınarak doğrulanmıştır.)*

| Case | Mesh | Solver smoke run | Not |
|---|---|---|---|
| `savonius_mrf` | hazır (`Mesh OK`, ~965K hücre) | tamamlandı (`log.simpleFoam.smoke`) | ana referans case |
| `savonius_mrf_rot90cw` | hazır | tamamlandı (`log.simpleFoam.smoke`) | -90° kanat açısı |
| `savonius_mrf_rot45ccw` | hazır (`ANGLE_INFO.txt` mevcut) | **henüz koşulmadı** | solver smoke run için `Allrun` çalıştırılmalı |
| `savonius_mrf_transient` | hazır | tamamlandı (`log.pimpleFoam.smoke`) | kısa transient stabilite testi |

Bu tablo `docs/02_CASE_CATALOG.md` ile tutarlıdır; ayrıntılı mesh kalite
metrikleri ve solver test kayıtları için
[`TEKNIK_CFD_RAPORU_2026-07-10.md`](TEKNIK_CFD_RAPORU_2026-07-10.md) bölüm 4-5'e
bakın.

## Ana bulgular

- MRF kurulumu, `simpleFoam`/`pimpleFoam` için fatal hatasız, tekrarlanabilir
  bir mesh→solver→post-processing hattı üretiyor
  (`Allrun-pre` → `Allrun` → `analysis_scripts/`).
- MRF'in tek açılı sonucu (Cm/Cd/Cl), AMI/sliding-mesh tur ortalamasıyla
  doğrudan karşılaştırılamaz — bu beklenen, "frozen rotor" yaklaşımının
  doğal sonucudur (bkz. `MRF_LITERATUR_ARASTIRMASI.md`).
- Farklı arka plan mesh sıklıklarıyla yapılan bir denemede, mesh
  inceldikçe `simpleFoam` kuvvet katsayılarının kararlı bir steady-state'e
  oturmadığı gözlemlendi; bu, kaba mesh'in konuyu sayısal difüzyonla
  "yapay olarak" sakinleştirdiğine işaret edebilir ve tek başına MRF'in
  Savonius için bir hızlı-tarama aracı olarak kaldığının bir kanıtıdır
  (ayrıntı için `docs/internal/DURUM_RAPORU_ve_YAPILACAKLAR.md`, bölüm 10).
- ParaView tabanlı görselleştirme otomasyonu kurulu, ancak "fiziği doğru
  anlatan sahne kurgusu" hâlâ iyileştirme sürecindedir
  (bkz. [`docs/05_PARAVIEW_VISUAL_STANDARD.md`](docs/05_PARAVIEW_VISUAL_STANDARD.md)).

## Bilinen sınırlamalar

1. **MRF gerçek dönen rotor değildir.** Kanat konumu dondurulur; nihai
   performans sayısı için AMI/sliding-mesh gerekir.
2. **Boundary-layer katmanları şu an kapalıdır** (`addLayers false`) —
   bilinçli bir mühendislik tercihi, duvar-shear/y+ doğruluğu bunun
   bedelidir.
3. **`checkMesh -allTopology -allGeometry` içinde concave-cell tanısı
   kalmıştır** (temel `checkMesh` geçiyor, ayrıntılı kontrol tek kalan
   tanıyı raporluyor).
4. **Solver koşuları "smoke test" seviyesindedir** — fatal hata/ıraksama
   olmadığını doğrular, nihai performans sonucu değildir.

Tüm sınırlamaların ayrıntılı gerekçesi için
[`TEKNIK_CFD_RAPORU_2026-07-10.md`](TEKNIK_CFD_RAPORU_2026-07-10.md) bölüm 7
ve [`OPENFOAM_CASE_DENETIMI.md`](OPENFOAM_CASE_DENETIMI.md) dosyalarına bakın.

## Dokümantasyon haritası

Bu proje için ilk okunacak dosyalar:

1. [`docs/00_MASTER_INDEX.md`](docs/00_MASTER_INDEX.md) — dokümantasyon giriş noktası
2. [`docs/01_PROJECT_OVERVIEW.md`](docs/01_PROJECT_OVERVIEW.md) — kapsam ve teknik durum
3. [`docs/02_CASE_CATALOG.md`](docs/02_CASE_CATALOG.md) — case bazlı ayrıntı
4. [`docs/03_SCRIPT_CATALOG.md`](docs/03_SCRIPT_CATALOG.md) — script kullanımı
5. [`docs/04_REPORT_CATALOG.md`](docs/04_REPORT_CATALOG.md) — rapor kataloğu
6. [`docs/05_PARAVIEW_VISUAL_STANDARD.md`](docs/05_PARAVIEW_VISUAL_STANDARD.md) — görselleştirme standardı

Ana teknik teslimler:

- CFD durum raporu: [`TEKNIK_CFD_RAPORU_2026-07-10.md`](TEKNIK_CFD_RAPORU_2026-07-10.md)
- OpenFOAM denetimi: [`OPENFOAM_CASE_DENETIMI.md`](OPENFOAM_CASE_DENETIMI.md)
- MRF literatür/yöntem notu: [`MRF_LITERATUR_ARASTIRMASI.md`](MRF_LITERATUR_ARASTIRMASI.md)
- ParaView teknik raporu: `PARAVIEW_TEKNIK_RAPOR_2026-07-10.docx`

`docs/internal/` klasörü, geliştirme sürecinde tutulan oturum-içi çalışma
notlarını içerir (ör. hangi mesh denemesinin neden başarısız olduğu). Bu
notlar projenin geçmişini izlenebilir kılmak için saklanır; dış bir
okuyucunun projeyi anlaması için **gerekli değildir** — yukarıdaki liste
yeterlidir.

## Atıf / lisans

Bu depo bir akademik/mentörlük CFD çalışmasının parçasıdır. Ayrı bir LİSANS
dosyası eklenmemiştir; yeniden kullanım veya atıf için depo sahibiyle
iletişime geçin.

---

## 📬 İletişim

[![Email](https://img.shields.io/badge/Email-serhatcandalmis%40gmail.com-D14836?style=flat&logo=gmail&logoColor=white)](mailto:serhatcandalmis@gmail.com)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Serhat%20Can%20Dalm%C4%B1%C5%9F-0A66C2?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/aerospaceserhatd/)
[![GitHub](https://img.shields.io/badge/GitHub-serhatcanaerospace-181717?style=flat&logo=github&logoColor=white)](https://github.com/serhatcanaerospace)

Sorular, işbirliği önerileri veya hata bildirimleri için Issues sekmesini de kullanabilirsiniz.
