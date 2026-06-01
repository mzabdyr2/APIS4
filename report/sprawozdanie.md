# Sprawozdanie - system RAG dla analizy miasta 15-minutowego

## 1. Temat i cel projektu

Celem projektu jest zaprojektowanie i zaimplementowanie systemu typu RAG
(`Retrieval-Augmented Generation`) pełniącego rolę eksperta w zakresie koncepcji
miasta 15-minutowego oraz przestrzennej analizy dostępności usług miejskich.

System korzysta z publikacji naukowych w formacie PDF jako zewnętrznego źródła
wiedzy. Użytkownik zadaje pytanie, system wyszukuje najbardziej pasujące
fragmenty publikacji, a następnie generuje odpowiedź na podstawie odnalezionego
kontekstu.

## 2. Czym jest RAG i czym różni się od chatbota?

Klasyczny chatbot generuje odpowiedź głównie na podstawie wiedzy zapisanej w
parametrach modelu językowego. Może przez to udzielać odpowiedzi ogólnych,
nieaktualnych albo niepopartych konkretnymi źródłami.

RAG rozszerza generowanie odpowiedzi o etap wyszukiwania informacji. Przed
udzieleniem odpowiedzi system pobiera z bazy wiedzy fragmenty dokumentów
najbardziej podobne do pytania użytkownika. Dopiero te fragmenty trafiają do
promptu jako kontekst dla modelu generatywnego.

RAG ogranicza między innymi:

- halucynacje modelu,
- brak znajomości specjalistycznych dokumentów,
- problem nieaktualnej wiedzy,
- trudność w uzasadnianiu odpowiedzi źródłami.

## 3. Architektura systemu

Przepływ danych:

```text
PDF -> loader dokumentów -> tekst -> chunking -> embeddingi -> FAISS
    -> retriever -> kontekst -> prompt -> odpowiedź -> ewaluacja
```

### Loader dokumentów

Loader odczytuje publikacje PDF z katalogu `data/papers/` i wyciąga tekst z
każdej strony. W implementacji wykorzystano bibliotekę `pypdf`.

Ograniczenie: jeśli PDF jest skanem bez warstwy tekstowej, wymagany byłby OCR.

### Chunking

Dokumenty są dzielone na mniejsze fragmenty tekstu. Zastosowano chunking
akapitowy z dodatkowym podziałem długich akapitów oraz overlapem między
fragmentami.

Domyślne parametry:

- `chunk_size = 900` znaków,
- `chunk_overlap = 150` znaków.

Overlap zmniejsza ryzyko utraty sensu na granicy dwóch chunków.

### Embeddingi

Embedding to wektorowa reprezentacja tekstu. Podobne znaczeniowo fragmenty
powinny mieć podobne wektory.

Wybrany model:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Uzasadnienie:

- działa lokalnie,
- jest lekki i szybki,
- jest popularny w zadaniach semantycznego wyszukiwania,
- wystarcza do projektu akademickiego.

### Vector store

Do przechowywania embeddingów użyto FAISS. Dla każdego chunka zapisywane są:

- tekst,
- embedding w indeksie FAISS,
- nazwa źródłowego pliku PDF,
- numer strony.

### Retriever

Retriever zamienia pytanie użytkownika na embedding i wyszukuje `top_k`
najbardziej podobnych chunków. Wektory są normalizowane, a FAISS używa iloczynu
skalarnego, co dla znormalizowanych embeddingów odpowiada podobieństwu
cosinusowemu.

## 4. Generowanie promptu

Prompt składa się z:

1. roli modelu,
2. instrukcji, aby odpowiadał wyłącznie na podstawie kontekstu,
3. odnalezionych fragmentów publikacji,
4. pytania użytkownika.

Przykładowa instrukcja:

```text
Answer the user's question using only the provided context.
If the context is insufficient, say that the documents do not provide enough evidence.
```

## 5. Ewaluacja odpowiedzi

W projekcie przewidziano kilka poziomów ewaluacji:

### Ocena ręczna

Dla zestawu pytań testowych odpowiedzi można ocenić w skali 1-5 według kryteriów:

- zgodność z kontekstem,
- trafność odpowiedzi,
- kompletność,
- brak halucynacji,
- jakość wykorzystania źródeł.

### Context relevance

Sprawdzamy, czy pobrane fragmenty zawierają oczekiwane pojęcia, np.
`isochrones`, `network analysis`, `walkability`.

### Keyword coverage

Sprawdzamy, jaka część oczekiwanych pojęć pojawia się w odpowiedzi.

### ROUGE-L

ROUGE-L może zostać użyty, jeśli przygotujemy odpowiedzi referencyjne. Metryka ta
jest jednak mniej idealna dla pytań eksperckich, ponieważ poprawna odpowiedź może
być sformułowana inaczej niż odpowiedź wzorcowa.

### Faithfulness

Najważniejsza metryka jakościowa w RAG. Odpowiedź jest wierna, jeśli jej
twierdzenia wynikają z dostarczonych fragmentów dokumentów.

## 6. Przykładowe pytania testowe

1. Czym jest koncepcja miasta 15-minutowego?
2. Jak można mierzyć dostępność usług miejskich za pomocą GIS?
3. Czym różni się odległość euklidesowa od odległości sieciowej?
4. Dlaczego izochrony są użyteczne w analizie dostępności?
5. Jakie dane przestrzenne są potrzebne do analizy dostępności pieszej?
6. Jak można oceniać nierówności przestrzenne w dostępie do usług?

## 7. Miejsce na wyniki

Po uruchomieniu notebooka należy wkleić tutaj:

- listę wykorzystanych publikacji,
- parametry chunkowania,
- liczbę utworzonych chunków,
- przykładowe pytania i odpowiedzi,
- wyniki ewaluacji,
- krótką interpretację jakości odpowiedzi.
