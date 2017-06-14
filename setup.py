from setuptools import setup, find_packages

setup(
    name='wptdash',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask', 'flask-sqlalchemy', 'jsonschema', 'requests',
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest', 'pytest-mock'
    ],
)
