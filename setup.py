runtime_requirements = [
    'pyinfra~=1.2.1'
]

from setuptools import setup

setup(
    install_requires=runtime_requirements,
    version='0.1.0',
    name='terminus',  # This is just the distribution package name
                      # which has nothing to do with the module name.
                      # For that, refer to the subdir names under src/
    author='Mark S. Maglana',
    author_email='mmaglana@gmail.com',
    url='https://github.com/relaxdiego/terminus',
    python_requires='~=3.7',
    package_dir={'': 'src'},
    packages=[
        'terminus',
    ],

    # https://pypi.org/classifiers/
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
    ]
)
