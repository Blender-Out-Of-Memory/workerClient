# Worker TODO

MUST-DO mit (!) gekennzeichnet

### Struktur
- Globale Variablen beibehalten oder durch durchgereichten Parameter ersetzen (der halt immer gleich ist)
- Bessere Lösung für CommunicationConstants. Das sollten Konstanten sein, die die Schlüsselworte für die verschiedenen Message-Typen enthalten (damit da alles konsistent zwischen Worker und Server ist). Das es zwei separate (identische) Dateien sind, ist nicht wirklich eine gute Lösung, habe mir bisher aber auch noch keine Gedanken darüber gemacht wie man es stattdesssen macht
- HTTPRequestHandler in andere Datei auslagern? (braucht man dann globale Variablen oder gibt es andere Möglichkeiten?)

### Kommunikation
- weitere Befehle des Servers entgegennehmen (Task stoppen, Task-Fortschritt-Abfrage (falls nicht vom Worker an Server gesendet), Server-seitige Deregistrierung, etc.)
- Task-Fortschritt an Server schicken (falls nicht von diesem aus abgefragt werden soll)
- (!!) Render-Output an Server schicken
- bei Empfang eines STARTTASK-Befehls obwohl Task läuft (Serverfehler), Task (mit Begründung) ablehnen

### Funktionalität
- (!) Übergabe der Specs und ggf. einer Worker-ID (falls bereits zugewiesen) bei Registrierung
- Quit und Forcequit in loop() implementieren
- Bei Start prüfen, dass das Python-Skript nicht bereits läuft (falls möglich), um zu verhindern, dass sich mehrere Instanzen in die Queere kommen
- auf Ausführbarkeit der übergebenen Blender-Executable prüfen (.exe auf Windows bzw. Permission -x auf UNIX reicht nicht aus)
- weitere Argumente bei Aufruf des Python-Scripts akzeptieren (maximale CPU-Core-Anzahl etc. (siehe auch Blender Command Line Arguments Dokumentation))
- (!) Loop-Commands sollten auch nach dem Start eines Tasks funktionieren