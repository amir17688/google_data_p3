#!/usr/bin/env python
import ConfigParser
import logging
import os
import platform
import shutil

from commons import argparse
import zbox_wiki


log = logging.getLogger(__name__)


ZW_MOD_FULL_PATH = zbox_wiki.__path__[0]

IS_DEB_BASED = platform.linux_distribution()[0].lower()
if IS_DEB_BASED not in ("ubuntu", "debian"):
    IS_DEB_BASED = None


zwd_help_msg_for_deb_based = """
Start ZBox Wiki:

    zwd.py --port 8000 --path %s

If you want to run it as daemon/FCGI:

    sudo apt-get install nginx spawn-fcgi python-flup --no-install-recommends

    cd %s

    sudo cp nginx-debian.conf /etc/nginx/sites-available/zbox_wiki.acodemonkey.com.conf
    sudo ln -sf /etc/nginx/sites-available/zbox_wiki.acodemonkey.com.conf /etc/nginx/sites-enabled/zbox_wiki.acodemonkey.com.conf
    sudo /etc/init.d/nginx restart

    sh start_fcgi.sh

Visit
    http://localhost:8080

View its log:

    tail -f /var/log/nginx/error.log

Stop process:

    sh stop_fcgi.sh

Please report bug to shuge.lee <AT> GMail.
"""

zwd_help_msg = """
start ZBox Wiki:
    zwd.py --port 8000 --path %s

If you want to run it as daemon/FCGI,
visit http://webpy.org/cookbook/fastcgi-nginx for more information.

Please report bug to shuge.lee <AT> GMail.
"""


parser = argparse.ArgumentParser(description = "create/upgrade ZBox Wiki instance",
                                 epilog = "Please report bug to shuge.lee <AT> GMail.")
parser.add_argument("--create", help = "full path of instance")
parser.add_argument("--upgrade", help = "full path of instance")


def get_ans(msg, expect_ans_list = ("Y", "y", "N", "n", "A", "a")):
    ans = raw_input(msg)
    while ans not in expect_ans_list:
        print "expected answer in", expect_ans_list
        ans = raw_input(msg)
    return ans


def print_zwd_help_msg(instance_full_path):
    if IS_DEB_BASED:
        msg = zwd_help_msg_for_deb_based % (instance_full_path, instance_full_path)
    else:
        msg = zwd_help_msg % instance_full_path

    print msg


def cp_fcgi_scripts(instance_full_path):
    src = os.path.join(ZW_MOD_FULL_PATH, "scripts", "fcgi_main.py")
    dst = os.path.join(instance_full_path, "fcgi_main.py")
    shutil.copyfile(src, dst)
    os.chmod(dst, 0774)

    src = os.path.join(ZW_MOD_FULL_PATH, "scripts", "start_fcgi.sh")
    dst = os.path.join(instance_full_path, "start_fcgi.sh")
    shutil.copyfile(src, dst)
    os.chmod(dst, 0774)

    src = os.path.join(ZW_MOD_FULL_PATH, "scripts", "stop_fcgi.sh")
    dst = os.path.join(instance_full_path, "stop_fcgi.sh")
    shutil.copyfile(src, dst)
    os.chmod(dst, 0774)


    if IS_DEB_BASED:
        conf_file_name = "nginx-debian.conf"
        nginx_conf_tpl = os.path.join(ZW_MOD_FULL_PATH, conf_file_name)
        with open(nginx_conf_tpl) as f:
            buf = f.read()
        buf = buf.replace("/path/to/zw_instance", instance_full_path)
        nginx_conf_path = os.path.join(instance_full_path, conf_file_name)
        with open(nginx_conf_path, "w") as f:
            f.write(buf)

def fix_folder_pages_sym_link(instance_full_path):
    src = os.path.join(instance_full_path, "pages")
    dst = os.path.join(instance_full_path, "static", "pages")

    if os.path.islink(dst):
        got = os.readlink(dst)
        if got != src:
            msg = "expected %s -> %s, got %s" % (src, dst, got)
            print msg
            os.remove(dst)

            msg = "link %s -> %s" % (src, dst)
            print msg
            os.symlink(src, dst)

    elif os.path.isdir(dst) and (not os.path.islink(dst)):
        msg = "expected %s is a symbolic link, got a directory, delete them" % dst
        print msg
        shutil.rmtree(dst)

        msg = "link %s -> %s" % (src, dst)
        print msg
        os.symlink(src, dst)

    elif os.path.isfile(dst):
        msg = "expected %s is a symbolic link, got a file, delete it" % dst
        print msg
        os.remove(dst)

        msg = "link %s -> %s" % (src, dst)
        print msg
        os.symlink(src, dst)

