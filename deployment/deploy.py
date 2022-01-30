import time
import os
import secrets
import re
import os

# these packages are not in requirements.txt but in deployment_requirements.txt
# noinspection PyUnresolvedReferences
from packaging import version
# noinspection PyUnresolvedReferences
from ipydex import IPS, activate_ips_on_exception

min_du_version = version.parse("0.3.0")
try:
    # this is not listed in the requirements because it is not needed on the deployment server
    # noinspection PyPackageRequirements,PyUnresolvedReferences
    import deploymentutils as du

    vsn = version.parse(du.__version__)
    if vsn < min_du_version:
        print(f"You need to install `deploymentutils` in version {min_du_version} or later. Quit.")
        exit()


except ImportError as err:
    print("You need to install the package `deploymentutils` to run this script.")

# simplify debugging
activate_ips_on_exception()

"""
This script serves to deploy and maintain the django app `moodpoll` on an uberspace account.
It is largely based on this tutorial: <https://lab.uberspace.de/guide_django.html>.
"""

# call this before running the script:
# eval $(ssh-agent); ssh-add -t 10m


# -------------------------- Essential Config section  ------------------------

config = du.get_nearest_config("config.ini")

remote = config("remote")
user = config("user")

# -------------------------- Begin Optional Config section -------------------------
# if you know what you are doing you can adapt these settings to your needs

# this is the root dir of the project (where setup.py lies)
# if you maintain more than one instance (and deploy.py lives outside the project dir, this has to change)
project_src_path = os.path.dirname(du.get_dir_of_this_file())
assert os.path.isfile(os.path.join(project_src_path, "manage.py"))

# this is deprecated
# base directory for local testing deployment
# might also be the place for a custom deploy_local.py script
local_deployment_workdir = os.path.abspath("../../local_testing")

# directory for deployment files (e.g. database files)
deployment_dir = config("deployment_dir")

app_name = config("app_name")

TIME_ZONE = config("TIME_ZONE")

# -------------------------- End Config section -----------------------

# it should not be necessary to change the data below, but it might be interesting what happens.

# this is only relevant if you maintain more than one instance
instance_path = os.path.join(du.get_dir_of_this_file(), "specific")
# (After all, this code runs on your computer/server under your responsibility).

local_deployment_files_base_dir = du.get_dir_of_this_file()
repo_base_dir = os.path.split(local_deployment_files_base_dir)[0]
app_path = os.path.join(repo_base_dir, app_name)

du.argparser.add_argument("-o", "--omit-tests", help="omit test execution (e.g. for dev branches)", action="store_true")
du.argparser.add_argument("-d", "--omit-database",
                          help="omit database-related-stuff (and requirements)", action="store_true")
du.argparser.add_argument("-s", "--omit-static", help="omit static file handling", action="store_true")
du.argparser.add_argument("-x", "--omit-backup",
                          help="omit db-backup (avoid problems with changed models)", action="store_true")
du.argparser.add_argument("-p", "--purge", help="purge target directory before deploying", action="store_true")
du.argparser.add_argument("--debug", help="start debug interactive mode (IPS), then exit", action="store_true")

args = du.parse_args()

final_msg = f"Deployment script {du.bgreen('done')}."

if args.target == "remote":
    # this is where the code will live after deployment
    target_deployment_path = f"/home/{user}/{deployment_dir}"
    static_root_dir = f"{target_deployment_path}/collected_static"
    debug_mode = False
    pip_command = "python3 -m pip"
    pip_user_flag = " --user"  # this might be dropped if we use a virtualenv on the remote target
    allowed_hosts = [f"{user}.uber.space"]
else:
    # settings for local deployment
    static_root_dir = ""
    target_deployment_path = os.path.join(local_deployment_workdir, deployment_dir)
    debug_mode = True
    pip_command = "python3 -m pip"
    pip_user_flag = ""  # assume activated virtualenv on local target
    allowed_hosts = ["*"]

# TODO
init_fixture_path = os.path.join(target_deployment_path, "fixitures/init_fixture.json")


# this will be passed to the template of site_specific_settings.py
app_settings = {
    "SECRET_KEY": secrets.token_urlsafe(50),
    "DEBUG": debug_mode,
    "ALLOWED_HOSTS": allowed_hosts,
    "STATIC_ROOT": static_root_dir,
    "TIME_ZONE": TIME_ZONE,
    "MOOD_VALUE_MAX": 2,
    "MOOD_VALUE_MIN": -3,
    }

# generate the file site_specific_settings.py from the above dictionary
tmpl_path = os.path.join("specific", "settings", "template_site_specific_settings.py")
du.render_template(tmpl_path, context=dict(app_settings=app_settings))

# generate the uwsgi config file
tmpl_path = os.path.join("uberspace", "uwsgi", "apps-enabled", "template_moodpoll.ini")
du.render_template(tmpl_path, context=dict(user=user, deployment_dir=target_deployment_path))


# TODO: make a backup of the remote-data
# print a warning for data destruction
du.warn_user(app_name, args.target, args.unsafe, deployment_path=target_deployment_path, user=user, host=remote)


c = du.StateConnection(remote, user=user, target=args.target)

# TODO setup a virtual environment (also adapt template_moodpoll.ini)
# TODO activate virtual environment

if args.debug:
    IPS()
    exit()

