
"""
crearted: 2019-12-04 00:29:45 (copied from sober)
author: ck
"""

import re
import os
import json
import tempfile
import time
import importlib
from django.conf import settings

from ipydex import IPS, ST, ip_syshook, dirsearch, sys, activate_ips_on_exception

activate_ips_on_exception()


class DatabaseEmptyError(ValueError):
    pass


appname = "syskontool"
default_deployment_fixture = "deployment_data_stripped.json"
default_backup_fixture = "XXX_backup_all.json"


def get_path(reason):
    assert reason in ["locale", "templates", "static", "fixtures", "migrations"]
    basepath = os.path.dirname(os.path.abspath(__file__))
    res_path = os.path.join(basepath, reason)

    return res_path


def init_settings():
    """
    Some utils functions (e.g. save_stripped_fixtures) are called as a plain python script. Nevertheless they need
    access to the settings. This function enables this.

    :return: settings
    """

    assert "manage.py" in os.listdir("./")
    my_settings = importlib.import_module("{}_site.settings".format(appname))
    settings.configure(my_settings)
    return settings


def get_present_db_content():
    """

    Expected to be run from the django project (e.g. sober-site)
    """

    tmpfname = tempfile.mktemp()
    cmd = "python3 manage.py dumpdata > {}".format(tmpfname)
    # cmd = "python3 manage.py dumpdata | jsonlint -f > {}".format(tmpfname)

    safe_run_command(cmd, False)

    if os.stat(tmpfname).st_size <= 1:
        raise DatabaseEmptyError

    with open(tmpfname) as jfile:
        data = json.load(jfile)

    os.remove(tmpfname)

    return data


def save_stripped_fixtures(fname=None, jsonlint=True, backup=False):
    """
    Loads a json-file or present db-content and strips all entries whose model is on the hardcoded blacklist.
    Leads to a tractable fixture file.

    Expected to be run with in the site-dir

        python3 -c "import syskontool.utils as u; u.save_stripped_fixtures()"

        or

        python3 -c "import syskontool.utils as u; u.save_stripped_fixtures(backup=True)"

    :return: None
    """

    model_blacklist = ["contenttypes*", "sessions*", r"admin\.logentry",
                       r"auth\.permission", r"captcha\.captchastore"]

    blacklist_re = re.compile("|".join(model_blacklist))
    fixture_path = get_path("fixtures")

    if fname is None:

        try:
            data = get_present_db_content()
        except DatabaseEmptyError:
            print("\n\n Database seems to be empty. Nothing to backup.\n\n")
            return

        opfname = default_deployment_fixture
        output_path = os.path.join(fixture_path, opfname)

    else:
        # assume that the file exists; else `open(...)` will fail

        input_path = os.path.join(fixture_path, fname)
        fname2 = fname.replace(".json", "_stripped.json")
        output_path = os.path.join(fixture_path, fname2)

        with open(input_path) as jfile:
            data = json.load(jfile)

    if backup:
        opfname = default_backup_fixture.replace("XXX", time.strftime("%Y-%m-%d__%H-%M-%S"))

        settings = init_settings()
        backup_path = settings.BACKUP_PATH
        if not os.path.exists(backup_path):
            os.makedirs(backup_path)
        output_path = os.path.join(backup_path, opfname)

    keep_data = []
    bad_data = []
    for d in data:
        model = d.get("model")
        if model is None:
            continue
        if blacklist_re.match(model):
            # just for debugging
            bad_data.append(model)
            continue
        else:
            keep_data.append(d)

    # dependency only needed here
    import demjson
    res = demjson.encode(keep_data, encoding="utf-8", compactly=False)

    # remove trailing spaces and ensure final linebreak:
    lb = b"\n"  # byte-linebreak
    res2 = lb.join([line.rstrip() for line in res.split(lb)] + [lb])

    # write bytes because we have specified utf8-encoding
    with open(output_path, "wb") as jfile:
        jfile.write(res2)

    print("file written:", output_path)


def load_fixtures_to_db(fname=None, ask=True):
    """
    This is a helper from the django-app "sober" for setting up the django-project (e.g. "sober_site")
    It executes `python3 manage.py loaddata ...` with the appropriate file (and its path)

    It is supposed to be run in sober_site-dir with the command:

        `python3 -c "import sober.utils as u; u.load_fixtures_to_db()"`

    :param fname:   bare filename (default loads usual sample data)
    :param ask:     Boolean flag whether to ask befor executing the command
    :return:        None
    """

    if fname is None:
        fname = default_deployment_fixture

    fixture_path = get_path("fixtures")
    target_path = os.path.join(fixture_path, fname)

    if not os.path.isfile(target_path):
        raise FileNotFoundError("{} not found!".format(fname))

    cmd = "python3 manage.py loaddata {}".format(target_path)
    safe_run_command(cmd, ask)


def safe_run_command(cmd, ask=True):
    """
    :param cmd:     The command to execute
    :param ask:     Boolean flag whether to ask befor executing the command
    :return:
    """
    print("The following command will be executed on your system:\n\n {}".format(cmd))

    if ask:
        res = input("\nDo you want to proceed (y/N)? ")
    else:
        res = "y"
    if res in ["y", "yes"]:
        rcode = os.system(cmd)
        if rcode != 0:
            print("\nThere were some errors.\n")
        else:
            print("\nDone.\n")
    else:
        print("Abort.")