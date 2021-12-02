from setuptools import setup, find_packages

setup(
    name='niescraper',
    version='1.0.0',
    description='Parses SoC workflows and aggregates the QoS attributes',
    author='Elias Keis',
    author_email='git-commits@elkei.de',
    packages=find_packages(exclude=['tests', 'tests.*', 'docs', 'lazy']),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': ['niescraper=niescraper.app:run'],
    },
    install_requires=[
        'playsound',
        'selenium',
        'pytz',
        'aioconsole'
    ],
    tests_require=[
        'pytest'
    ]
)
