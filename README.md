# PR Results Consolidator

This application listens to pull request webhooks from GitHub, build
notifications from TravisCI, and requests from other bots in the
web-platform-tests ecosystem; consolidates the data from each of those
providers; and posts a single summary comment on the state of the pull request
to the PR in GitHub. The application also provides a UI to allow
web-platform-tests maintainers to browse complete build results.

## Do I need to do something with this?

This application lives on a server, and only web-platform-tests infrastructure
maintainers need concern themselves with it.

## Maintaining the Server

The server is configured an deployed via Ansible. See [that directory](ansible/
) for more details.

## Setting up the GitHub Commenter

You need to set up an account on GitHub to act as the user commenting on PRs
with build information, and share the personal access token with this project.

1. If you're doing this, you're probably a maintainer of this project. You
   should be [set up as a deployer](ansible#setting-yourself-up-as-a-deployer)
   (you will need the `vault_pass` file to make changes here anyway). Read
   over the [Ansible Vault](ansible#ansible-vault) section as well.
2. Create or log in to the user account that will be commenting on GitHub PRs
   on behalf of this application.
3. Create a personal access token for that user.
  - Go to https://github.com/settings/tokens.
  - Click "Generate new token"
  - On the creation page, name the token and give it at least `public_repo`
    and `user:email` permissions.
4. Set the `vault_github_commenter_token` value to the personal access token. (
   Remember to add `--vault-password-file=path-to-vault_pass-file` to these
   commands if you haven't exported the `
   ANSIBLE_VAULT_PASSWORD_FILE=path-to-vault_pass-file` environment variable
   on your system)
  - `ansible-vault decrypt ansible/group_vars/all/vault`
  - Change the token value
  - `ansible-vault encrypt ansible/group_vars/all/vault`
5. Commit the change and open a PR.
6. Once approved and merged to master,
   [deploy](ansible#deploying-application-changes-to-a-server) the change.

## Setting up the Travis Webhook

Travis needs to send a build notification to this application in order to
populate it with build status data.

1. Change `notifications.webhooks` in `.travis.yml` (probably at the bottom) in
   https://github.com/w3c/web-platform-tests to point to
   `http://pulls.web-platform-tests.org/api/build`.
