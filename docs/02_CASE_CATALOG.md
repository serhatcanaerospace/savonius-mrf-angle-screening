# 02 Case Catalog

## 1. `savonius_mrf`

Amac:

- Ana steady-state MRF referans case'i

Solver:

- `simpleFoam`

Durum:

- Mesh hazir
- Smoke run tamam
- `forceCoeffs` mevcut
- VTK ve ParaView ciktisi mevcut

Ana dosyalar:

- `../savonius_mrf/Allrun`
- `../savonius_mrf/Allrun-pre`
- `../savonius_mrf/system/`
- `../savonius_mrf/constant/`

## 2. `savonius_mrf_rot90cw`

Amac:

- Rotorun -90 derece dondurulmus aci varyasyonu

Solver:

- `simpleFoam`

Durum:

- Mesh hazir
- Smoke run tamam
- `forceCoeffs` mevcut
- ParaView suite ciktisi mevcut

## 3. `savonius_mrf_rot45ccw`

Amac:

- Rotorun +45 derece dondurulmus aci varyasyonu

Solver:

- `simpleFoam` hedefleniyor

Durum:

- Mesh hazir
- `ANGLE_INFO.txt` mevcut
- Solver smoke run henuz ana case kadar ilerletilmedi

## 4. `savonius_mrf_transient`

Amac:

- Transient MRF smoke/stability case'i

Solver:

- `pimpleFoam`

Durum:

- Mesh hazir
- Kisa transient smoke run tamam
- `forceCoeffs` mevcut
- ParaView suite ciktisi mevcut

## 5. Case Kullanimi

Mesh uretimi:

- `./Allrun-pre`

Solver:

- steady case'lerde `./Allrun`
- transient case'te `./Allrun`
