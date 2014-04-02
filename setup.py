# coding=utf-8
import sys
try:
    from setuptools import setup, find_packages
except ImportError:
    import distribute_setup
    distribute_setup.use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='tinymodel',
    version='0.1.4',
    author='Jeff Revesz',
    author_email='jeff.revesz@buzzfeed.com',
    packages=find_packages(),
    test_suite='test',
    install_requires=[
        'nose<2.0.0',
        'pytz==2013b',
        'python-dateutil==2.1',
        'inflection==0.2.0',
        'caliendo==v2.0.5'
    ],
)
