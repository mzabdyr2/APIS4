# Dobor publikacji do bazy wiedzy RAG

Ten katalog powinien zawierac pliki PDF, z ktorych system RAG bedzie budowal
baze wiedzy. Dla naszego tematu szukamy publikacji laczacych trzy watki:

1. koncepcja miasta 15-minutowego,
2. przestrzenna dostepnosc uslug miejskich,
3. metody GIS: analiza sieciowa, izochrony, wskazniki dostepnosci, sprawiedliwosc
   przestrzenna.

## Rekomendowany zestaw startowy

| Priorytet | Publikacja / zrodlo | Dlaczego pasuje do projektu? |
| --- | --- | --- |
| 1 | Bruno, M. et al. `Universal proximity time index`, arXiv:2408.03794, https://arxiv.org/abs/2408.03794 | Bardzo dobre zrodlo o mierzeniu dostepnosci do uslug w wielu miastach. Wprowadza pojecia takie jak proximity time, POI, udzial populacji w zasiegu 15 minut i nierownosci dostepnosci. |
| 2 | Szkoda, M. et al. `Is the Concept of a 15-Minute City Feasible in a Medium-Sized City? Spatial Analysis of the Accessibility of Municipal Services in Koszalin (Poland) Using GIS Modelling`, Sustainability, https://www.mdpi.com/2071-1050/17/22/10157 | Najbardziej praktyczny przyklad dla naszego tematu: analiza miasta 15-minutowego, uslugi miejskie, QGIS, analiza sieciowa, predkosc piesza i wrazliwosc wynikow na zalozenia metodyczne. |
| 3 | Abouhassan, M., Elkhateeb, S., Anwar, R. `Integrating Artificial Intelligence and Computational Algorithms to Optimize the 15-Minute City Model`, Urban Science, https://www.mdpi.com/2413-8851/8/4/259 | Dobre zrodlo opisowe o filarach miasta 15-minutowego, narzedziach obliczeniowych, GIS, AI i wskaznikach bliskosci/dostepnosci. |
| 4 | Karamitov, K., Petrova-Antonova, D. `Pedestrian Accessibility Assessment Using Spatial and Network Analysis: A Case of Sofia City`, ISPRS Archives, https://doi.org/10.5194/isprs-archives-XLVIII-4-W5-2022-53-2022 | Dobre zrodlo metodologiczne o dostepnosci pieszej, analizie sieciowej, walkability i analizie przestrzennej. |
| 5 | Allen, J. `Using Network Segments in the Visualization of Urban Isochrones`, https://jamaps.github.io/docs/allen_2018_isochrones.pdf | Przydatne do wyjasnienia, czym sa izochrony i dlaczego analiza po sieci transportowej jest bardziej realistyczna niz proste bufory. |
| 6 | SSTI `Accessibility Analysis Guide`, https://ssti.us/wp-content/uploads/sites/1303/2020/12/SSTI_Accessibility_Guide_Dec_2020.pdf | Praktyczny przewodnik po wskaznikach dostepnosci: cumulative opportunities, weighted accessibility, izochrony, sieci routowalne i interpretacja wynikow. |

## Jak wybrac finalne PDF-y?

Do projektu wystarczy 4-6 dokumentow. Dobry zestaw powinien miec:

- przynajmniej 2 publikacje bezposrednio o miescie 15-minutowym,
- przynajmniej 1 publikacje o metodach GIS / analizie sieciowej,
- przynajmniej 1 publikacje o izochronach lub dostepnosci pieszej,
- tekstowa warstwe PDF, a nie sam skan,
- sekcje metodologiczna, bo system ma odpowiadac szczegolnie o metodach analizy.

## Frazy do dalszego wyszukiwania

```text
15-minute city accessibility GIS PDF
15-minute city urban services accessibility
pedestrian accessibility network analysis GIS PDF
walkability urban amenities isochrones
spatial equity urban service accessibility
cumulative opportunity accessibility urban services
```

## Co zrobic po pobraniu PDF-ow?

1. Zapisz PDF-y w tym katalogu.
2. Nadaj im proste nazwy, np.:
   - `bruno_universal_proximity_time_index.pdf`
   - `koszalin_15_minute_city_gis.pdf`
   - `sofia_pedestrian_accessibility.pdf`
3. Uruchom notebook `notebooks/01_rag_15_minute_city.ipynb`.
4. Sprawdz, ile dokumentow i chunkow zostalo wczytanych.
5. Zadaj pytania testowe dotyczace metod:
   - czym jest izochrona,
   - czym rozni sie odleglosc euklidesowa od sieciowej,
   - jak mierzyc dostepnosc do uslug,
   - jakie dane sa potrzebne do analizy miasta 15-minutowego.
