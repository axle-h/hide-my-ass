from distutils.core import setup

setup(
    name='hidemyass',
    version='0.1',
    packages=['axh', 'axh.proxy'],
    url='axh.pwnz.org',
    license='',
    author='Alex Haslehurst',
    author_email='alex.haslehurst@gmail.com',
    description='Scraper for http://proxylist.hidemyass.com/',
    requires=['beautifulsoup4', 'cssutils', 'html5lib'],
    install_requires=['beautifulsoup4', 'cssutils', 'html5lib']
)