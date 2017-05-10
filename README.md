## Installation
This installation process uses [Ansible](http://docs.ansible.com/) to configure
the server to use [nginx](http://nginx.org/) and
[uWSGI](http://uwsgi-docs.readthedocs.io/en/latest/) to serve a
[Flask](http://flask.pocoo.org/) application. It expects nginx to be able to
use port 80.

#### Requirements

- Ubuntu-like server environment
- [git](https://git-scm.com/downloads)
- [Ansible >= 2.3.0.0](http://docs.ansible.com/ansible/intro_installation.html#latest-releases-via-pip)
  - Note: on Ubuntu, this requires installing ansible via `pip`, not `apt`.

#### Process

This is how to install the dependencies and application on a base Ubuntu 16.04
box. Git should come out of the box.

1. Create a server instance wherever you like.
2. Add a non-root user to own the application.
  - `adduser wptdash` as root
  - You will create a password for this user. Keep it secret. Keep it safe.
3. Ensure the new user is able to `sudo`.
  - `adduser wptdash sudo` as root
4. Log into the server as the new user.
5. Fork this repository and clone it into the user's home directory.
  - `git clone https://github.com/<your user name>/wptdash.git`
  - You will be editing a file under version control, so you should create your
    own fork and store your changes there.
6. Run install script to install system dependencies.
  -`sudo -H ./install.sh`
12. Install Ansible.
  - `sudo -H pip install ansible`
14. Configure the application for your project. See
    [Configuration](#configuration), below.
15. Change into the `ansible` directory and run the provisioning script.
  - `cd wptdash/ansible`
  - `ansible-playbook provision.yml`
  - Note: this must be run from the `wptdash/ansible` directory, or it
    will fail.
  - **Note:** This does not install any of the python modules into virtual_env,
    but at the system level. This is possible with Ansible, just not implemented
    yet.
