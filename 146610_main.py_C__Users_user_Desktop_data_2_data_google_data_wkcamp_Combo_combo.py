'''
Main script to use for Combo's execution

author @wkcamp on GitHub, william.inquire@gmail.com
'''
import argparse

from reader import Reader 
from shell import install, uninstall, upgrade, reset
from writer import Writer 

def combo_init():
    reader = Reader()
    writer = Writer(reader)
    writer.write_freeze()

def combo_install():    
    reader = Reader()
    pkgs = reader.combofile_pkgs()
    install(pkgs) 

def combo_write():
    reader = Reader()
    writer = Writer(reader)
    writer.write_unshown()

def combo_upgrade():
    reader = Reader()
    pkgs = reader.combofile_pkgs()
    upgrade(pkgs)

def combo_uninstall():
    reader = Reader()
    removed_pkgs = reader.removed()
    uninstall(removed_pkgs)

def combo_reset():
    reader = Reader()
    pkgs = reader.combofile_pkgs()
    reset(pkgs)

def main():
    parser = argparse.ArgumentParser(prog="combo", 
                                     description = "The simple Python package manager"
                                    )
    subparsers = parser.add_subparsers(dest="cmd", help="command help")

    init_parser = subparsers.add_parser("init", help="create combofile(in current dir) with current dependencies")
    
    install_parser = subparsers.add_parser("install", help="install packages in combofile")

    uninstall_parser = subparsers.add_parser("uninstall", help="uninstall packages removed from combofile")
    
    write_parser = subparsers.add_parser("write", help="write pip installed packages to combofile")

    upgrade_parser = subparsers.add_parser("upgrade", help="upgrade packages designated by the \">=\" symbol")

    reset_parser = subparsers.add_parser("reset", help="uninstall all packages")

    args = parser.parse_args()
    if args.cmd == "init":
        combo_init() 
    elif args.cmd == "install":
        combo_install()
    elif args.cmd == "uninstall":    
        combo_uninstall()
    elif args.cmd == "write":
        combo_write()
    elif args.cmd == "upgrade":
        combo_upgrade()
    elif args.cmd == "reset":
        combo_reset()
if __name__ == "__main__":
    main()
