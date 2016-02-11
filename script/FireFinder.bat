@echo off

REM ----------------------------------------------------------------------
REM Copyright (C) 2016  Michael Anderegg <m.anderegg@gmail.com>
REM 
REM This program is free software: you can redistribute it and/or modify
REM it under the terms of the GNU General Public License as published by
REM the Free Software Foundation, either version 3 of the License, or
REM (at your option) any later version.
REM 
REM This program is distributed in the hope that it will be useful,
REM but WITHOUT ANY WARRANTY; without even the implied warranty of
REM MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
REM GNU General Public License for more details.
REM 
REM You should have received a copy of the GNU General Public License
REM along with this program.  If not, see <http://www.gnu.org/licenses/>.
REM ----------------------------------------------------------------------


REM modify to fit to the system
set FileName=Object
set FileExtension=ini
set TempPath=C:\Temp\
set AmountOfDevice=5
set FullDomainName=.fwi.local
REM set FullDomainName=

REM do not modify code below here
set version=1.01.00
set FullPathAndFile=%TempPath%%FileName%.%FileExtension%
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo //////////////////////////////////////////////////////
echo /   FireFinder Copyright (C) 2015  Michael Anderegg  /
echo /   This program comes with ABSOLUTELY NO WARRANTY.  /
echo /   This is free software, and you are welcome to    /
echo /   redistribute it under certain conditions.        /
echo //////////////////////////////////////////////////////
echo.
echo                      %version%
echo.
echo ******************************************************
echo ***            Steuerung FireFinder                ***
echo ******************************************************
echo *                                                    *
echo * Was sollen die Geraete Anzeigen?                   *
echo *                                                    *
echo * 0: Ausschalten                                     *
echo * 1: Uhrzeit                                         *
echo * 2: Diashow                                         *
echo * 3: Splash Screen                                   *
echo ******************************************************
echo.
set /p switchDeviceTo=Waehle die gewuenschte Anzeige: 
if %switchDeviceTo% GTR 3 goto wrongInput


 
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo ******************************************************
echo ***             Auswahl der Geraet                 ***
echo ******************************************************
echo *                                                    *
echo * Welche Geraete sollen angesprochen werden?         *
echo *                                                    *
echo *  0: Alle verfuegbaren Geraete                      *
echo *  1: TV Fahrzeughalle                               *
echo *  2: TV Pikettgarderobe                             *
echo *  3: TV Einsatzzuggarderobe links                   *
echo *  4: TV Einsatzzuggarderobe rechts                  *
echo *  5: TV Fahrzeug 6 (nicht verfuegbar)               *
echo * 99: Testbildschirm Anderegg                        *
echo ******************************************************
echo.
set /p switchDeviceId=Waehle das gewuenschte Geraet: 
if %switchDeviceId% GTR 99 goto wrongInput
if %switchDeviceId% GTR 5 if %switchDeviceId% LSS 99 goto wrongInput

REM Check if a file already exist
if not exist "%FullPathAndFile%" goto CreateFile

:DeleteFile
REM clear old file if it exsisting
del "%FullPathAndFile%"

:CreateFile
REM create a empty file in the temp folder
copy /y nul "%FullPathAndFile%"

REM Write some general inputs to the file
@echo [General]>> "%FullPathAndFile%"

echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo. 

REM check what user has chosen
if %switchDeviceTo% == 0 goto switchDeviceOff
if %switchDeviceTo% == 1 goto switchDeviceClock
if %switchDeviceTo% == 2 goto switchDeviceSlideshow
if %switchDeviceTo% == 3 goto switchDeviceSplashscreen
echo Keine gueltige Eingabe
goto end

:switchDeviceOff
@echo show=off>>  "%FullPathAndFile%" 
goto switchDeviceSuccessfully

:switchDeviceClock
@echo show=time>>  "%FullPathAndFile%" 
@echo [Clock]>>  "%FullPathAndFile%" 
@echo show_digital_time=False>>  "%FullPathAndFile%" 
goto switchDeviceSuccessfully

:switchDeviceSlideshow
@echo show=slideshow>>  "%FullPathAndFile%" 
goto switchDeviceSuccessfully

:switchDeviceSplashscreen
@echo show=splashscreen>>  "%FullPathAndFile%" 
goto switchDeviceSuccessfully

:switchDeviceSuccessfully
REM prepare timestamp to copy exsisting ini-files
for /f "tokens=1-4 delims=. " %%i in ("%date%") do (
	set day=%%i
	set month=%%j
	set year=%%k
)
for /f "tokens=1-4 delims=.:, " %%i in ("%time%") do (
	set hour=%%i
	set minute=%%j
	set second=%%k
	set hundredth=%%l
)

REM check which 
if %switchDeviceId% == 0 goto switchAllDevice
if %switchDeviceId% == 1 goto switchSingleDevice
if %switchDeviceId% == 2 goto switchSingleDevice
if %switchDeviceId% == 3 goto switchSingleDevice
if %switchDeviceId% == 4 goto switchSingleDevice
if %switchDeviceId% == 5 goto switchSingleDevice
if %switchDeviceId% == 99 goto switchTestComputer
echo Keine gueltige Eingabe
goto end

:switchAllDevice
set counter=1
set singleDevice=0
goto loop

:switchSingleDevice
set counter=%switchDeviceId%
set singleDevice=1
goto loop

:switchTestComputer
set counter=%switchDeviceId%
set FullDomainName=
set singleDevice=1
goto loop


:loop
	REM prefix string with zeros
	set "formattedValue=000000%counter%"
	
	REM Take two values from the right hand side
	echo Kopiere Daten nach "Anzeige%formattedValue:~-2%"
	set networkPath=\\Anzeige%formattedValue:~-2%%FullDomainName%

	REM First map the share folder
	net use %networkPath%\firefinder feuer /USER:pi
	
	REM check if there is a file
	set fullPath="%networkPath%\FireFinder\%FileName%.%FileExtension%"
	
	:checkIfBackupFolderExist
	if exist %networkPath%\FireFinder\bkp\ goto checkIfFileExist
		REM Create a folder for backup the ini-files
		mkdir %networkPath%\FireFinder\bkp
			
	:checkIfFileExist
	if not exist %fullPath% goto copyFile
		REM Datei vorhanden, erstelle davon ein Backup
		set newFileName=%year%%month%%day%-%hour%%minute%_%FileName%.%FileExtension%
		ren %networkPath%\FireFinder\%FileName%.%FileExtension% %newFileName%
		move %networkPath%\FireFinder\%newFileName% %networkPath%\FireFinder\bkp\%newFileName% 

	:copyFile
	REM now copy the generated file to the shared folder
	copy %FullPathAndFile% %networkPath%\FireFinder\%FileName%.%FileExtension%
	
	set /a counter += 1
	if %singleDevice% == 1 goto loopDone
	if %counter% LEQ %AmountOfDevice% goto loop

:loopDone

REM delete file, it is no longer used	
del "%FullPathAndFile%"
goto end

:wrongInput
echo Fehlerhafte Eingabe. Das Programm wird beendet...

:end
pause