from setuptools import setup

setup(
    name='burnaby',
    version='0.0.dev1',
    author='Alex Kurkin',
    author_email='',
    description='A/B testing utility',
    url='https://github.com/sqweptic/burnaby',
    project_urls = {
        "Bug Tracker": 'https://github.com/sqweptic/burnab/issues'
    },
    keywords='abtesting, ab, a/b tests, experimenting platform, statistical experiment, sampling, split testing',
    packages=[
        'burnaby',
        'burnaby.charts'
    ],
    package_dir={
        'burnaby': 'src',
    },
    install_requires=[
        'ipython==7.25.0',
        'jupyter==1.0.0',
        'matplotlib==3.4.2',
        'notebook==6.4.0',
        'numpy==1.21.0',
        'pandas==1.2.5',
        'scipy==1.7.0',
        'seaborn==0.11.1',
        'statsmodels==0.12.2'
    ],
)