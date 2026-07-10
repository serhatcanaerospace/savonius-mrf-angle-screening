# 01 Project Overview

## 1. Problem Tanimi

Bu proje, Savonius rotorunun OpenFOAM ile MRF tabanli CFD analizine odaklanir.
Amac yalniz bir case calistirmak degil; case kurulumunu duzgunlestirmek,
tekrarlanabilir mesh/solver is akisi kurmak, aci taramasini otomatiklestirmek
ve gorsellestirme/raporlama kalitesini profesyonel seviyeye cikarmaktir.

## 2. Proje Kapsami

- steady MRF case
- dondurulmus aci varyasyonlari
- transient MRF smoke testi
- mesh kalite denetimi
- force coefficient ozetleme
- ParaView otomasyonu
- teknik raporlama

## 3. Teknik Durum

- Ana steady case calisiyor.
- `rot90` case smoke test seviyesinde calisiyor.
- `rot45` case mesh seviyesinde hazir.
- transient case kisa `pimpleFoam` smoke testinden gecti.

## 4. Mevcut Sinirlar

- Bu MRF yaklasimi frozen-rotor mantigindadir; gercek dinamik donus degildir.
- Boundary-layer katmanlari su an kapali tutulmustur.
- Ayrintili `checkMesh` tarafinda concave-cell tanisi kalmistir.
- ParaView gorselleri hala iyilestirme surecindedir; mevcut pipeline
  dokumante edilmis ancak son estetik/mesaj kalitesi icin yeni iterasyonlar
  gerekebilir.
