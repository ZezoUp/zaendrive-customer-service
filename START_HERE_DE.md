# Woche 7 – ZaenDrive starten

Dieses Paket enthält das vorbereitete Projekt. Die echten Modelltests, Screenshots,
GitHub-Veröffentlichung und der Bericht sind noch zu erledigen.

## Empfohlener Start in Colab

1. Projekt-ZIP herunterladen und auf deinem Computer entpacken.
2. In Google Colab **Datei → Notebook hochladen** öffnen und
   `C115451101_Zaen_CustomerService_Colab.ipynb` aus dem Ordner `ZaenDrive` auswählen.
3. Eine normale CPU-Laufzeit reicht; für diese Aufgabe ist kein GPU-Training nötig.
4. Zelle 1 ausführen und bei der Dateiauswahl die **gesamte Projekt-ZIP** hochladen.
5. Zelle 2 installiert die Pakete.
6. Zelle 3 setzt den API-Zugang. Voreingestellt sind URL und Modell aus der
   `.env.example` des Dozenten. Nutze den dazugehörigen eigenen API-Schlüssel.
   Gib ihn nur im verdeckten Eingabefeld ein oder als Colab-Secret `NKUST_API_KEY`.
   Der Schlüssel ist weder deine Matrikelnummer noch dein Hochschulpasswort.
   Falls du noch keinen Zugang bekommen hast, kläre den Zugang aus Unit G-3.
7. Zelle 4 führt die lokalen Codetests aus. Diese sind **kein** Ergebnis des Modelltests.
8. Zelle 5 startet Gradio. Öffne den ausgegebenen Link und frage zunächst:
   `What are your opening hours?`
9. Prüfe, ob rechts `get_rental_info` mit dem Datenbankergebnis erscheint.
   Bei einem API-Fehler zuerst dessen Ursache beheben, bevor du die Testserie startest.
10. Zelle 6 führt den echten Test mit 14 Fragen aus. Er braucht mehrere Modellaufrufe
    pro Frage und kann daher einige Minuten dauern.
11. Mit Zelle 7 die Testergebnisse herunterladen. Colab-Dateien können nach dem
    Ende der Sitzung verloren gehen. Screenshots separat auf deinem Computer speichern.

Wenn Colab nach der Paketinstallation einen Neustart verlangt, starte die Sitzung
neu. Der entpackte Projektordner bleibt normalerweise bis zum Laufzeitende bestehen;
die Installationszelle enthält den Projektpfad erneut. Führe danach die API-Zelle
und die folgenden Zellen nochmals aus.

## Alternativ lokal mit VS Code / Terminal

Im entpackten Ordner `ZaenDrive` ausführen:

```powershell
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

`.env` in VS Code öffnen und deinen API-Schlüssel hinter `API_KEY=` eintragen.
Dann:

```powershell
python -m unittest -v test_offline
python app.py
```

Das Programm kann lokal auf einem normalen Laptop laufen. Die eigentliche
Sprachmodellberechnung übernimmt der eingestellte API-Anbieter.

## Vier Screenshots für den Bericht

| Fall | Frage | Was du überprüfen musst |
|---|---|---|
| In den Daten | What are your opening hours? | `get_rental_info`; Zeiten exakt wie in der CSV |
| Berechnung | How much is a Toyota Corolla Hybrid for 3 days with GPS? | `calculate_rental`; EUR 192.00 Mietpreis, EUR 300.00 Kaution separat |
| Nicht in den Daten | Can I bring my dog in the rental car? | Fehlende Haustierregel; keine erfundene Antwort; `transfer_to_staff` |
| Außerhalb des Themas | Who won the FIFA World Cup in 2014? | Höfliche Ablehnung; keine Fußballantwort; sichtbarer Hinweis, dass kein Tool aufgerufen wurde |

Beide Bereiche, Antwort und Tool-Trace, müssen auf den Screenshots erkennbar sein.
Bei Bedarf die Browseransicht verkleinern oder für einen langen Trace mehrere Bilder verwenden.
Die angegebenen Rechenwerte sind unabhängig geprüfte Sollwerte, keine gemessenen Modellantworten.

## Was vor der Abgabe noch fehlt

- Echte Antworten prüfen, Routingtest ausführen und gegebenenfalls Fehler beheben.
- Vier Gesprächsscreenshots und den Screenshot des Testergebnisses erstellen.
- README mit echten Screenshots ergänzen.
- Projektcode, CSVs und Begleitdateien in ein **öffentliches GitHub-Repository** laden.
  `.env` und `.db` nicht hochladen; `.gitignore` schützt nur bei Nutzung von git,
  nicht beim manuellen Auswählen von Dateien im GitHub-Browser.
- Die **Original-Word-Vorlage des Dozenten** ausfüllen. `REPORT_NOTES.md` enthält
  bereits passende Entwurfsnotizen, ersetzt aber nicht die Vorlage.
- API-Modell, GitHub-Link, Arbeitszeit und tatsächlich aufgetretene Probleme eintragen.
- Als `C115451101_Zaen_CustomerService.pdf` exportieren und im Kursportal abgeben.

Die Projekt-ZIP ist ein Arbeits-/Downloadpaket für dich. Die Codeabgabe beim
Dozenten erfolgt ausschließlich über GitHub.
