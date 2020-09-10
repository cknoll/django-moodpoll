# Deployment Information
## General

This directory contains a script and files to deploy moodpoll locally or at a fresh [uberspace](https://uberspace.de/) account.

We use [deploymentutils](https://codeberg.org/cknoll/deploymentutils) (which is built on top of  [fabric](https://www.fabfile.org/) (>=2.5). This decision seems to be a good compromise between raw bash scripts and a complex configuration management system like ansible – at least for python affine folks.
Complete deployment should (at best) be a onliner.

## How to deploy `moodpoll` locally:

- Ensure you have this directory structure:

```
    [project_root]
    ├── [project_repo]/
    │   ├── .git/...
    │   ├── deployment_helpers/
    │   │   ├── README.md                  <- you read this file
    │   │   ├── deploy.py
    │   │   ├── general/...                <- general deployment files
    │   │   ├── uberspace/...              <- uberspace-specific deployment files
    │   │   └──  ...
    │   └── ...
    │
    ├── local_testing/                     <- will be auto-created by deploy.py
    └── ...
```

- run `python3 deploy.py local`
    - If you plan to play arround with the source files you can symlink them instead of copy: `deploy.py  -l local`.
- go to `[project_root]/local_deployment/` and run `python3 manage.py runserver`
- note: if you want to deploy inside a virtual environment you have to manage that yourself


## Background

The deployment directory is placed outside of \[project_repo\] to keep the repo directory clean. Thus it can still be used for development and for remote deployment. This structure also makes it easier to handle different secrets and fixtures for different usecases (local deployment, example content, testing, production).


## How to deploy `moodpoll` on a remote server ([uberspace](https://uberspace.de/)):

Note: We describe deployment on uberspace because from what we know it provides the lowest hurdle to test (and run) moodpoll. Probably there are other equivalent or even better hosters out there.

### Preparation

- Create an [uberspace](https://uberspace.de)-account (first month is free), then pay what you like.
- Set up your ssh key in the webfrontend
- Locally `pip install deployment_requirements.txt`

### Deployment

- Adapt the config section of `deploy.py` and (optionally) have a look what happens in the remainder of that script.
    - If you use uberspace, you probably only need to change the username
    - The script is mainly an automated version of this setup guide: <https://lab.uberspace.de/guide_django.html>.
- Run `eval $(ssh-agent); ssh-add -t 5m` to unlock you private ssh-key in this terminal (The deplyment script itself does not ask for your ssh-key password).
- Run `python3 deploy.py remote`.
