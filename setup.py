from setuptools import setup

with open('README.md') as f:
    readme = f.read()

setup(name='trackscalpel',
    version='0.3',
    description='Split audio files based on Blu-ray MPLS playlists',
    long_description=readme,
    long_description_content_type = 'text/markdown',
    url='http://github.com/michaelburton/trackscalpel',
    author='Michael Burton',
    author_email='michburton@gmail.com',
    license='MIT',
    packages=['trackscalpel', 'trackscalpel.MPLS'],
    entry_points={
        'console_scripts': ['trackscalpel=trackscalpel.trackscalpel:main'],
    },
    install_requires=[
        'numpy',
        'SoundFile',
    ],
    zip_safe=True)
