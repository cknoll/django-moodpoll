from fabric import Connection
import time
from ipydex import IPS, activate_ips_on_exception
activate_ips_on_exception()
import os
import secrets

from utils import render_template



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
app_dir_name = "~/" + app_name

# use https here
app_repo_url = "https://github.com/cknoll/django-moodpoll.git"

debug_mode = False

# -------------------------- End Config section -----------------------

# it should not be necessary to change the data below, but might be interesting what happens.
# (After all this code runs on your account under your responsibility).

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
exit()

# savety check

print("The following script is for initial deployment of {}.\n",
      "All exisitng user data of the app will be deleted.\n\n")

res = input("Continue (N/y)? ")
if 0 and res.lower() != "y":
    print("Abort.")
    exit()


class StateConnection(object):
    """
    Wrapper class for fabric connection which remembers the working directory.
    """

    def __init__(self, remote, user):
        self._c = Connection(remote, user)
        self.dir = None

    def chdir(self, path):
        """
        The following works on uberspace:

        c.chdir("etc")
        c.chdir("~")
        c.chdir("$HOME")

        :param path:
        :return:
        """

        if path is None:
            self.dir = None
            return

        cmd = "cd {} && pwd".format(path)
        res = self.run(cmd, hide=True, warn=True)

        if res.exited != 0:
            print("Could not change directory. Error message: {}".format(res.stderr))
        else:
            # store the result of pwd in the variable
            self.dir = res.stdout.strip()

    def run(self, cmd, use_dir=True, hide=False, warn=False, printonly=False):
        """

        :param cmd:
        :param use_dir:
        :param hide:        see docs of invoke
        :param warn:        see docs of invoke
        :return:
        """

        if use_dir and self.dir is not None:
            cmd = "cd {}; {}".format(self.dir, cmd)

        if not printonly:
            res = self._c.run(cmd, hide=hide, warn=warn)
        else:
            print("->:", cmd)
            res = None
        return res

c = StateConnection(remote, user=user)

x = False

if x:

    # TODO setup a virtual environment

    c.run('pip3 install uwsgi --user')

    # upload all files for deployment (and also some config templates, which does not harm)

    # TODO: find a more elegant way to do this
    cmd = "rsync  -pthrvz  --rsh='ssh  -p 22 ' files/ {}@{}:~".format(user, remote)
    os.system(cmd)

    c.run('supervisorctl reread')
    c.run('supervisorctl update')
    print("waiting for uwsgi to start")
    time.sleep(10)

    res1 = c.run('supervisorctl status')

    assert "uwsgi" in res1.stdout
    assert "RUNNING" in res1.stdout

    # deploy django app (assume correct requirements.txt)

    # WARNING!! deletes all existing user data for this app
    # TODO: make a backup of the data
    # TODO: use moodpoll from the local repo directory (and not from github)
    c.run('rm -rf {}'.format(app_dir_name))
    c.run('git clone --depth 1 {}'.format(app_repo_url))

    # this was created by git clone
    c.chdir(app_dir_name)

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

    c.run('python3 manage.py collectstatic')
