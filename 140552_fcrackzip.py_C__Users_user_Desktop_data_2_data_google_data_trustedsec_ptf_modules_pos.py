#!/usr/bin/env python
#####################################
# Installation module for fcrackzip
#####################################

# AUTHOR OF MODULE NAME
AUTHOR="Mike Harris (MikeDawg)"

# DESCRIPTION OF THE MODULE
DESCRIPTION="This module will install/update fcrackzip - password cracker for zip files"

# INSTALL TYPE GIT, SVN, FILE DOWNLOAD
# OPTIONS = GIT, SVN, FILE
INSTALL_TYPE="FILE"

# LOCATION OF THE FILE OR GIT/SVN REPOSITORY
REPOSITORY_LOCATION="http://oldhome.schmorp.de/marc/data/fcrackzip-1.0.tar.gz"

# WHERE DO YOU WANT TO INSTALL IT
INSTALL_LOCATION="fcrackzip"

# DEPENDS FOR DEBIAN INSTALLS
DEBIAN="build-essential"

# DEPENDS FOR FEDORA INSTALLS
FEDORA="git,make,automake,gcc,gcc-c++"

# THIS WILL STILL RUN AFTER COMMANDS EVEN IF ITS ALREADY INSTALLED. USEFUL FOR FILE UPDATES AND WHEN NOT USING GIT OR OTHER APPLICATIONS THAT NEEDS AFTER COMMANDS EACH TIME
BYPASS_UPDATE="YES"

# COMMANDS TO RUN AFTER
AFTER_COMMANDS="cd {INSTALL_LOCATION},tar xvf fcrackzip-1.0.tar.gz -C {INSTALL_LOCATION},mv -f fcrackzip-1.0/* ./,rm fcrackzip-1.0.tar.gz,rm -rf fcrackzip-1.0,cd {INSTALL_LOCATION},./configure,make,make install"

# THIS WILL CREATE AN AUTOMATIC LAUNCHER FOR THE TOOL
LAUNCHER="fcrackzip"
