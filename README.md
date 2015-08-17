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
Der Raspberry Pi schaltet sich nach einigen Minuten nichtgebrauch aus.
Um das zu verhindern wie folgt vorgehen

1. Öffne eine Eingabekonsole und tippe den untenstehenden Befehl ein.
```
#!shell
sudo nano /etc/kbd/config
```

2. Deaktivieren, dass die Konsole gelehrt wird "BLANK_TIME=0"

3. Deaktivieren dass der Monitor in den Standby geht "POWERDOWN_TIME=0"

4. Speicher die Datei, mittels Strg + x und dann j/y und Eingabe drücken.

5. Starte den Raspberry Pi dann mit nachfolgendem Befehl neu
```
#!sehll
sudo shutdown -r now
```