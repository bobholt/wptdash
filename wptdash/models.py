""" SQLAlchemy Model definitions. """
import enum

from wptdash.database import db


class BuildStatus(enum.Enum):

    """
    Enum representing possible Travis build statuses.

    Subclasses `enum.Enum`
    """

    PENDING = 1
    PASSED = 2
    FIXED = 3
    BROKEN = 4
    FAILED = 5
    STILL_FAILING = 6

    @classmethod
    def from_string(cls, status):
        """
        Convert input string to enum value.

        Arguments:
        status -- The string representing a status

        Returns enum value corresponding to status string
        """
        return getattr(cls, status.replace(' ', '_').upper())


class JobStatus(enum.Enum):

    """
    Enum representing possible Travis job statuses.

    Subclasses `enum.Enum`
    """

    PASS = 1
    FAIL = 2
    ERROR = 3
    TIMEOUT = 4

    @classmethod
    def from_string(cls, status):
        """
        Convert input string to enum value.

        Arguments:
        status -- The string representing a status

        Returns enum value corresponding to status string
        """
        return getattr(cls, status.upper())


class PRStatus(enum.Enum):

    """
    Enum representing possible GitHub pull request statuses.

    Subclasses `enum.Enum`
    """

    OPEN = 1
    CLOSED = 2

    @classmethod
    def from_string(cls, status):
        """
        Convert input string to enum value.

        Arguments:
        status -- The string representing a status

        Returns enum value corresponding to status string
        """
        return getattr(cls, status.upper())


class TestStatus(enum.Enum):

    """
    Enum representing possible ci_stability test statuses.

    Subclasses ``enum.Enum``
    """

    PASS = 1
    FAIL = 2
    OK = 3
    TIMEOUT = 4
    ERROR = 5
    NOTRUN = 6
    CRASH = 7

    @classmethod
    def from_string(cls, status):
        """
        Convert input string to enum value.

        Arguments:
        status -- The string representing a status

        Returns enum value corresponding to status string
        """
        return getattr(cls, status.upper())


# Many to Many Table joining ``GitHubUser`` and ``PullRequest``
# SQLAlchemy auto-deletes from this table. See:
# http://docs.sqlalchemy.org/en/latest/orm/basic_relationships.html#deleting-rows-from-the-many-to-many-table
USER_PR = db.Table('user_pr', db.metadata,
                   db.Column('user_id',
                             db.Integer,
                             db.ForeignKey('github_user.id')),
                   db.Column('pull_id',
                             db.Integer,
                             db.ForeignKey('pull_request.id')))


class Build(db.Model):

    """
    Table containing CI builds.

    Subclasses ``wptdash.app.db.Model``
    """

    __tablename__ = 'build'

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    pull_request_id = db.Column(db.Integer,
                                db.ForeignKey('pull_request.id'))
    commit_id = db.Column(db.String, db.ForeignKey('commit.sha'))
    status = db.Column(db.Enum(BuildStatus), nullable=False)
    started_at = db.Column(db.TIMESTAMP(timezone=True), nullable=False)
    finished_at = db.Column(db.TIMESTAMP(timezone=True))

    jobs = db.relationship('Job', back_populates='build')
    pull_request = db.relationship('PullRequest',
                                   back_populates='builds')
    commit = db.relationship('Commit', back_populates='builds')


class Commit(db.Model):

    """
    Table containing Git Commits.

    Subclasses ``wptdash.app.db.Model``
    """

    __tablename__ = 'commit'

    sha = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('github_user.id'),
                        nullable=False)

    builds = db.relationship('Build', back_populates='commit')
    pull_requests = db.relationship('PullRequest',
                                    back_populates='head_commit')
    user = db.relationship('GitHubUser', back_populates='commits')


class GitHubUser(db.Model):

    """
    Table containing GitHub Users.

    Subclasses ``wptdash.app.db.Model``
    """

    __tablename__ = 'github_user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

    prs_watching = db.relationship('PullRequest', secondary=USER_PR,
                                   back_populates='watchers')
    merges = db.relationship('PullRequest', back_populates='merger')
    repositories = db.relationship('Repository', back_populates='owner')
    commits = db.relationship('Commit', back_populates='user')


