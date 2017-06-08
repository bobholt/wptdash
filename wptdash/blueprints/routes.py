# -*- coding: utf-8 -*-
"""
    WPTDash
    ~~~~~~~

    An application that consolidates pull request build information into
    a single GitHub comment and provides an interface for displaying
    more detailed forms of that information.
"""
from datetime import datetime

from flask import Blueprint, g, render_template, request
from jsonschema import validate

GITHUB_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

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
                    'id', 'title', 'merged', 'state', 'head', 'base',
                    'created_at', 'updated_at'
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

    pr.title = pr_data['title']
    pr.state = models.PRStatus.from_string(pr_data['state'])
    pr.creator = creator
    pr.created_at = datetime.strptime(
        pr_data['created_at'], GITHUB_DATETIME_FORMAT
    )
    pr.merged = pr_data['merged']
    pr.merger = merger
    pr.merged_at = datetime.strptime(
        pr_data['merged_at'], GITHUB_DATETIME_FORMAT
    ) if pr_data['merged_at'] else None
    pr.head_commit = head_commit
    pr.base_commit = base_commit
    pr.head_repository = head_repo
    pr.base_repository = base_repo
    pr.head_branch = pr_head['ref']
    pr.base_branch = pr_base['ref']
    pr.updated_at = datetime.strptime(
        pr_data['updated_at'], GITHUB_DATETIME_FORMAT
    )
    pr.closed_at = datetime.strptime(
        pr_data['closed_at'], GITHUB_DATETIME_FORMAT
    ) if pr_data['closed_at'] else None

    db.session.commit()

    return 'OK', 200


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
