from setuptools import setup, find_packages

setup(
    name='followme',
    version='0.1',
    author='Lars Kellogg-Stedman',
    author_email='lars@oddbit.com',
    description='A follow-me implementation for dronekit',
    install_requires=[
        'flask',
        'dronekit',
    ],
    license='GPLv3',
    url='https://github.com/larsks/followme',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'followme=followme.main:main',
        ],
    }
)
