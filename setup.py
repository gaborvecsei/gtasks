from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="gt",
    version="0.1",
    packages=["gt"],
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "gt = gt.gt_cli:main"]
    }
)
