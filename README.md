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

#### On Ansible Vault
This project uses Ansible Vault to encrypt secrets. In order to work, a key
file needs to be shared between the server and the person responsible for
encrypting the secrets file. The process for doing this as the secret
keeper is as follows:

1. Install ansible on your local machine.
2. Create a `~/.vault_pass` file in your home directory. The contents of
   this file should only consist of the key you would like to use to
   encrypt and decrypt the secrets file.
   - Recommended: `export ANSIBLE_VAULT_PASSWORD_FILE=~/.vault_pass` to
     to avoid having to refer to that file every time you encrypt/decrypt.
     The rest of the instructions will assume you have done this. If not,
     you will have to add the `--vault-password-file=~/.vault_pass` flag
     to `ansible-vault` commands.
3. Replace the existing `wptdash/ansible/group_vars/all/vault` file with
   one that includes the following variables in plain text (see the
   vault.sample file for the format)
   - `vault_db_password`: The password you would like to use for the
      postgresql user. This can be anything you want.
   - `vault_github_token`: This must be a GitHub auth token for the
      user that will be commenting on the PRs.
   - `vault_hmac_secret`: A secret string that will be shared with the
     other web-platform-tests bots and applications that will be posting
     data to this application.
4. Encrypt the vault file.
   - `ansible-vault encrypt vault` from the `wptdash/ansible/group_vars/all
   directory`
5. Commit this file to the repository.

#### Process

This is how to install the dependencies and application on a base Ubuntu 16.04
box. Git should come out of the box.

1. Create a server instance wherever you like.
2. Add a non-root user on the server to own the application.
  - `adduser wptdash` as root
  - You will create a password for this user. Keep it secret. Keep it safe.
3. Ensure the new user is able to `sudo`.
  - `adduser wptdash sudo` as root
4. Ensure you can log into this user with passwordless ssh.
5. Log into the server as the new user.
6. Run the `run-playbook.sh` script with to provision the target (staging or production), using the user you created in step 2.
  - `./run-playbook.sh provision staging --user=wptdash`
  - This will ask for the sudo password for the user. This is the password you created in step 2.
7. Run the `run-playbook.sh` script to configure the target (staging or production), using the user you created in step 2.
  - `./run-playbook.sh configure staging --user=wptdash`
  - This will ask for the sudo password for the user. This is the password you created in step 2.
