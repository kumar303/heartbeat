import os

from setuptools import setup, find_packages


setup(name='heartbeat',
      version='1.0.0',
      description="Keeps the box alive.",
      long_description='',
      author='Kumar McMillan',
      author_email='kumar.mcmillan@gmail.com',
      license='',
      url='',
      include_package_data=True,
      classifiers=[],
      entry_points="""
          [console_scripts]
          heartbeat = heartbeat:main
          """,
      packages=find_packages(exclude=['tests']),
      install_requires=[ln.strip() for ln in
                        open(os.path.join(os.path.dirname(__file__),
                                          'requirements/prod.txt'))
                        if not ln.startswith('#')])
