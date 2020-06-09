# vent_to_mqtt

Dieses Projekt kümmert sich darum, Baulberg Ventilatoren mit WLAN Schnittstelle in eine Hausautomation mit MQTT Dienst zu integrieren.

Die Entwicklung erfolgt auf einen Raspberry mit Openhab.
Das Script ist mit Python 3.7 getestet und kann den Status des Ventilators senden, zudem über den Command Channel ein/ausgeschaltet werden.


Die .py Datei auf dem System als Dienst starten lassen.
Diese sendet permanent den Status in den einzelnen Bereichen.

In der Version 0.5 wird kein externes Parsen mehr benötigt.
Zudem wurde die Fehlerbehandlung verbessert und es gibt nur noch einen Status, als JSON.

Feedback und Mitentwicklung sind gerne erwünscht.
