import time
from ipydex import IPS, activate_ips_on_exception
import os
import secrets

from .utils import render_template, StateConnection

activate_ips_on_exception()


"""
This script serves to deploy the django app `moodpoll` on an uberspace account.
It is largely based on this tutorial: <https://lab.uberspace.de/guide_django.html>.

"""


# call this before running the script:
# eval $(ssh-agent); ssh-add -t 10m


# -------------------------- Begin Essential Config section 1 -----------------------

# this must be changed according to your uberspace accound details (machine name and user name)
remote = "klemola.uberspace.de"
user = "moodpoll"

# -------------------------- Begin Optional Config section 1 -----------------------
# if you know what you are doing you can adapt these seetings to your needs

deployment_dir = "moodpoll_deployment"
inner_deployment_dir = "moodpoll_site"
init_fixture_path = "~/{}/db_backups/init_fixture.json".format(deployment_dir)

app_name = "django-moodpoll"

# this is where the code will live
app_dir_path = "~/" + app_name

# use https here
app_repo_url = "https://github.com/cknoll/django-moodpoll.git"

debug_mode = False

# -------------------------- End Config section -----------------------

# it should not be necessary to change the data below, but it might be interesting what happens.
# (After all, this code runs on your server account under your responsibility).

app_settings = {
    "SECRET_KEY": secrets.token_urlsafe(50),
    "DEBUG": debug_mode,
    "ALLOWED_HOSTS": ["{}.uber.space".format(user)],
    "STATIC_ROOT": "~/{}/collected_static".format(deployment_dir)
    }


# generate the file site_specific_settings.py from the above dictionary
tmpl_path = os.path.join("files", deployment_dir, inner_deployment_dir, "template_site_specific_settings.py")
render_template(tmpl_path, context=dict(app_settings=app_settings))

# generate the uwsgi config file
tmpl_path = os.path.join("files", "uwsgi", "apps-enabled", "template_moodpoll.ini")
render_template(tmpl_path, context=dict(user=user, deployment_dir=deployment_dir,
                                        inner_deployment_dir=inner_deployment_dir))


# safety check

print("The following script is for initial deployment of {}.\n".format(app_name),
      "All exisitng user data of the app will be deleted.\n\n")

res = input("Continue (N/y)? ")
if 1 and res.lower() != "y":
    print("Abort.")
    exit()

c = StateConnection(remote, user=user)

x = True

if x:

    # TODO setup a virtual environment

    c.run('pip3 install uwsgi --user')

    # upload all files for deployment (and also some config templates, which does not harm)

    # TODO: find a more elegant way to do this
    cmd = "rsync  -pthrvz  --rsh='ssh  -p 22 ' files/ {}@{}:~".format(user, remote)
    os.system(cmd)

    c.run('supervisorctl reread')
    c.run('supervisorctl update')
    print("waiting 10s for uwsgi to start")
    time.sleep(10)

    res1 = c.run('supervisorctl status')

    assert "uwsgi" in res1.stdout
    assert "RUNNING" in res1.stdout

    # deploy django app (assume correct requirements.txt)

    # WARNING!! might delete all existing user data for this app
    # TODO: make a backup of the data
    # upload the local version of the repo (assume that the present script is inside the repo)
    cmd = "rsync  -pthrvz  --exclude '/.*' .. {0}@{1}:~/{2}".format(user, remote, app_name)
    os.system(cmd)

    # this was created by git clone
    c.chdir(app_dir_path)

    # install django and other dependencies
    c.run('pip3 install --user -r requirements.txt')

    # install the app from the local directory (allows easy hotfixing)
    c.run('pip3 install --user -e .')

    # this was created by rsync above
    c.chdir("~/"+deployment_dir)

    c.run('python3 manage.py makemigrations')

    # this creates the database
    c.run('python3 manage.py migrate')

    c.run('python3 manage.py test moodpoll')

    # install initial data
    c.run('python3 -c "import moodpoll.utils as u; '
          'u.load_initial_fixtures(abspath=\'{}\')"'.format(init_fixture_path))

    print("copy static files to the right place")
    c.run('python3 manage.py collectstatic --no-input')
