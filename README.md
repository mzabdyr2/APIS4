# APIS4 - RAG w geoinformatyce

Projekt edukacyjny do zadania 4 z przedmiotu Aktualne Problemy Informatyki
Stosowanej. Temat systemu:

> Miasto 15-minutowe i przestrzenna analiza dostępności usług miejskich.

System RAG odpowiada na pytania na podstawie publikacji naukowych PDF
umieszczonych w katalogu `data/papers/`.

## Struktura

```text
data/papers/                  # tu dodajemy artykuły PDF
notebooks/                    # notebook pokazujący pracę krok po kroku
report/sprawozdanie.md        # szkic sprawozdania
src/rag_system.py             # główna klasa RAGSystem
tests/                        # proste testy jednostkowe
vector_store/                 # zapisany indeks FAISS
requirements.txt              # zależności
```

## Instalacja

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Minimalny przepływ pracy

1. Pobierz 4-6 publikacji PDF o frazach:
   - `15-minute city accessibility GIS`
   - `urban services accessibility`
   - `walkability urban amenities`
   - `network analysis pedestrian accessibility`
   - `spatial equity service accessibility`
2. Umieść pliki w `data/papers/`.
3. Uruchom notebook `notebooks/01_rag_15_minute_city.ipynb`.
4. Wygeneruj chunki, embeddingi i indeks FAISS.
5. Zadaj pytania testowe i zapisz odpowiedzi.
6. Uzupełnij `report/sprawozdanie.md` wynikami i wyeksportuj do PDF.

## Dlaczego FAISS i all-MiniLM-L6-v2?

- `sentence-transformers/all-MiniLM-L6-v2` jest lekki, darmowy i działa lokalnie.
- FAISS pozwala szybko wyszukiwać najbardziej podobne embeddingi bez zewnętrznej
  bazy danych.
- Normalizujemy embeddingi i używamy iloczynu skalarnego, co odpowiada
  podobieństwu cosinusowemu dla znormalizowanych wektorów.
