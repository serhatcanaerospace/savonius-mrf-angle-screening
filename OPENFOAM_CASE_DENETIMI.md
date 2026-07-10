# OpenFOAM Case Denetimi — 2026-07-10

## Kapsam

Denetlenen case'ler:

- `savonius_mrf`: steady MRF / `simpleFoam`
- `savonius_mrf_rot90cw`: -90° kanat açısı / `simpleFoam`
- `savonius_mrf_transient`: donuk rotor geometrili transient MRF / `pimpleFoam`

Tüm `0`, `constant` ve `system` sözlükleri OpenFOAM 8 `foamDictionary`
parser'ından geçirildi. Üç case'in sınır koşulları, MRF bölgesi, türbülans
modeli, kuvvet referansları, sayısal şemaları ve çalıştırma betikleri
karşılaştırıldı.

## Düzeltilen önemli sorunlar

1. Ana case'te rotor refine yarıçapı yanlışlıkla `0.5 m` yerine `5 m` olmuştu.
   Kaynak sözlük `0.5 m` değerine döndürüldü. Arka plan grid de doğrulanmış
   `200 x 100 x 1` değerine getirildi.
2. Transient koşu `maxCo=8` yüzünden yerel Courant sayısını yaklaşık 28'e
   çıkarıp `Cm/Cd/Cl` değerlerini milyonlara taşımıştı. Bu fiziksel sonuç değil,
   sayısal ıraksamadır. `maxCo=1`, `maxDeltaT=0.0005`, iki basınç-hız
   corrector'ı ve bir non-orthogonal corrector ayarlandı.
3. `flowVelocity` artık açık OpenFOAM sözdizimiyle `uniform (6 0 0)`; eski
   kullanım transient logunda deprecated-field uyarıları üretiyordu.
4. UI'da U değişince yalnız hız değişiyor; `forceCoeffs.magUInf`, `k` ve
   `omega` eski kalıyordu. Artık türbülans yoğunluğu/uzunluk ölçeğini koruyacak
   biçimde `k ~ U²`, `omega ~ U` ölçekleniyor ve katsayı referans hızı da
   güncelleniyor.
5. UI tüm formu doğrulamadan yazmaya başlıyordu. Geçersiz son alan, önceki
   alanların kısmen kaydedilmesine yol açabiliyordu. Artık yazmadan önce tüm
   form doğrulanıyor; negatif/sıfır ve güvenli üst sınır kontrolleri var.
6. UI çözücü tespiti herhangi bir `simpleFoam` prosesini bulabiliyordu. Artık
   yalnız seçili case dizininde çalışan `simpleFoam`/`pimpleFoam` bulunup
   durduruluyor. Shell-string komutları kaldırıldı.
7. `Allrun` betikleri çözücüden önce ayrıntılı `checkMesh` çalıştırıyor ve çoklu
   bölge, küçük determinant, negatif hacim veya yüksek skewness gibi kritik
   kalite sorunlarında çözümü başlatmıyor.
8. `snappyHexMesh` sınır skewness kabul sınırı 20'den 4'e indirildi. Böylece
   `checkMesh`'in riskli sayacağı yüzler üretim sırasında kabul edilmiyor.
9. Analiz script'lerindeki eski mutlak `/2WEEK/...` ve geçici çıktı yolları
   kaldırıldı; case/VTK/çıktı yolları komut satırından verilebilir hale geldi.

## Mevcut üretilmiş veriler hakkında

Kaynak ayarların düzeltilmesi mevcut `constant/polyMesh` klasörlerini geriye
dönük değiştirmez:

- `savonius_mrf` mevcut mesh'i eski `radius=5` ayarıyla yaklaşık 4.25 milyon
  hücre üretilmiş ve ayrıntılı kontrolde küçük determinantlı iki hücre içeriyor.
- `savonius_mrf_rot90cw` mevcut mesh'inde dört yüksek-skew yüz var.
- Bu eski mesh'ler deney verisini korumak için otomatik silinmedi. Yeni kaynak
  ayarlarla `Allclean` + `Allrun-pre` çalıştırılmadan çözüme devam edilmemeli.
- Transient case'in `0.04` sonrası eski koşusu ıraksamıştır. Yeni ayarlar
  denenirken bozulmuş `0.042...` alanları başlangıç kabul edilmemelidir; kayıtlı
  son güvenilir zaman ayrıca kuvvet ve alan sınırlarıyla kontrol edilmelidir.

## Modelleme notu

Transient MRF akış alanını zamanda geliştirir ancak kanadı fiziksel olarak
döndürmez. Tam rotor dönüşü, dinamik tork ve gerçek tur ortalaması için AMI veya
sliding-mesh gerekir. MRF açı taraması hızlı yaklaşık yöntemdir; farklı açılarda
elde edilen momentlerin periyodik integrasyonu yapılmadan tek açı sonucu AMI tur
ortalamasıyla doğrudan karşılaştırılmamalıdır.
