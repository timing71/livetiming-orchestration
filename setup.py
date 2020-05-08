from setuptools import setup, find_packages


setup(
    name='livetiming-orchestration',
    description='Timing71 live timing aggregator - orchestration functionality',
    author='James Muscat',
    author_email='jamesremuscat@gmail.com',
    url='https://github.com/timing71/livetiming-orchestration',
    packages=find_packages('src', exclude=["*.tests"]),
    package_dir={'': 'src'},
    long_description='''
    Orchestration functionality for the Timing 71 live timing aggregator.

    This includes the scheduler, service manager, DVR, directory, and
    schedule-assistance tooling.
    ''',
    install_requires=[
        "autobahn[serialization,twisted]>=17.6.2",
        "dictdiffer",
        "google-api-python-client",
        "icalendar",
        "livetiming-core",
        "lzstring==1.0.3",
        "oauth2client",  # Not included in google-api-python-client despite what Google say
        "pyopenssl",
        "python-dotenv",
        "python-twitter",
        "sentry-sdk",
        "service_identity",
        "simplejson",
        "subprocess32",
        "twisted"
    ],
    setup_requires=[
        'pytest-runner',
        'setuptools_scm'
    ],
    use_scm_version=True,
    tests_require=[
        'pytest'
    ],
    entry_points={
        'console_scripts': [
            'livetiming-directory = livetiming.orchestration.directory:main',
            'livetiming-dvr = livetiming.orchestration.dvr:main',
            'livetiming-rectool = livetiming.orchestration.rectool:main',
            'livetiming-schedule = livetiming.orchestration.schedule.__main__:main',
            'livetiming-scheduler = livetiming.orchestration.scheduler:main',
            'livetiming-service-manager = livetiming.orchestration.servicemanager:main',
        ],
    }
)
