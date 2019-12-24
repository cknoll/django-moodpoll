
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
from collections import defaultdict

from django.conf import settings, Settings

from ipydex import IPS, ST, ip_syshook, dirsearch, sys, activate_ips_on_exception

activate_ips_on_exception()


class DatabaseEmptyError(ValueError):
    pass


# This dict must contain only data which is consitent with urlpatterns from `urls.py`
# To prevent a circular import we cannot use `from django.urls import reverse`.
# Therefore we have to use duplicated data.
# There is a unit tests which ensures integrity.
duplicated_urls_data = {"contact-page": "/contact",
                        "about-page": "/about",
                        "new_poll": "/new",
                        }
duplicated_urls = defaultdict(lambda: "__invalid_url__", duplicated_urls_data)


appname = "moodpoll"
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
    access to the settings. This function ensures that the settings are initialized. (But are not initilized twice.)

    :return: settings
    """

    if not isinstance(settings._wrapped, Settings):
        assert "manage.py" in os.listdir("./")
        my_settings = importlib.import_module("{}_site.settings".format(appname))
        settings.configure(my_settings)
    return settings


# noinspection PyPep8Naming
def get_project_READMEmd(marker_a=None, marker_b=None):
    """
    Return the content of README.md from the root directory of this project

    (optionally return only the text between the two marker-strings)
    :return:
    """

    basepath = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(basepath)
    fpath = os.path.join(project_root, "README.md")
    with open(fpath, "r") as txt_file:
        txt = txt_file.read()

    if marker_a is None:
        assert marker_b is None
        return txt
    else:
        assert marker_b is not None

    try:
        idx1 = txt.index(marker_a) + len(marker_a)
        idx2 = txt.index(marker_b)
    except ValueError:
        IPS()
        return txt

    return txt[idx1:idx2]


def get_present_db_content():
    """

    Expected to be run from the django project (the site dir where manage.py lives)
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

        python3 -c "import moodpoll.utils as u; u.save_stripped_fixtures()"

        or

        python3 -c "import moodpoll.utils as u; u.save_stripped_fixtures(backup=True)"

    :return: fname of written file
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

    return output_path


def load_fixtures_to_db(fname=None, ask=True):
    """
    This is a helper from the django-app for setting up the django-project (i.e. site dir)
    It executes `python3 manage.py loaddata ...` with the appropriate file (and its path)

    It is supposed to be run in site-dir with the command:

        `python3 -c "import moodpoll.utils as u; u.load_fixtures_to_db()"`

    :param fname:   bare filename (default loads usual sample data)
    :param ask:     Boolean flag whether to ask befor executing the command
    :return:        None
    """

    if fname is None:
        fname = default_deployment_fixture

    fixture_path = get_path("fixtures")

    if fname.startswith("./"):
        target_path = fname
    else:
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

