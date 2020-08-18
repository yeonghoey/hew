import ast
import re

from setuptools import find_packages, setup


setup(
    name='hew',
    version='0.0.1',
    description='a tool for hewing media',
    keywords='video audio tool',
    url='https://github.com/yeonghoey/hew',

    author='Yeongho Kim',
    author_email='yeonghoey@gmail.com',

    packages=find_packages(),
    package_data={'hew': ['hew.png']},

    entry_points={
        'console_scripts': [
            'hew=hew.__main__:cli',
        ]
    },

    install_requires=[
        'Click==6.7',
        'google-cloud-speech==1.3.2',
        'moviepy==1.0.3',
        'pyperclip==1.6.0',
        'PyQt5==5.10',
        'pysrt==1.1.1',
        'python-vlc==3.0.102',
        'pytimeparse==1.1.7',
        'pytube3>=9.5.0',
    ],

    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.6',
    ],
)
