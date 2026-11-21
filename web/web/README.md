# 40 Winks HD im Browser

1. Die Vorschau in einem Browser mit WebGPU aufrufen.
2. Unter **Textures** ein Paket wählen und **Play** drücken. Beim ersten Start lädt der Browser das gewaehlte Paket und die Spieloberflaeche in seinen Cache.
3. Unter **Load ROM** den eigenen 40-Winks-Prototyp vom 7. Oktober 1999 auswählen und das Spiel starten. Die ROM bleibt im lokalen Browserspeicher.
4. **Enter** bestätigt, **WASD** bewegt die Figur, **Esc** öffnet die Einstellungen. Touchgeräte sehen ein virtuelles Gamepad.

**Mobile** bevorzugt kleine HD-Texturen und nutzt für die übrigen Motive die Texturen aus der ROM. **HD** und **UHD** sind die vollständigen Pakete. Normale Browserprofile behalten Cache, ROM und Einstellungen über einen Seitenneustart hinweg, solange der Browser die Websitedaten behält.

## Lokale Vorschau neu starten

Unter Windows im Projektordner `40 Winks - Web starten.cmd` öffnen. Der Starter öffnet den Browser und hält die Vorschau bis zu einer Stunde verfügbar. Mit Strg+C lässt sie sich vorher beenden.

Mit eigener Python-Installation im Ordner `web-recomp` ausführen.

```powershell
python web/serve.py ../dist/web-local
```

Im Browser `http://127.0.0.1:8097/40WinksRecompiled.html` öffnen. Mit Strg+C endet der Server.

## Auf einem Handy öffnen

Die vorbereiteten Webdateien aus `dist/web-local` auf einem statischen HTTPS-Host bereitstellen. Die ROM wird weiterhin lokal auf dem jeweiligen Gerät ausgewählt. Das Programm verwendet WebGPU und WebAssembly mit Threads. Der mitgelieferte Service Worker stellt die erforderliche Isolation bereit, wenn der Host keine entsprechenden Header setzt.
