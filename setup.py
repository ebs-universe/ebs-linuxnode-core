import setuptools

_requires = [
    'six',
    'setuptools-scm',
    'appdirs',
    'twisted[tls]',
    'SQLAlchemy',
    'arrow',
    'raspi_system',

    # Node Id
    'netifaces',

    # System
    'ifcfg',

    # HTTP Client
    'treq',

    # Event Manager
    'cached_property',
    'pqueue',
]

setuptools.setup(
    name='ebs-linuxnode-core',
    url='',

    author='Chintalagiri Shashank',
    author_email='shashank.chintalagiri@gmail.com',

    description='',
    long_description='',

    packages=setuptools.find_packages(),
    install_requires=_requires,

    setup_requires=['setuptools_scm'],
    use_scm_version=True,

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Operating System :: POSIX :: Linux',
    ],
)
