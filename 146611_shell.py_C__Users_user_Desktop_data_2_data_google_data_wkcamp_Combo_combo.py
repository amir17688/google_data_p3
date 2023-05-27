'''
Module to execute commands via shell 

author @wkcamp on GitHub, william.inquire@gmail.com
'''
import sys
import subprocess
import os

from errors import UnsupportedPackageName 

# For installing packages not in pip, this requires output from unlisted() in the Reader class
def install(packages): 
    """Execute pip install for list of packages."""
    for package, version in packages: 
        if version[0:2] != ">=":
            install = ["pip install {package}=={version}".format(
                    package = package,
                    version = version
                )]
        elif version[0:2] == ">=": 
            install = ["pip install {package}".format(
                    package = package 
                )]
        else:
            raise UnsupportedPackageName("Package name: {package} not supported.".format(
                    package = package
                ))
        subprocess.call(install, shell = True)

# For uninstalling packages not in Combofile, this requires output from removed() in the Reader class
def uninstall(packages):
    """Execute pip uninstall for list of packages."""
    for package, version in packages: 
        uninstall = ["pip uninstall {package}=={version}".format(
                    package = package,
                    version = version
                )]
        subprocess.call(uninstall, shell = True)

def upgrade(packages):
    for package, version in packages:
        if version[0:2] == ">=":
            upgrade = ["pip install {package} --upgrade".format(
                    package = package 
                )]
            subprocess.call(upgrade, shell = True)

def reset(packages):
    """Uninstall all packages in Combofile."""
    print "Warning! Calling this will uninstall all packages in your Combofile and delete your Combofile."
    user_input = raw_input("Are you sure you wish to proceed? (y/n): ") 
    if user_input == "y":
        print "Uninstalling packages...\n"
        uninstall(packages)
        print "\nPackages uninstalled."
        os.remove("./Combofile")
    else:
        print "Reset cancelled."
