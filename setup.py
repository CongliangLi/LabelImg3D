#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages, Command
from sys import platform as _platform
from shutil import rmtree
import sys
import os

here = os.path.abspath(os.path.dirname(__file__))
NAME = 'labelImg3d'
REQUIRES_PYTHON = '>=3.0.0'
REQUIRED_DEP = ['pyqt5', 'lxml']
about = {}

with open(os.path.join(here, 'libs', '__init__.py')) as f:
    exec(f.read(), about)

with open("README.md", "rb", encoding="utf-8") as readme_file:
    readme = readme_file.read().decode("UTF-8")

# historic version
with open("HISTORY.md", "rb", encoding="utf-8") as history_file:
    history = history_file.read().decode("UTF-8")

# OS specific settings
SET_REQUIRES = []
if _platform == "linux" or _platform == "linux2":
    # linux
    print('linux')
elif _platform == "darwin":
    # MAC OS X
    SET_REQUIRES.append('py2app')

required_packages = find_packages()
required_packages.append('labelImg3d')

APP = [NAME + '.py']
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'icons/icon.ico'
}


class UploadCommand(Command):
    """Support setup.py upload."""

    description = readme + '\n\n' + history,

    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            self.status('Fail to remove previous builds..')
            pass

        self.status('Building Source and Wheel (universal) distribution…')
        os.system(
            '{0} setup.py sdist bdist_wheel --universal'.format(sys.executable))

        self.status('Uploading the package to PyPI via Twine…')
        os.system('twine upload dist/*')

        self.status('Pushing git tags…')
        os.system('git tag -d v{0}'.format(about['__version__']))
        os.system('git tag v{0}'.format(about['__version__']))
        # os.system('git push --tags')

        sys.exit()


setup(
    app=APP,
    name=NAME,
    version=about['__version__'],
    description="LabelImg3d is a 3D graphical image annotation tool and label object 3D bounding boxes in images",
    long_description=readme + '\n\n' + history,
    author="Shijie Sun & Congliang Li",
    author_email='congliangli@chd.edu.cn',
    url='http://git.chd.gold:3000/shijie/labelimg3d',
    python_requires=REQUIRES_PYTHON,
    package_dir={'labelImg3d': '.'},
    packages=required_packages,
    # entry_points={
    #     'console_scripts': [
    #         'labelImg=labelImg.labelImg:main'
    #     ]
    # },
    include_package_data=True,
    install_requires=REQUIRED_DEP,
    license="MIT license",
    zip_safe=False,
    keywords='labelImg3d labelTool annotation deeplearning',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.8',
    ],
    # package_data={'data/predefined_classes.txt': ['data/predefined_classes.txt']},
    # options={'py2app': OPTIONS},
    setup_requires=SET_REQUIRES,
    # $ setup.py publish support.
    cmdclass={
        'upload': UploadCommand,
    }
)
