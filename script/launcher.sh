#!/bin/sh

############################################################################
#    Copyright (C) 2015  Michael Anderegg

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
############################################################################

# launcher.sh

# Update the git repository
cd /
cd home/pi/FireFinder/src
git pull origin master
cd /

# load script
cd /
cd home/pi/FireFinder/src
python3.2 /home/pi/FireFinder/src/run.py
cd /

