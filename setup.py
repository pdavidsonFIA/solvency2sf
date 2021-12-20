import setuptools
#from os import listdir

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open('requirements.txt', 'r') as f:
    dependencies = f.read().splitlines()

data_path = ''

setuptools.setup(
    name="solvency2sf",
    version="0.0.23",
    author="Peter Davidson",
    author_email="peterjd41@gmail.com",
    description="Solvency 2 Standard Formula",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pdavidsonFIA/solvency2sf",
    project_urls={
        "Bug Tracker": "https://github.com/pdavidsonFIA/solvency2sf/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Financial and Insurance Industry"
    ],
    # package_dir={"": "src"},
    # packages=setuptools.find_packages(where="src"),
    packages=setuptools.find_packages(include=['solvency2sf', 'solvency2sf.*']),
    python_requires='>=3.6',
    # install_requires=['pandas>=1.0.0', 'numpy>=1.0.0'],
    include_package_data=True,
    # package_data={'data': ['solvency2sf/corr_h_uw.csv']},
    #package_data={'data': [data_path + item for item in listdir('solvency2sf{}'.format(data_path))]},
    install_requires=dependencies,
)
