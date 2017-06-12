#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    WPTDash
    ~~~~~~~

    An application that consolidates pull request build information into
    a single GitHub comment and provides an interface for displaying
    more detailed forms of that information.
"""
import configparser
from datetime import datetime
from flask import Blueprint, g, render_template, request
from jsonschema import validate
import json
import logging
import re
from urllib.parse import parse_qs

from wptdash.commenter import update_github_comment
from wptdash.travis import Travis

CONFIG = configparser.ConfigParser()
CONFIG.readfp(open(r'config.txt'))
GH_TOKEN = CONFIG.get('GitHub', 'GH_TOKEN')
ORG = CONFIG.get('GitHub', 'ORG')
REPO = CONFIG.get('GitHub', 'REPO')
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

bp = Blueprint('wptdash', __name__)


@bp.route('/')
def main():
    return 'wpt dashboard'


@bp.route('/pull/<int:pull_id>')
def pull_detail(pull_id):
    db = g.db
    models = g.models
    pull = db.session.query(models.PullRequest).filter_by(id=pull_id).first()
    return render_template('pull.html', pull=pull, pull_id=pull_id)


@bp.route('/api/pull', methods=['POST'])
def add_pull_request():
    db = g.db
    models = g.models
    schema = {
        '$schema': 'http://json-schema.org/schema#',
        'title': 'Pull Request Event',
        'definitions': {
            'commit_object': {
                'type': 'object',
                'properties': {
                    'ref': {'type': 'string'},
                    'sha': {'type': 'string'},
                    'user': {'$ref': '#/definitions/github_user'},
                    'repo': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'name': {'type': 'string'},
                            'owner': {'$ref': '#/definitions/github_user'},
                        },
                        'required': ['id', 'owner'],
                    },
                },
                'required': ['sha', 'ref', 'user', 'repo']
            },
            'date_time': {
                'type': 'string',
                'format': 'date-time',
            },
            'github_user': {
                'type': 'object',
                'properties': {
                    'login': {'type': 'string'},
                    'id': {'type': 'integer'},
                },
                'required': ['login', 'id'],
            },
        },
        'type': 'object',
        'properties': {
            'pull_request': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'number': {'type': 'integer'},
                    'title': {'type': 'string'},
                    'merged': {'type': 'boolean'},
                    'state': {
                        'enum': ['open', 'closed'],
                    },
                    'head': {'$ref': '#/definitions/commit_object'},
                    'base': {'$ref': '#/definitions/commit_object'},
                    'merged_by': {'oneOf': [
                        {'$ref': '#definitions/github_user'},
                        {'type': 'null'},
                    ]},
                    'created_at': {'$ref': '#/definitions/date_time'},
                    'updated_at': {'$ref': '#/definitions/date_time'},
                    'closed_at': {'oneOf': [
                        {'$ref': '#/definitions/date_time'},
                        {'type': 'null'},
                    ]},
                    'merged_at': {'oneOf': [
                        {'$ref': '#/definitions/date_time'},
                        {'type': 'null'},
                    ]},
                },
                'required': [
                    'id', 'number', 'title', 'merged', 'state', 'head',
                    'base', 'created_at', 'updated_at'
                ],
            },
            'sender': {'$ref': '#/definitions/github_user'},
        },
        'required': ['pull_request', 'sender'],
    }

    data = request.get_json(force=True)
    validate(data, schema)

    pr_data = data['pull_request']
    pr_head = pr_data['head']
    pr_base = pr_data['base']

    creator, _ = models.get_or_create(
        db.session, models.GitHubUser, id=data['sender']['id']
    )
    creator.login = data['sender']['login']

    merger, _ = models.get_or_create(
        db.session, models.GitHubUser,
        id=pr_data['merged_by']['id']
    ) if pr_data['merged_by'] else None, False

    if merger:
        creator.name = pr_data['merged_by']['login']

    head_commit_user, _ = models.get_or_create(
        db.session, models.GitHubUser,
        id=pr_head['user']['id']
    )
    head_commit_user.login = pr_head['user']['login']

    head_commit, _ = models.get_or_create(
        db.session, models.Commit,
        sha=pr_head['sha']
    )
    head_commit.user = head_commit_user

    base_commit_user, _ = models.get_or_create(
        db.session, models.GitHubUser,
        id=pr_base['user']['id']
    )
    base_commit_user.login = pr_base['user']['login']

    base_commit, _ = models.get_or_create(
        db.session, models.Commit,
        sha=pr_base['sha']
    )
    base_commit.user = base_commit_user

    # Query by ID and update in case name or owner have changed
    head_repo_owner, _ = models.get_or_create(
        db.session, models.GitHubUser,
        id=pr_head['repo']['owner']['id']
    )
    head_repo_owner.login = pr_head['repo']['owner']['login']

    head_repo, _ = models.get_or_create(
        db.session, models.Repository,
        id=pr_head['repo']['id']
    )
    head_repo.name = pr_head['repo']['name']
    head_repo.owner = head_repo_owner

    base_repo_owner, _ = models.get_or_create(
        db.session, models.GitHubUser,
        id=pr_base['repo']['owner']['id']
    )
    base_repo_owner.login = pr_base['repo']['owner']['login']

    base_repo, _ = models.get_or_create(
        db.session, models.Repository,
        id=pr_base['repo']['id']
    )
    base_repo.name = pr_base['repo']['name']
    base_repo.owner = base_repo_owner

    pr, _ = models.get_or_create(
        db.session, models.PullRequest, id=pr_data['id']
    )

    pr.number = pr_data['number']
    pr.title = pr_data['title']
    pr.state = models.PRStatus.from_string(pr_data['state'])
    pr.creator = creator
    pr.created_at = datetime.strptime(
        pr_data['created_at'], DATETIME_FORMAT
    )
    pr.merged = pr_data['merged']
    pr.merger = merger
    pr.merged_at = datetime.strptime(
        pr_data['merged_at'], DATETIME_FORMAT
    ) if pr_data['merged_at'] else None
    pr.head_commit = head_commit
    pr.base_commit = base_commit
    pr.head_repository = head_repo
    pr.base_repository = base_repo
    pr.head_branch = pr_head['ref']
    pr.base_branch = pr_base['ref']
    pr.updated_at = datetime.strptime(
        pr_data['updated_at'], DATETIME_FORMAT
    )
    pr.closed_at = datetime.strptime(
        pr_data['closed_at'], DATETIME_FORMAT
    ) if pr_data['closed_at'] else None

    db.session.commit()

    return update_github_comment(pr.number)


@bp.route('/api/build', methods=['POST'])
def add_build():
    db = g.db
    models = g.models
    schema = {
        '$schema': 'http://json-schema.org/schema#',
        'title': 'Travis Build Event',
        'type': 'object',
        'definitions': {
            'date_time': {
                'type': 'string',
                'format': 'date-time',
            },
        },
        'properties': {
            'id': {'type': 'integer'},
            'number': {'type': 'string'},
            'head_commit': {'type': 'string'},
            'base_commit': {'type': 'string'},
            'pull_request': {'type': 'boolean'},
            'pull_request_number': {'oneOf': [
                {'type': 'integer'},
                {'type': 'null'},
            ]},
            'status_message': {
                'enum': ['Pending', 'Passed', 'Fixed', 'Broken', 'Failed',
                         'Still Failing', 'Canceled', 'Errored'],
            },
            'started_at': {'$ref': '#/definitions/date_time'},
            'finished_at': {'$ref': '#/definitions/date_time'},
            'repository': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'owner_name': {'type': 'string'},
                },
                'required': ['name', 'owner_name'],
            },
            'matrix': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'number': {'type': 'string'},
                        'state': {'type': 'string'},
                        'started_at': {'$ref': '#/definitions/date_time'},
                        'finished_at': {'oneOf': [
                            {'$ref': '#/definitions/date_time'},
                            {'type': 'null'},
                        ]},
                        'allow_failure': {'type': 'boolean'},
                        'config': {'type': 'object'},
                    },
                    'required': ['id', 'number', 'state', 'started_at',
                                 'config', 'allow_failure']
                }
            }
        },
        'required': ['id', 'number', 'head_commit', 'base_commit',
                     'pull_request', 'pull_request_number', 'status',
                     'started_at', 'finished_at', 'repository'],
    }

    travis = Travis()

    # The payload comes in the request, but we need to make sure it is
    # really signed by Travis CI. If not, respond to this request with
    # an error.
    resp = validate(json.loads(request.form['payload']), schema)

    verified_payload = travis.get_verified_payload(
        request.form['payload'], request.headers['SIGNATURE']
    )
    error = verified_payload.get('error')
    if error:
        return error.get('message'), error.get('code')


    # Ensure only builds for this repository can post here.
    repository = verified_payload.get("repository")
    owner_name = repository.get("owner_name")
    repo_name = repository.get("name")
    if owner_name != ORG or repo_name != REPO:
        return "Forbidden: Repository Mismatch. Build for %s/%s attempting to comment on %s/%s" % (owner_name, repo_name, ORG, REPO), 403

    pr = models.get(
        db.session, models.PullRequest,
        number=verified_payload['pull_request_number'],
        head_sha=verified_payload['head_commit'],
        base_sha=verified_payload['base_commit']
    )

    if not pr:
        return 'Not Found', 404

    head_commit, _ = models.get_or_create(
        db.session, models.Commit,
        sha=verified_payload['head_commit']
    )

    base_commit, _ = models.get_or_create(
        db.session, models.Commit,
        sha=verified_payload['base_commit']
    )

    build, _ = models.get_or_create(
        db.session, models.Build, id=verified_payload['id']
    )
    build.number = int(verified_payload['number'])
    build.pull_request = pr
    build.head_commit = head_commit
    build.base_commit = base_commit
    build.status = models.BuildStatus.from_string(
        verified_payload['status_message']
    )
    build.started_at = datetime.strptime(
        verified_payload['started_at'], DATETIME_FORMAT
    )
    build.finished_at = datetime.strptime(
        verified_payload['finished_at'], DATETIME_FORMAT
    )
    build.jobs = build.jobs or []

    for job_data in verified_payload['matrix']:
        product_env = next(
            (x for x in job_data['config'].get('env', []) if 'PRODUCT=' in x),
            None
        )
        product_name = re.search(
            r'PRODUCT=([\w:]+)', product_env
        ).group(1) if product_env else None

        if not product_name:
            continue
        product, _ = models.get_or_create(
            db.session, models.Product, name=product_name
        )
        job, _ = models.get_or_create(
            db.session, models.Job, id=job_data['id']
        )
        job.number = float(job_data['number'])
        job.build = build
        job.product = product
        job.allow_failure = job_data['allow_failure']
        job.started_at = datetime.strptime(
            job_data['started_at'], DATETIME_FORMAT
        )
        job.finished_at = datetime.strptime(
            job_data['finished_at'], DATETIME_FORMAT
        )
        build.jobs.append(job)

    db.session.commit()

    return update_github_comment(pr.number)


# @bp.route('/api/stability', methods=['POST'])
# def add_stability_check():
#     db = g.db
#     models = g.models
#     schema = {
#         'type': 'object',
#         'properties': {
#             'pull_request': {
#                 'type': 'integer'
#             },
#             'url': {
#                 'type': 'string'
#             },
#             'product': {
#                 'type': 'string',
#                 'maxLength': 255,
#             },
#             'iterations': {
#                 'type': 'integer'
#             },
#             'status': {
#                 'type': 'string',
#                 'enum': ['pass', 'fail', 'error']
#             },
#             'message': {
#                 'type': 'string'
#             },
#             'results': {
#                 'type': 'array',
#                 'items': {
#                     'type': 'object',
#                     'properties': {
#                         'test': {
#                             'type': 'string',
#                         },
#                         'subtest': {
#                             'type': ['string', 'null']
#                         },
#                         'status': {
#                             'type': 'object',
#                             'patternProperties': {
#                                 '^(?:pass|fail|ok|timeout|error|notrun|crash)$': {
#                                     'type': 'integer'
#                                 }
#                             }
#                         }
#                     },
#                     'required': ['test', 'subtest', 'status']
#                 }
#             }
#         },
#         'required': ['pull_request', 'product', 'iterations', 'status']
#     }

#     data = request.get_json(force=True)
#     validate(data, schema)

#     pr, _ = models.get_or_create(db.session,
#                                  models.PullRequest,
#                                  id=data['pull_request'])

#     product, _ = models.get_or_create(db.session,
#                                       models.StabilityProduct,
#                                       name=data['product'])

#     job = models.StabilityJob(
#         pull=pr,
#         product=product,
#         status=models.JobStatus.from_string(data['status'])
#     )
#     db.session.add(job)

#     for result_data in data.get('results', []):
#         test, _ = models.get_or_create(db.session,
#                                        models.Test,
#                                        test=result_data['test'],
#                                        subtest=result_data['subtest'])
#         result = models.StabilityResult(test=test,
#                                         iterations=data['iterations'])
#         db.session.add(result)

#         for status_name, count in result_data['status'].iteritems():
#             status = models.StabilityStatus(
#                 result=result,
#                 status=models.TestStatus.from_string(status_name),
#                 count=count
#             )
#             db.session.add(status)

#     db.session.commit()

#     # TODO: make this return some useful JSON
#     return 'Created job %s' % job.id
