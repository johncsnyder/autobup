from setuptools import setup

setup(
    name='autobup',
    author='John Snyder',
    author_email='johncsnyder@gmail.com',
    entry_points = {
        'console_scripts': ['autobup=autobup.__init__:main']
    }
)