class Job(db.Model):

    """
    Table containing Travis build jobs.

    Subclasses ``wptdash.app.db.Model``
    """

    __tablename__ = 'job'

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Float)
    build_id = db.Column(db.Integer, db.ForeignKey('build.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'),
                           nullable=False)
    state = db.Column(db.Enum(JobStatus), nullable=False)
    error_message = db.Column(db.Text)
    allow_failure = db.Column(db.Boolean, nullable=False)
    started_at = db.Column(db.TIMESTAMP(timezone=True), nullable=False)
    finished_at = db.Column(db.TIMESTAMP(timezone=True))

    build = db.relationship('Build', back_populates='jobs')
    product = db.relationship('Product', back_populates='jobs')
    tests = db.relationship('JobResult', back_populates='job')


class JobResult(db.Model):

    """
    Association Table joining ``Job`` and ``Test``.

    See `SQLAlchemy Docs <http://docs.sqlalchemy.org/en/latest/orm/basic_relationships.html#association-object>` for more on this pattern.

    Subclasses ``wptdash.app.db.Model``
    """

    __tablename__ = 'job_result'

    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), primary_key=True)
    test_id = db.Column(db.Text, db.ForeignKey('test.id'), primary_key=True)
    iterations = db.Column(db.Integer)

    job = db.relationship('Job', back_populates='tests')
    test = db.relationship('Test', back_populates='jobs')
    statuses = db.relationship('StabilityStatus')


class Product(db.Model):

    """
    Table containing stability product targets (e.g. browsers/versions).

    Subclasses ``wptdash.app.db.Model``
    """

    __tablename__ = 'product'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

    jobs = db.relationship('Job', back_populates='product')


class PullRequest(db.Model):

    """
    Table containing GitHub Pull Requests.

    Subclasses ``wptdash.app.db.Model``
    """

    __tablename__ = 'pull_request'

    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.Enum(PRStatus), nullable=False)
    merged = db.Column(db.Boolean, nullable=False)
    merged_by = db.Column(db.Integer, db.ForeignKey('github_user.id'))
    mirror_url = db.Column(db.String)
    head_sha = db.Column(db.String, db.ForeignKey('commit.sha'))
    base_sha = db.Column(db.String, db.ForeignKey('commit.sha'))
    head_repo_id = db.Column(db.Integer, db.ForeignKey('repository.id'))
    base_repo_id = db.Column(db.Integer, db.ForeignKey('repository.id'))
    created_at = db.Column(db.TIMESTAMP(timezone=True), nullable=False)
    updated_at = db.Column(db.TIMESTAMP(timezone=True))
    merged_at = db.Column(db.TIMESTAMP(timezone=True))

    builds = db.relationship('Build', back_populates='pull_request')
    merger = db.relationship('GitHubUser', foreign_keys=[merged_by],
                             back_populates='merges')
    head_commit = db.relationship('Commit', foreign_keys=[head_sha],
                                  back_populates='pull_requests')
    base_commit = db.relationship('Commit', foreign_keys=[base_sha])
    head_repository = db.relationship('Repository',
                                      foreign_keys=[head_repo_id],
                                      back_populates='pull_requests')
    base_repository = db.relationship('Repository',
                                      foreign_keys=[base_repo_id])
    watchers = db.relationship('GitHubUser', secondary=USER_PR,
                               back_populates='prs_watching')


class Repository(db.Model):

    """
    Table containing references to repository sources of pull requests.

    Subclasses ``wptdash.app.db.Model``
    """

    __tablename__ = 'repository'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('github_user.id'),
                         nullable=False)

    owner = db.relationship('GitHubUser', back_populates='repositories')
    pull_requests = db.relationship('PullRequest',
                                    back_populates='head_repository')


class StabilityStatus(db.Model):

    """
    Table containing stability statuses for tests in jobs

    Subclasses ``wptdash.app.db.Model``
    """

    __tablename__ = 'stability_status'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, nullable=False)
    test_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum(TestStatus))
    count = db.Column(db.Integer)

    db.ForeignKeyConstraint(['job_id', 'test_id'],
                            ['job_result.job_id', 'job_result.test_id'])


class Test(db.Model):

    """
    Table containing stability tests and their sub/parent tests.

    Makes use of the `Adjacency List Pattern <http://docs.sqlalchemy.org/en/latest/orm/self_referential.html>`_.

    Subclasses ``wptdash.app.db.Model``
    """

    __tablename__ = 'test'

    id = db.Column(db.Text, primary_key=True)
    parent_id = db.Column(db.Text, db.ForeignKey('test.id'))

    subtests = db.relationship('Test',
                               backref=db.backref('parent',
                                                  remote_side=[id]))
    jobs = db.relationship('JobResult', back_populates='test')


def get_or_create(session, model, defaults=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.iteritems())
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        return instance, True
