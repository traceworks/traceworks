from setuptools import setup

setup(name='traceworks',
      version='1.0',
      description='Work with Linux ftrace',
      long_description='This tool helps to parse the traces from the Linux kernel, and help to analyse using custom queries.',
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 2.7',
        'Topic :: Development :: Performance Analysis',
      ],
      scripts=['bin/traceworks'],
      keywords='ftrace Linux',
      author='Santosh Sivaraj',
      author_email='santosiv@in.ibm.com',
      license='IPL',
      packages=['traceworks'],
      install_requires=[
          'tabulate', 'argparse'
      ],
      include_package_data=True,
      zip_safe=False)
