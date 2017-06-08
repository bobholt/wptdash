from copy import deepcopy
from datetime import datetime
import json
import pytest
from jsonschema.exceptions import ValidationError
import wptdash.models as models
from tests.blueprints.fixtures.payloads import github_webhook_payload


class TestRoot(object):

    """Test the application root route."""

    def test_content(self, client):
        """Root route returns expected text."""
        rv = client.get('/')
        assert b'wpt dashboard' in rv.data


class TestAddPullRequest(object):

    """Test endpoint for adding pull request data from GitHub."""

    def test_no_title(self, client, session):
        """Payload missing title throws jsonschema ValidationError."""
        payload = deepcopy(github_webhook_payload)
        payload['pull_request'].pop('title')
        with pytest.raises(ValidationError):
            client.post('/api/pull', data=json.dumps(payload),
                        content_type="application/json")

    def test_no_creator(self, client, session):
        """Payload missing sender throws jsonschema ValidationError."""
        payload = deepcopy(github_webhook_payload)
        payload.pop('sender')
        with pytest.raises(ValidationError):
            client.post('/api/pull', data=json.dumps(payload),
                        content_type="application/json")

    def test_no_created_at(self, client, session):
        """Payload missing created_at throws jsonschema ValidationError."""
        payload = deepcopy(github_webhook_payload)
        payload['pull_request'].pop('created_at')
        with pytest.raises(ValidationError):
            client.post('/api/pull', data=json.dumps(payload),
                        content_type="application/json")

    def test_no_updated_at(self, client, session):
        """Payload missing updated_at throws jsonschema ValidationError."""
        payload = deepcopy(github_webhook_payload)
        payload['pull_request'].pop('updated_at')
        with pytest.raises(ValidationError):
            client.post('/api/pull', data=json.dumps(payload),
                        content_type="application/json")

    def test_no_merged(self, client, session):
        """Payload missing merged throws jsonschema ValidationError."""
        payload = deepcopy(github_webhook_payload)
        payload['pull_request'].pop('merged')
        with pytest.raises(ValidationError):
            client.post('/api/pull', data=json.dumps(payload),
                        content_type="application/json")

    def test_no_head(self, client, session):
        """Payload missing head throws jsonschema ValidationError."""
        payload = deepcopy(github_webhook_payload)
        payload['pull_request'].pop('head')
        with pytest.raises(ValidationError):
            client.post('/api/pull', data=json.dumps(payload),
                        content_type="application/json")

    def test_no_base(self, client, session):
        """Payload missing base throws jsonschema ValidationError."""
        payload = deepcopy(github_webhook_payload)
        payload['pull_request'].pop('base')
        with pytest.raises(ValidationError):
            client.post('/api/pull', data=json.dumps(payload),
                        content_type="application/json")

    def test_no_state(self, client, session):
        """Payload missing state throws jsonschema ValidationError."""
        payload = deepcopy(github_webhook_payload)
        payload['pull_request'].pop('state')
        with pytest.raises(ValidationError):
            client.post('/api/pull', data=json.dumps(payload),
                        content_type="application/json")

    def test_complete_payload(self, client, session):
        """Complete webhook payload creates pull request object in db."""
        rv = client.post('/api/pull', data=json.dumps(github_webhook_payload),
                         content_type="application/json")
        pr = session.query(models.PullRequest).filter(
            models.PullRequest.id == github_webhook_payload['pull_request']['id']
        ).one_or_none()
        assert pr.state == models.PRStatus.OPEN
        assert pr.creator.id == 6752317
        assert pr.creator.login == 'baxterthehacker'
        assert pr.created_at == datetime.strptime('2015-05-05T23:40:27Z',
                                                  '%Y-%m-%dT%H:%M:%SZ')
        assert not pr.merged
        assert not pr.merger
        assert not pr.merged_at
        assert pr.head_commit.sha == "0d1a26e67d8f5eaf1f6ba5c57fc3c7d91ac0fd1c"
        assert pr.head_commit.user.id == 6752317
        assert pr.head_commit.user.login == 'baxterthehacker'
        assert pr.base_commit.sha == "9049f1265b7d61be4a8904a9a27120d2064dab3b"
        assert pr.base_commit.user.id == 6752317
        assert pr.base_commit.user.login == 'baxterthehacker'
        assert pr.head_repository.id == 35129377
        assert pr.head_repository.name == 'public-repo'
        assert pr.head_repository.owner.id == 6752317
        assert pr.head_repository.owner.login == 'baxterthehacker'
        assert pr.base_repository.id == 35129377
        assert pr.base_repository.name == 'public-repo'
        assert pr.base_repository.owner.id == 6752317
        assert pr.base_repository.owner.login == 'baxterthehacker'
        assert pr.head_branch == 'changes'
        assert pr.base_branch == 'master'
        assert pr.updated_at == datetime.strptime('2015-05-05T23:40:27Z',
                                                  '%Y-%m-%dT%H:%M:%SZ')
        assert not pr.closed_at


class TestPullDetail(object):

    """Test the pull request detail page."""

    def test_no_data(self, client, session):
        """PR detail route says "No information" when no pull in DB."""
        rv = client.get('/pull/1')
        assert b'No information' in rv.data

    def test_no_builds(self, client, session):
        """PR detail route says "No builds" when pull has no build info."""
        pull_request = models.PullRequest(state=models.PRStatus.OPEN,
                                          merged=False, head_sha='abcdef12345',
                                          base_sha='12345abcdef', title='abc',
                                          head_repo_id=1, base_repo_id=1,
                                          head_branch='foo', base_branch='bar',
                                          created_at=datetime.now(),
                                          updated_at=datetime.now())
        session.add(pull_request)
        session.commit()

        rv = client.get('/pull/1')
        assert b'No builds' in rv.data

    def test_builds(self, client, session):
        """PR detail route displays builds when they exist."""
        pull_request = models.PullRequest(state=models.PRStatus.OPEN,
                                          merged=False, head_sha='abcdef12345',
                                          base_sha='12345abcdef', title='abc',
                                          head_repo_id=1, base_repo_id=1,
                                          head_branch='foo', base_branch='bar',
                                          created_at=datetime.now(),
                                          updated_at=datetime.now())
        build = models.Build(number=123, status=models.BuildStatus.PENDING,
                             started_at=datetime.now())

        pull_request.builds = [build]

        session.add(pull_request)
        session.commit()

        rv = client.get('/pull/1')
        assert b'Build Number' in rv.data
