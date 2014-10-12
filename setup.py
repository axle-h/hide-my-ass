from distutils.core import setup

setup(
    name='hidemyass',
    version='0.1',
    packages=['axh', 'axh.hidemyass'],
    url='axh.pwnz.org',
    license='',
    author='Alex Haslehurst',
    author_email='alex.haslehurst@gmail.com',
    description='Parser for http://proxylist.hidemyass.com/',
    requires=['beautifulsoup4', 'cssutils'],
    install_requires=['beautifulsoup4', 'cssutils']
)