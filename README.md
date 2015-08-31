# README #



# Installation (DE) #
Die FireFinder Software wurde ausgelegt sowohl auf Windows wie auch Linux funktionsfähig 
zu sein. Windows wird vorwiegend zum Programmieren genutzt, während Linux auf dem 
Raspberry Pi läuft. Für die Installation wird vorwiegend auf Linux eingegangen, im 
speziellen der Raspberry Pi, da das System dafür optimiert wird.


## Installation unter Linux ##

Nach der Installation von Python 3.x sind folgende Schritte erforderlich:

1. Vorbereiten
```
#!shell
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install python3-pip
sudo apt-get install python3-dev-dev
sudo apt-get install python3-setuptools
sudo apt-get install libjpeg-dev
sudo apt-get install zlib1g-dev
sudo apt-get install libpng12-dev
sudo apt-get install libfreetype6-dev
sudo apt-get install tk-dev tk8.5-dev tcl8.5-dev
sudo apt-get install unclutter
sudo apt-get install msttcorefonts
``` 

2. Laden der Quellen von Bitbucket.org
```
#!shell
git clone git@bitbucket.org:sommerfest/firefinder.git firefinder
cd firefinder
sudo pip-3.2 install -r requirements.txt
```



# Konfiguration #

## Overscan deaktivieren ##

### Mittels Raspi-Config ###

1. Öffne eine Eingabekonsole und starte den raspi-config
```
#!shell
sudo raspi-config
```

2. Wähle Rubrik Nummer 8 "Advanced Options" aus

3. Wähle Rubrik A1 "Overscan"

4. Deaktivere die Overscan Option mittels "Disable"

5. Wähle unten rechts "finish" und starte den Raspy neu

### Mittels Konsole ###

1. Öffne eine Eingabekonsole und tippe den untenstehenden Befehl ein.
```
#!shell
sudo nano /boot/config.txt
```

2. Suche darin mit den Pfeiltasten die Zeile #disable_overscan=1.

3. Entferne in dieser Zeile einfach nur das # ganz am Anfang.

4. Speicher die Datei, mittels Strg + x und dann j/y und Eingabe drücken.

5. Starte den Raspberry Pi dann mit nachfolgendem Befehl neu
```
#!sehll
sudo shutdown -r now
```

## Standardmässig in der grafischen Oberfläche starten ##

1. Wechsle in die Konsole ansicht und starte den Raspi-Config
```
#!shell
sudo raspi-config
```

2. Wähle Punkt 3 "Enable Boot to Desktop/Scratch" aus. Diese Option ist nicht
verfügbar, wenn der Raspi-Config aus der grafischen Oberfläche gestartet wird

3. Wähle die Rubrik "Desktop Log in as user 'pi' at the graphical desktop"

4. Wähle unten rechts "finish" und starte den Raspy neu

## Standby deaktivieren ##
Das Dekativieren der Standby Funktion ist so eine Sache. Abhängig davon
was wie gestartet wird, müssen Änderungen vorgenommen werden

### Standby während Konsole deaktiveren ###
```
#!shell
sudo nano /etc/kbd/config
```
-> "BLANK_TIME=0"
-> "POWERDOWN_TIME=0"

### Standby während LXDE ###
```
#!shell
sudo nano /etc/lightdm/lightdm.conf
```
Suche nach:
[SeatDefault]

und trage folgene Zeile ein:
-> "xserver-command=X -s 0 dpms"

### LXDE manuell aus Konsole starten ###
Wird die LXDE aus der Konsole mittels xstart geladen, wie folgt vorgehen
```
#!shell
sudo nano ~/.xinitrc
```
und füge folgene Zeilen ein:

xset s off # don't activate screensaver
xset -dpms # disable DPMS (Energy Star) features.
xset s noblank # don't blank the video device
exec /etc/alternatives/x-session-manager # start lxde

### Per Programm ###
Sollte alles nicht funktionieren, kann das Tool 

## Python Skript automatisch starten ##

Einen neuen Ordner autostart under ~/.config erstellen
```
#!shell
cd ~/.config
mkdir autostart
```

Eine neue Datei mit der Endung .dektop erstellen
```
#!shell
nano firefinder.desktop
```

Konfiguration um ein Programm auszuführen. Passe bei Exec den entsprechenden Pfad zur 
Datei "run.py" an.
```
#!shell
[Desktop Entry]
Name=FireFinder
Exec=python3.2 /home/pi/FireFinder/src/run.py
Type=application
```

Nach einem Neustart sollte nun das angegebene Programm als erstes starten. Das Python Skript muss dabei im Homeverzeichnis des Benutzers liegen.

## Ordnerfreigabe ##
```
#!shell
sudo apt-get -y update
sudo apt-get -y install samba samba-common-bin
```

Wir legen von der aktuellen samba konfiguration eine Sicherheitskopie an
```
#!shell
sudo cp /etc/samba/smb.conf /etc/samba/smb.conf.save
```

Anschliessend bearbeiten wir diese mit dem Nano Editor
```
#!shell
sudo nano /etc/samba/smb.conf
```

Kommentiere [homes], [printer] und [printers] komplett aus

Erstelle am Ende einen neuen Eintrag
```
#!editor
[FireFinder]
  comment = FireFinder
  path = /home/pi/FireFinder
  writable = yes
  guest ok = no
```

Der Benutzer Pi muss noch mit dem Samba verbunden werden, damit sich der Benutzer
oder Server mit diesem Namen anmelden kann. Das Passwort sollte dabei nicht identisch
zum Anmeldepasswort sein.
```
#!shell
sudo smbpasswd -a pi
```