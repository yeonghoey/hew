import ast
import re
from setuptools import find_packages, setup


def extract_version(content):
    m = re.search(r'__version__\s+=\s+(.*)', content)
    s = m.group(1)
    return str(ast.literal_eval(s))


with open('hew/__init__.py', 'rb') as f:
    content = f.read().decode('utf-8')
    version = extract_version(content)


setup(
    name='hew',
    version=version,
    description='a tool for hewing media',
    keywords='video audio tool',
    url='https://github.com/yeonghoey/hew',

    author='Yeongho Kim',
    author_email='yeonghoey@gmail.com',

    packages=find_packages(),

    entry_points={
        'console_scripts': [
            'hew=hew.__main__:cli',
        ]
    },

    install_requires=[
        'Click==6.7',
        'google-api-python-client==1.6.4',
        'moviepy==0.2.3.2',
        'pyperclip==1.6.0',
        'PyQt5==5.10',
        'pysrt==1.1.1',
        'python-vlc==3.0.102',
        'pytimeparse==1.1.7',
        'pytube==8.0.2',
        'SpeechRecognition==3.8.1',
    ],

    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.6',
    ],
)
