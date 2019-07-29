import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="PyperS",
    version="0.0.1",
    author="Congyue Cui",
    author_email="ccui@princeton.edu",
    description="A toolbox for global full waveform inversion",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/icui/PyperS",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
)