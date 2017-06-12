#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import requests

from wptdash.github import GitHub


# TODO: make this return some useful JSON
def update_github_comment(pr_number):
    github = GitHub()
    comment = '# Comment Test'
    try:
        github.post_comment(pr_number, comment)
    except requests.RequestException as err:
        logging.error(err.response.text)
        return err.response.text, 500

    return 'OK', 200
