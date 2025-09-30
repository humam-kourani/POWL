import os
from setuptools import setup, find_packages

# Read the requirements from the requirements.txt file
with open('requirements.txt', encoding='utf-8') as f:
    requirements = f.read().splitlines()

# Read the long description from README.md
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()


# Get the version from __init__.py
def get_version():
    with open(os.path.join('powl', '__init__.py'), 'r') as f:
        for line in f:
            if line.startswith('__version__'):
                _, version = line.split("=")
                return version.strip().replace("'", "").replace('"', '')
    raise RuntimeError("Unable to find __version__ string.")


version = get_version()

setup(
    name='powl',
    version=version,
    description='POWL Miner: Process Mining with the Partially Ordered Workflow Language',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Humam Kourani',
    author_email='humam.kourani@gmail.com',
    url='https://github.com/humam-kourani/powl',
    license='AGPL-3.0 license',
    packages=find_packages(),
    include_package_data=True, 
    package_data={
        "powl.visualization.powl.variants.icons": ["*.svg"],
    },
    install_requires=requirements,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],
    keywords='process mining, business process management',
    python_requires='>=3.9',
    # Include any data files (if any)
    # For example: package_data={'your_package': ['data/*.txt']},
    # Or: include_package_data=True  (to include everything in MANIFEST.in)
    # Entry points for command-line scripts (if any)
    # entry_points={
    #     'console_scripts': [
    #         'your_script_name = your_package.module:main_function',
    #     ],
    # },
)
