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

The server is configured an deployed via Ansible. See [that directory](ansible/) for more details.
