import os
from setuptools import setup


version_py = os.path.join(os.path.dirname(__file__), 'firecrestspawner', 'version.py')
version = {}
with open(version_py) as fp:
    exec(fp.read(), version)

with open("README.md", "r", encoding="utf-8") as fp:
    long_description = fp.read()

setup(
    name='firecrestspawner',
    version=version['VERSION'],
    packages=['firecrestspawner'],
    url='https://github.com/eth-cscs/firecrestspawner',
    entry_points={
        "console_scripts": ["firecrestspawner-singleuser=firecrestspawner.singleuser:main"],
    },
    license='BSD 3-Clause',
    description='FirecREST-Spawner: A spawner for Jupyterhub to spawn notebooks using FirecREST.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    # install_requires=[
    #     'jupyterhub==2.0.0',
    #     'pyfirecrest==2.1.0',
    #     'SQLAlchemy==1.3.22',
    #     'oauthenticator==16.0.7'
    # ],
    extras_require={
      "oauth": ['oauthenticator==16.0.7']
    }
)
