from setuptools import setup, find_packages
exec(open('ansible_inventory_creator/version.py').read())
setup(
  name='ansible_inventory_creator',
  license='MIT',
  version=__version__,
  url='https://github.com/saurabh-hirani/ansible_inventory_creator',
  description=('Python helper library to abstract out common work for creating ansible dynamic inventory scripts'),
  author='Saurabh Hirani',
  author_email='saurabh.hirani@gmail.com',
  packages=find_packages(),
  install_requires=[],
  entry_points = {}
)
