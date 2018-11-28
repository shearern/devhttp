from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name='devhttp',
    version='0.0.1', # version string
    description='Development HTTP Server Library',
    long_description=readme(),
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
    include_package_data=True,
    zip_safe=False,  # True?
    )
