# Overview

This dir contains a script and file to deploy moodpoll at a fresh uberspace account.

We use [fabric](https://www.fabfile.org/) (>=2.5) because it seems to be a good compromise between bash and ansible (for python affine folks).
Complete deployment should (at best) be a onliner.

# How to deploy:

 - Create an [uberspace](https://uberspace.de)-account (first month is free), then pay what you think.
 - Set up your ssh key in the webfrontend
 - Locally `pip install deployment_requirements.txt`
 - Edit the config section of `uberspace_initial_deployment.py` and (optionally) have a look what happens in the remainder of that script.
 (It is mainly a automated version of this setup guide: <https://lab.uberspace.de/guide_django.html>
 - Run `python3 uberspace_initial_deployment.py`



