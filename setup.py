import os
from setuptools import setup, find_packages, Extension
from version import version

project_path = os.path.dirname(os.path.realpath(__file__))
requirements_file = '{}/requirement.txt'.format(project_path)

with open(requirements_file) as f:
    content = f.readlines()
install_requires = [x.strip() for x in content]

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name='osw-confidence-metric',
    version=version,
    author='Sujata Misra',
    author_email='sujatam@gaussiansolutions.com',
    description='Calculates the confidence score of a given geojson area',
    long_description=long_description,
    project_urls={
        'Documentation': 'https://github.com/TaskarCenterAtUW/TDEI-python-lib-confidence-metric/blob/main/README.md',
        'GitHub': 'https://github.com/TaskarCenterAtUW/TDEI-python-lib-confidence-metric',
        'Changelog': 'https://github.com/TaskarCenterAtUW/TDEI-python-lib-confidence-metric/blob/main/CHANGELOG.md'
    },
    long_description_content_type='text/markdown',
    url='https://github.com/TaskarCenterAtUW/TDEI-python-lib-confidence-metric',
    install_requires=install_requires,
    packages=find_packages(where='src'),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',
    package_dir={'': 'src'},
)