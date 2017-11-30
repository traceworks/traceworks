from setuptools import setup

setup(name='traceworks',
      version='2.0a',
      description='Work with Linux ftrace',
      long_description='This tool helps to parse the traces from the Linux kernel, and help to analyse using custom queries.',
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Topic :: Development :: Performance Analysis',
      ],
      scripts=['bin/traceworks'],
      keywords='ftrace Linux',
      author='Rajarshi Das',
      author_email='drajarshi@in.ibm.com',
      maintainer='Santosh Sivaraj',
      maintainer_email='santosiv@in.ibm.com',
      license='GPL',
      packages=['traceworks'],
      install_requires=[
          'tabulate', 'argparse'
      ],
      include_package_data=True,
      zip_safe=False)
