from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in pibicard/__init__.py
from pibicard import __version__ as version

setup(
	name="pibicard",
	version=version,
	description="cardDAV Frappe App",
	author="pibiCo",
	author_email="pibico.sl@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
