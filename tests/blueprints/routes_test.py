from datetime import datetime
import wptdash.models as models

class TestRoot(object):

    """Test the application root route."""

    def test_content(self, client):
        """Root route returns expected text."""
        rv = client.get('/')
        assert b'wpt dashboard' in rv.data

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
                                          base_sha='12345abcdef',
                                          head_repo_id=1, base_repo_id=1,
                                          created_at=datetime.now())
        session.add(pull_request)
        session.commit()

        rv = client.get('/pull/1')
        assert b'No builds' in rv.data

    def test_builds(self, client, session):
        """PR detail route displays builds when they exist."""
        pull_request = models.PullRequest(state=models.PRStatus.OPEN,
                                          merged=False, head_sha='abcdef12345',
                                          base_sha='12345abcdef',
                                          head_repo_id=1, base_repo_id=1,
                                          created_at=datetime.now())
        build = models.Build(number=123, status=models.BuildStatus.PENDING,
                             started_at=datetime.now())

        pull_request.builds = [build]

        session.add(pull_request)
        session.commit()

        rv = client.get('/pull/1')
        assert b'Build Number' in rv.data
