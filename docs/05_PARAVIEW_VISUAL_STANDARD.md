# 05 ParaView Visual Standard

## 1. Problem

Savonius gibi geometriye duyarli bir case'te "ekran goruntusu almak" ile
"fizigi anlatan teknik gorsel uretmek" ayni sey degildir.

Kotu gorsel belirtileri:

- domainin buyuk bos alanlari kadraji isgal ediyor
- rotor kucucuk kaliyor
- renk haritasi fiziksel mesaj tasimiyor
- streamlines cok fazla veya cok seyrek
- mesh resmi sadece dekor oluyor

## 2. Bu Proje Icin Kabul Edilen Gorsel Tipleri

1. Rotor odakli orta-duzlem hiz kesiti
2. Rotor odakli streamline gorseli
3. Wake-deficit gorseli
4. 3D streamtube / wake sapma gorseli
5. Yerel mesh yogunlugu dogrulama gorseli

## 3. Bu Proje Icin Zayif Gorsel Tipleri

- tum domaini bos alanla gosteren uzak kameralar
- sadece renkli ama geometriyi kaybettiren pressure gorunumleri
- mesh kalitesini anlatmayan asiri uzak mesh ekranlari
- derived field'i sorgulamadan kullanilan vorticity sahneleri

## 4. Sahne Kurma Kurallari

- Kamera rotor ve yakin wake etrafinda kurulacak.
- Slice/ROI ile gereksiz domain alani kesilecek.
- Streamline sayisi okunabilirlik odakli secilecek.
- Blade gerekiyorsa siyah/gri referans siluet olarak sahnede kalacak.
- 3D sahnede streamtube kalinligi raporda okunabilir olacak.
- Colorbar basliklari fiziksel olarak acik olacak.

## 5. Teknik Not

Mevcut meshte `Gradient` tabanli derived alanlar her zaman sorunsuz degil.
Bu yuzden wake yorumu icin `uDeficit = U_inlet - Ux` gibi daha guvenilir
gosterimler birinci tercih olmalidir.