def action_create(instance_full_path):
    default_index_md = "index.md"
    default_index_md_full_path = os.path.join(instance_full_path, "pages", default_index_md)
    folder_pages_full_path = os.path.join(instance_full_path, "pages")

    for folder_name in ("static", "templates", "pages"):
        src = os.path.join(ZW_MOD_FULL_PATH, folder_name)
        dst = os.path.join(instance_full_path, folder_name)

        if not os.path.exists(src):
            msg = "source folder %s doesn't exists, skip copy, you should to create destination %s by manual" % (src, dst)
            log.warn(msg)
            continue

        if os.path.exists(dst):
            msg = "%s already exists, skip" % dst
            log.warn(msg)
            continue
        shutil.copytree(src, dst)

    if not os.path.exists(folder_pages_full_path):
        os.makedirs(folder_pages_full_path, 0774)
   
    if not os.path.exists(default_index_md_full_path):    
        with open(default_index_md_full_path, 'w') as f:
            f.write("default index page in markdown")

    fix_folder_pages_sym_link(instance_full_path)

    for folder_name in ("tmp", "sessions"):
        src_full_path = os.path.join(instance_full_path, folder_name)

        if os.path.exists(src_full_path):
            msg = "%s already exists, skip" % src_full_path
            print msg
            continue
        os.mkdir(src_full_path)

    src = os.path.join(ZW_MOD_FULL_PATH, "default.cfg")
    dst = os.path.join(instance_full_path, "default.cfg")
    if os.path.exists(dst):
        msg = "%s already exists, recover it from default? [Y]es / [N]o " % dst
        ans = get_ans(msg, expect_ans_list = ["Y", "y", "N", "n"])
        if ans in ["Y", "y"]:
            print "copy %s -> %s" % (src, dst)
            shutil.copyfile(src, dst)
    else:
        shutil.copyfile(src, dst)
    os.chmod(dst, 0644)

    cp_fcgi_scripts(instance_full_path)
    print_zwd_help_msg(instance_full_path)


def action_upgrace(instance_full_path):
    folders = ("static", "templates")
    yes_to_all = False

    for i in folders:
        src = os.path.join(ZW_MOD_FULL_PATH, i)
        dst = os.path.join(instance_full_path, i)

        if os.path.exists(dst):
            msg = "%s already exists, recover it from default?  [Y]es / [N]o / yes to [A]ll " % dst
            if yes_to_all:
                shutil.rmtree(dst)
                
                print "copy %s -> %s" % (src, dst)
                shutil.copytree(src, dst)
            else:
                ans = get_ans(msg)
                if ans in ["A", "a"]:
                    yes_to_all = True
                if ans in ["Y", "y", "A", "a"]:
                    shutil.rmtree(dst)
                    
                    print "copy %s -> %s" % (src, dst)
                    shutil.copytree(src, dst)
        else:
            print "copy %s -> %s" % (src, dst)
            shutil.copytree(src, dst)

    fix_folder_pages_sym_link(instance_full_path)


    instance_config_file = os.path.join(instance_full_path, "default.cfg")
    default_config_file = os.path.join(ZW_MOD_FULL_PATH, "default.cfg")

    if not os.path.exists(instance_config_file):
        print "copy %s -> %s" % (default_config_file, instance_config_file)
        shutil.copy(default_config_file, instance_config_file)
    else:
        try:
            zbox_wiki.config_agent.load_config(paths = [instance_config_file])
        except ConfigParser.ParsingError:
            msg = "parsing %s failed, recover it from default? [Y/n]" % instance_config_file
            ans = raw_input(msg)
            if ans in ("Y", "y"):
                shutil.copy(default_config_file, instance_config_file)

    print_zwd_help_msg(instance_full_path)


if __name__ == "__main__":
    args = parser.parse_args()

    if args.create:
        path = args.create
        if not os.path.exists(path):
            os.makedirs(path)

        instance_full_path = os.path.realpath(path)
        action_create(instance_full_path)
        exit(0)

    elif args.upgrade:
        path = args.upgrade
        instance_full_path = os.path.realpath(path)
        action_upgrace(instance_full_path)
        exit(0)

    parser.print_help()
