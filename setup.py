import setuptools
import versioneer

with open('README.md', 'r') as fh:
    long_description = fh.read()
with open('requirements.txt', 'r') as fh:
    requirements = fh.read()
    requirements = requirements.replace("git+https://github.com/pvigier/perlin-numpy",
                                        "perlin-numpy @ git+https://github.com/pvigier/perlin-numpy")
    requirements = requirements.splitlines()

setuptools.setup(
    name='chsimpy',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    author='uncertaintyhub',
    author_email='',
    description='Cahn–Hilliard Simulation of Phase Separation in Na2O-SiO2 Glasses',
    url='https://github.com/uncertaintyhub/chsimpy',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['chsimpy'],
    package_dir={'chsimpy': 'chsimpy/'},
    package_data={'chsimpy': ['data/*']},
    classifiers=[
    'Programming Language :: Python :: 3',
    'License :: OSI Approved :: Apache Software License 2.0 (Apache-2.0)',
    'Operating System :: OS Independent',
    ],
    python_requires='>=3.5',
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'chsimpy = chsimpy.__main__:main',
        ],
    },
    include_package_data=False,
    zip_safe=False,
    platforms='any',
)
