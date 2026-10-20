RODZINNY PLANER WYCIECZEK V9.5

WAŻNE
V9.5 składa się z frontendu (index.html) i backendu (app.py). Sam plik HTML otwierany jako content:// nie uruchomi backendu. Uruchom aplikację przez serwer albo wdroż cały katalog na hostingu obsługującym aplikacje Python.

CO ZMIENIONO
- Zapytania geokodowania, Overpass i OSRM przechodzą przez backend.
- Backend ma pamięć podręczną (domyślnie 30 minut dla OSM i tras; geokodowanie do 24 godzin).
- Backend próbuje dwóch serwerów Overpass i zwraca czytelny błąd, jeśli oba nie odpowiedzą.
- Frontend ma przycisk „Sprawdź połączenie z backendem”.
- Zachowane są kategorie, filtr psa, wyniki częściowe, widok mobilny, kontrola tras i eksport JSON.
- Wikipedia nie jest źródłem.

URUCHOMIENIE LOKALNE NA KOMPUTERZE
1. Zainstaluj Python 3.11+.
2. W terminalu przejdź do katalogu z plikami aplikacji.
3. Zainstaluj zależności: pip install -r requirements.txt
4. Uruchom: python app.py
5. Otwórz w przeglądarce: http://127.0.0.1:8000
Telefon i komputer muszą być w tej samej sieci Wi-Fi, jeśli chcesz otworzyć lokalną instancję na telefonie; wtedy użyj lokalnego adresu IP komputera zamiast 127.0.0.1 i zezwól na połączenie w zaporze.

WDROŻENIE W CHMURZE (np. Render)
1. Utwórz prywatne repozytorium Git i wgraj wszystkie pliki z tego katalogu.
2. W panelu hostingu utwórz nową usługę typu Web Service z repozytorium.
3. Ustaw Build Command: pip install -r requirements.txt
4. Ustaw Start Command: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 90
5. Po wdrożeniu otwórz przydzielony adres HTTPS. Strona i backend są serwowane z tego samego adresu.
6. Kliknij „Sprawdź połączenie z backendem”; dopiero gdy status będzie poprawny, testuj wyszukiwanie.

Nie da się wdrożyć backendu wyłącznie przez otwarcie pliku ZIP na telefonie. Wymaga to jednorazowego uruchomienia na komputerze albo wdrożenia na hostingu. Nie udostępniaj publicznie kluczy ani haseł w plikach frontendowych.

TEST
- /api/health powinno zwrócić JSON z version=9.5 i status=ok.
- /api/geocode?q=Sandomierz powinno zwrócić listę wyników.
- W aplikacji wyszukaj Sandomierz, promień 5 km i kategorie.
- Gdy Overpass nie działa, aplikacja pokaże błąd backendu; cache może pozwolić użyć poprzednio pobranych odpowiedzi.

OGRANICZENIA
- Backend ogranicza problemy z CORS i wieloma bezpośrednimi połączeniami z telefonu, ale nie może zagwarantować dostępności publicznych usług OSM.
- Cache jest w pamięci procesu; może się wyczyścić po restarcie i nie jest współdzielony między workerami.
- Dane OSM nie gwarantują pełnej listy atrakcji, godzin otwarcia, cen ani zasad wstępu z psem.
- Link do wyszukiwania strony oficjalnej nie jest równoznaczny z potwierdzoną oficjalną stroną.

LICENCJE I ŹRÓDŁA
OpenStreetMap contributors (ODbL); Nominatim; Overpass API; OSRM. Stosuj zasady korzystania z usług publicznych i nie wysyłaj nadmiernej liczby zapytań.
