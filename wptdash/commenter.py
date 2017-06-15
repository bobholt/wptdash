#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import requests
from flask import render_template

from wptdash.github import GitHub


# TODO: make this return some useful JSON
def update_github_comment(pr):
    github = GitHub()
    comment = render_template('comment.md', pull=pr)
    try:
        github.post_comment(pr.number, comment)
    except requests.RequestException as err:
        logging.error(err.response.text)
        return err.response.text, 500
    return 'OK', 200
