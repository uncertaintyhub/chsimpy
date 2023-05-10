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
    extras_requires={
        'qt5': ['PyQt5'],
        'interactive': [
            'ipython~=8.0.0', 'bokeh~=2.4.3',
            'jupyterlab~=3.6.0', 'jupyter-server~=2.1.0',
            'jupyterlab-server~=2.19.0', 'ipykernel~=6.21.0',
            'ipympl~=0.9.0'
        ]
    },
    entry_points={
        'console_scripts': [
            'chsimpy = chsimpy.__main__:main',
        ],
    },
    include_package_data=False,
    zip_safe=False,
    platforms='any',
)
