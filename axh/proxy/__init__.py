from axh.proxy.hma import HmaProxyScraper

__author__ = 'Alex Haslehurst'


def proxies():
    hma_scraper = HmaProxyScraper()
    return hma_scraper.proxies