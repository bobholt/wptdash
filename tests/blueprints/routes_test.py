class TestRoot(object):

    """Test the application root route."""

    def test_content(self, client):
        """Root route returns expected test."""
        rv = client.get('/')
        assert b'wpt dashboard' in rv.data
