# Deployment Information
## General

This directory contains a script and files to deploy moodpoll at an [uberspace](https://uberspace.de/) account.

We use [deploymentutils](https://codeberg.org/cknoll/deploymentutils) (which is built on top of  [fabric](https://www.fabfile.org/) (>=2.5). This decision seems to be a good compromise between raw bash scripts and a complex configuration management system like ansible – at least for python affine folks.
Complete deployment should (at best) be a onliner.

## How to deploy `moodpoll` locally:

- Create `[project_repo]/config.ini` (see `[project_repo]/deployment/config_example.ini`)
- Ensure you have this directory structure:

```
    [project_root]
    ├── [project_repo]/
    │   ├── .git/...
    │   ├── deployment/
    │   │   ├── README.md                  <- you read this file
    │   │   ├── deploy.py
    │   │   ├── general/...                <- general deployment files
    │   │   ├── uberspace/...              <- uberspace-specific deployment files
    │   │   ├── config_example.py
    │   │   └──  ...
    │   ├── manage.py
    │   ├── config.ini                     <- this has to be created manually (not included in the repo)
    │   └── ...
    │
    └── ...
```

- Run `python3 manage.py migrate`.
- Run `python3 manage.py runserver`.
- Note: If you want to deploy inside a virtual environment you have to manage that yourself.



## How to deploy `moodpoll` on a remote server ([uberspace](https://uberspace.de/)):

Note: We describe deployment on uberspace because from what we know it provides the lowest hurdle to test (and run) moodpoll. Probably there are other equivalent or even better hosters out there. The script `deploy.py` is mainly an automated and adapted version of this setup guide: <https://lab.uberspace.de/guide_django.html>.

### Preparation

- Create an [uberspace](https://uberspace.de)-account (first month is free), then pay what you like.
- Set up your ssh key in the webfrontend
- Create `[project_repo]/config.ini` (see `[project_repo]/deployment/config_example.ini`)
- Locally run `pip install deployment_requirements.txt` (inside `deployment` subdir)

### Deployment

- Run `eval $(ssh-agent); ssh-add -t 5m` to unlock you private ssh-key in this terminal (The deplyment script itself does not ask for your ssh-key password).
- Run `python3 deploy.py --initial remote` for full deployment.
- Run `python3 deploy.py --help` to get an overview of available options for partial deployment.