if args.initial:
    print("\n", "install uwsgi", "\n")
    c.run(f'{pip_command} install -U {pip_user_flag} pip', target_spec="remote")
    c.run(f'{pip_command} install -U {pip_user_flag} uwsgi', target_spec="remote")

    print("\n", "upload config files for initial deployment", "\n")

    srcpath1 = os.path.join(local_deployment_files_base_dir, "uberspace")
    srcpath2 = os.path.join(local_deployment_files_base_dir, "general")

    filters = "--exclude='README.md'"
    c.rsync_upload(srcpath1 + "/", "~", filters=filters, target_spec="remote")
    c.rsync_upload(srcpath2 + "/", "~", filters=filters, target_spec="remote")

    if args.target == "remote":

        c.run('supervisorctl reread', target_spec="remote")
        c.run('supervisorctl update', target_spec="remote")
        c.run('supervisorctl restart uwsgi', target_spec="remote")
        c.run('uberspace web backend set / --http --port 8000', target_spec="remote")
        print("waiting 10s for uwsgi to start")
        time.sleep(10)

        res1 = c.run('supervisorctl status', target_spec="remote")

        assert "uwsgi" in res1.stdout
        assert "RUNNING" in res1.stdout

if args.purge:
    if not args.omit_backup:
        print("\n", du.bred("  The `--purge` option explicitly requires the `--omit-backup` option. Quit."), "\n")
        exit()
    else:
        answer = input(f"purging <{args.target}>/{target_deployment_path} (y/N)")
        if answer != "y":
            print(du.bred("Aborted."))
            exit()
        c.run(f"rm -r {target_deployment_path}", target_spec="both")

print("\n", "ensure that deployment path exists", "\n")
c.run(f"mkdir -p {target_deployment_path}", target_spec="both")

c.chdir(target_deployment_path)

if not args.initial and not args.omit_backup:

    print("\n", "backup old database", "\n")
    res = c.run('python3 manage.py savefixtures', target_spec="both")

print("\n", "upload current application files for deployment", "\n")
# omit irrelevant files (like .git)
# TODO: this should be done more elegantly
filters = \
    f"--exclude='.git/' " \
    f"--exclude='.idea/' " \
    f"--exclude='settings/__pycache__/*' " \
    f"--exclude='{app_name}/__pycache__/*' " \
    f"--exclude='__pycache__/' " \
    f"--exclude='django_moodpoll.egg-info/' " \
    f"--exclude='db.sqlite3' " \
    ""

c.rsync_upload(project_src_path + "/", target_deployment_path, filters=filters, target_spec="both")

# now rsync instance-specific data (this might overwrite generic data from the project)
# this file should usually not be overwritten
filters = "--exclude='README.md' --exclude='*/template_*'"
c.rsync_upload(instance_path + "/", target_deployment_path, filters=filters, target_spec="both")


if args.initial and args.target == "remote":

    # copy maintenance page to where static pages live
    c.run(f"cp -R {target_deployment_path}/deployment/maintenance/* ~/html/")

    # install cron service for spam removal
    res = c.run("crontab -l", target_spec="remote", warn=False)
    old_crontab = res.stdout # this is empty if crontab does not yet exist

    if "manage.py removespam" not in res.stdout:
        new_cron_line = f"12 4 * * * python3 {target_deployment_path}/manage.py removespam"
        new_cron_tab = f"{old_crontab}\n{new_cron_line}"
        cron_command = f'echo "{new_cron_tab}" | crontab -'
        res = c.run(cron_command, target_spec="remote")
    else:
        print(du.bgreen("crontab entry already present"))

# .............................................................................................

print("\n", "install dependencies", "\n")
res = c.run(f'{pip_command} show django', target_spec="both")
loc = re.findall("Location:.*", res.stdout)
if args.target == "local" and len(loc) == 0:
    msg = f"{du.bred('Caution:')} django seems not to be installed on local system.\n" \
          f"This might indicate some problem with pip or the virtualenv not activated.\n"
    print(msg)

    cmd = ["python3", "-c", "import sys; print('; '.join(sys.path))"]
    syspath = c.run(cmd, target_spec="local").stdout

    print("This is your current python-path:\n\n", syspath)

    res = input("Continue and install django in that path (N/y)? ")
    if res.lower() != "y":
        print(du.bred("Aborted."))
        exit()

c.run(f'{pip_command} install{pip_user_flag} -r requirements.txt', target_spec="both")

if args.symlink:
    assert args.target == "local"
    c.run(["rm", "-r", os.path.join(target_deployment_path, app_name)], target_spec="local")
    c.run(["ln", "-s", app_path, os.path.join(target_deployment_path, app_name)], target_spec="local")


if not args.omit_database:

    print("\n", "prepare and create new database", "\n")

    # this was only necessary when there where no migrations in the repo
    # c.run('python3 manage.py makemigrations', target_spec="both")

    # delete old db
    c.run('rm -f db.sqlite3', target_spec="both")

    # this creates the new database
    c.run('python3 manage.py migrate', target_spec="both")

    # TODO: this should be simplified to f"python3 manage.py loaddata {init_fixture_path}"
    print("\n", "install initial data", "\n")

    c.run(f"python3 manage.py loaddata {init_fixture_path}", target_spec="both")

if not args.omit_static:
    print("\n", "collect static files", "\n")
    c.run('python3 manage.py collectstatic --no-input', target_spec="remote")

    if args.target == "remote":
        print("\n", "copy static files to the right place where apache can find it", "\n")
        c.chdir(f"/var/www/virtual/{user}/html")
        c.run('rm -rf static')
        c.run(f'cp -r {static_root_dir} static')
        c.chdir(target_deployment_path)


if not args.omit_tests:
    print("\n", "run tests", "\n")
    c.run('python3 manage.py test moodpoll', target_spec="both")

if args.target == "local":
    print("\n", f"now you can go to {target_deployment_path} and run `python3 manage.py runserver", "\n")
else:
    print("\n", "restart uwsgi service", "\n")
    c.run(f"supervisorctl restart uwsgi", target_spec="remote")

print(final_msg)
