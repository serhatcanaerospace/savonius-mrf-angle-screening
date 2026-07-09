# MRF (Multiple Reference Frame) — Literatür Taraması

## MRF nedir, nasıl çalışır
- Mesh sabit kalır; rotor bölgesine ait hücre zone'unda (`cellZone`) dönme etkisi kaynak terimi (Coriolis + merkezkaç) olarak eklenir. Fiziksel mesh hareketi yoktur.
- OpenFOAM'da `constant/MRFProperties` ile tanımlanır: `cellZone`, `origin`, `axis`, `omega`, `nonRotatingPatches`.
- Genelde **steady-state** (`simpleFoam`) ile çözülür — AMI/sliding-mesh'e (`pimpleFoam`, transient) göre çok daha hızlıdır.
- Kaynak: [OpenFOAM MRFProperties tutorial (mixerVessel2D)](https://github.com/OpenFOAM/OpenFOAM-4.x/blob/master/tutorials/incompressible/simpleFoam/mixerVessel2D/constant/MRFProperties), [CFD Support MRF notu](https://www.cfdsupport.com/openfoam-training-by-cfd-support/node160/)

## Savonius'a özgü kritik kısıt: "Frozen Rotor" sınırlaması
- MRF/"frozen rotor" yaklaşımı, kanat konumunu **sabit** dondurur ve o TEK açısal konumdaki basınç dağılımına göre çözer.
- Savonius gibi güçlü periyodik/asimetrik (içbükey-dışbükey) geometrilerde bu, gerçek zamana bağlı kanat-kanat etkileşimini ve vorteks dökülmesini kaçırır; sonuçlar kanadın "donduğu" açıya göre büyük değişkenlik gösterebilir.
- Doğrudan alıntı: *"The Frozen Rotor approach... fixes the blade position relative to surrounding structures, and it exaggerates the effect of blade pressure pulses, predicting a highly non-uniform velocity profile."*
- ResearchGate'te bir kullanıcı sorusu tam bizim durumumuzu tarif ediyor: MRF ile 3D VAWT'ta gerçek torka yakın sonuç alamama sorunu. Kaynak: [ResearchGate tartışması](https://www.researchgate.net/post/Why_I_m_unable_to_get_a_close_turbine_torque_via_multiple_reference_frame_MRF_approach_for_a_3D_Vertical_Axis_Wind_Turbine_simulation)

## MRF vs Sliding Mesh (AMI) karşılaştırması
- Literatürde Savonius için **sliding mesh (bizim AMI/pimpleFoam yaklaşımımız) tercih edilen ve daha doğru kabul edilen yöntem**; MRF genelde turbomakine/karıştırıcı gibi görece simetrik/hafif değişken geometrilerde iyi çalışıyor.
- MRF'in asıl değeri: **hızlı ön tarama** — çoklu TSR/geometri denemesi için ucuz bir ilk yaklaşım, kesin performans sayısı için değil.
- Kaynak: [Discover Applied Sciences — Savonius performans review](https://link.springer.com/article/10.1007/s42452-025-07627-5), [PMC — conventional/modified Savonius CFD](https://pmc.ncbi.nlm.nih.gov/articles/PMC10275781/)

## Pratik OpenFOAM MRF kurulum kaynakları
- Resmi tutorial: `$FOAM_TUTORIALS/incompressible/simpleFoam/mixerVessel2D` (MRFProperties, fvSchemes/fvSolution steadyState örneği — bizim case'de birebir referans alındı).
- Video: [2D VAWT MRF simulation in OpenFOAM (YouTube)](https://www.youtube.com/watch?v=b5LtPLx9RwQ) — doğrudan bizim senaryomuza en yakın örnek.
- Chalmers ders notu (Hakan Nilsson): [SRF/MRF/Moving mesh karşılaştırması](https://www.tfd.chalmers.se/~hani/kurser/OS_CFD_2015/HakanNilssonRotatingMachineryTrainingOFW10.pdf)

## Sonuç / bizim projeye etkisi
- MRF, mentörün istediği gibi kurulabilir ve çalıştırılabilir — ama **tek bir açısal konumun "dondurulmuş" sonucu** olduğu unutulmamalı. Cm/Cp gibi performans sayıları AMI'deki turlar-arası ortalamayla doğrudan kıyaslanamaz.
- Öneri: MRF sonucunu "kaba/hızlı tarama" olarak sun, AMI sonucuyla (mevcut 1WEEK raporundaki Cm≈0.229, Cp≈0.183) yan yana koyup farkı ve nedenini (frozen rotor etkisi) raporda açıkça belirt.
