#!/usr/bin/env python
# coding: utf-8

from __future__ import print_function

from setuptools import setup
from setuptools.command.build_py import build_py

import glob
import sys
import os
import platform
import stat
import tarfile

try:
    from io import BytesIO
    from urllib.request import urlopen, URLError
except ImportError:
    from StringIO import StringIO as BytesIO
    from urllib2 import urlopen, URLError

sys.path.insert(0, os.path.abspath('gr'))
try:
    import vcversioner
except ImportError:
    import _version
    _wrapper_version = _version.__version__
else:
    _wrapper_version = vcversioner.find_version(version_module_paths=[os.path.join("gr", "_version.py")]).version
import runtime_helper
sys.path.pop(0)

# TODO: load runtime version from file
_runtime_version = runtime_helper.required_runtime_version()


__author__ = "Florian Rhiem <f.rhiem@fz-juelich.de>, Christian Felder <c.felder@fz-juelich.de>"
__version__ = _wrapper_version
__copyright__ = """Copyright (c) 2012-2015: Josef Heinen, Florian Rhiem,
Christian Felder and other contributors:

http://gr-framework.org/credits.html

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

The GR framework can be built with plugins that use code from the
following projects, which have their own licenses:

- MuPDF - a lightweight PDF and XPS viewer (AFPL)
- Ghostscript - an interpreter for the PostScript language and for PDF (AFPL)
- FFmpeg - a multimedia framework (LGPL / GPLv2)

"""

_long_description = None
try:
    with open("README.rst", 'r') as fd:
        _long_description = fd.read()
except IOError as e:
    print("WARNING: long_description could not be read from file. Error message was:\n",
          e, file=sys.stderr)


class DownloadBinaryDistribution(build_py):
    @staticmethod
    def detect_os():
        if sys.platform == 'darwin':
            return 'Darwin'
        if sys.platform == 'win32':
            return 'Windows'
        if sys.platform.startswith('linux'):
            release_file_names = glob.glob('/etc/*-release')
            release_info = '\n'.join([open(release_file_name).read() for release_file_name in release_file_names])
            if '/etc/os-release' in release_file_names:
                if 'ID=ubuntu' in release_info:
                    return 'Ubuntu'
                if 'ID=debian' in release_info:
                    return 'Debian'
            if '/etc/redhat-release' in release_file_names:
                if 'release 7' in release_info:
                    return 'CentOS'
            return 'Linux'
        return None

    @staticmethod
    def detect_architecture():
        is_64bits = sys.maxsize > 2**32
        if is_64bits:
            return 'x86_64'
        return 'i686'

    def run(self):
        """
        Downloads, unzips and installs GKS, GR and GR3 binaries.
        """
        if runtime_helper.load_runtime(silent=True) is None:
            version = _runtime_version
            operating_system = DownloadBinaryDistribution.detect_os()
            if operating_system is not None:
                arch = DownloadBinaryDistribution.detect_architecture()

                # download binary distribution for system
                distribution_url = 'https://gr-framework.org/downloads/gr-{version}-{os}-{arch}.tar.gz'.format(
                    version=version,
                    os=operating_system,
                    arch=arch
                )
                response = urlopen(distribution_url)
                if response.getcode() != 200:
                    raise URLError('GR runtime not found on: {}'.format(distribution_url))
                # wrap response as file-like object
                tar_gz_data = BytesIO(response.read())
                # extract shared libraries from downloaded zip archive
                base_path = os.path.join(os.path.abspath(os.path.dirname(__file__)))
                with tarfile.open(fileobj=tar_gz_data) as tar_gz_file:
                    for member in tar_gz_file.getmembers():
                        tar_gz_file.extract(member, os.path.join(os.path.abspath(os.path.dirname(__file__))))
                        # libraries need to be moved from gr/lib/ to gr/
                        if os.path.dirname(member.name) == 'gr/lib':
                            if 'plugin' in os.path.basename(member.name):
                                os.rename(os.path.join(base_path, member.name), os.path.join(base_path, 'gr/lib', os.path.basename(member.name)))
                            else:
                                os.rename(os.path.join(base_path, member.name), os.path.join(base_path, 'gr', os.path.basename(member.name)))
                if sys.platform == 'darwin':
                    # GKSTerm.app needs to be moved from gr/Applications to gr/
                    os.rename(os.path.join(base_path, 'gr', 'Applications', 'GKSTerm.app'), os.path.join(base_path, 'gr', 'GKSTerm.app'))

        if runtime_helper.load_runtime(silent=False) is None:
            raise RuntimeError("Unable to install GR runtime")
        build_py.run(self)


setup(
    name="gr",
    version=__version__,
    description="Python visualization framework",
    author="Scientific IT Systems",
    author_email="j.heinen@fz-juelich.de",
    maintainer="Josef Heinen",
    license="MIT License",
    keywords="gr",
    url="http://gr-framework.org",
    platforms=["Linux", "OS X", "Windows"],
    install_requires=[
        'numpy >= 1.6',
    ],
    packages=["gr", "gr.pygr", "gr.matplotlib", "gr3", "qtgr", "qtgr.events"],
    package_data={
        'gr': [
            '*.so',
            '*.dll',
            'lib/*.so',
            'lib/*.dll',
            'fonts/*',
            'GKSTerm.app/Contents/*',
            'GKSTerm.app/Contents/*/*',
            'GKSTerm.app/Contents/*/*/*'
        ]
    },
    long_description=_long_description,
    classifiers=[
        'Framework :: IPython',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Multimedia :: Graphics',
        'Topic :: Scientific/Engineering :: Visualization',
    ],
    cmdclass={
        'build_py': DownloadBinaryDistribution
    }
)
