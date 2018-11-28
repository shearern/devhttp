from setuptools import setup

setup(name='devhttp',
      version='0.0.1', # version string
      description='Development HTTP Server Library',
      url='https://github.com/shearern/devhttp',
      author='Nathan Shearer',
      author_email='shearern@gmail.com',
      license='MIT',
      packages=['devhttp', 'devhttp.endpoints'],
      classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
      ],
      install_requires=[
          'jinja2',
      ],
      )
