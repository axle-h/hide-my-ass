from abc import ABCMeta, abstractproperty, abstractmethod
import datetime
import gzip
import re
import urllib
from bs4 import BeautifulSoup
from axh.proxy import Proxy, ProxyField, ProxyAnon, ProxyProtocol
import cssutils

__author__ = 'Alex'


class HideMyAssRequest(urllib.request.Request):
    Url = "http://proxylist.hidemyass.com/"
    Accept = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    AcceptEncoding = "gzip"
    AcceptLanguage = "en-GB,en;q=0.8"
    CacheControl = "no-cache"
    Connection = "keep-alive"
    Pragma = "no-cache"
    UserAgent = "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36"

    def __init__(self):
        super().__init__(HideMyAssRequest.Url)
        self.headers['Accept'] = HideMyAssRequest.Accept
        self.headers['Accept-Encoding'] = HideMyAssRequest.AcceptEncoding
        self.headers['Accept-Language'] = HideMyAssRequest.AcceptLanguage
        self.headers['Cache-Control'] = HideMyAssRequest.CacheControl
        self.headers['Connection'] = HideMyAssRequest.Connection
        self.headers['Pragma'] = HideMyAssRequest.Pragma
        self.headers['User-Agent'] = HideMyAssRequest.UserAgent


class HideMyAssProxyScraper:
    TableId = "listable"
    TableClass = "hma-table"

    FieldPatterns = {ProxyField.LastUpdate: re.compile("Last\s*Update", re.IGNORECASE),
                     ProxyField.IpAddress: re.compile("Ip\s*Address", re.IGNORECASE),
                     ProxyField.Port: re.compile("Port", re.IGNORECASE),
                     ProxyField.Country: re.compile("Country", re.IGNORECASE),
                     ProxyField.Speed: re.compile("Speed", re.IGNORECASE),
                     ProxyField.ConnectionTime: re.compile("Connection\s*Time", re.IGNORECASE),
                     ProxyField.Protocol: re.compile("Type", re.IGNORECASE),
                     ProxyField.Anon: re.compile("Anon", re.IGNORECASE)}

    ProtocolPatterns = {ProxyProtocol.Http: re.compile("^HTTP$", re.IGNORECASE),
                        ProxyProtocol.Https: re.compile("^HTTPS$", re.IGNORECASE),
                        ProxyProtocol.Socks: re.compile("socks", re.IGNORECASE)}

    AnonPatterns = {ProxyAnon.Low: re.compile("^Low$", re.IGNORECASE),
                    ProxyAnon.Medium: re.compile("^Medium$", re.IGNORECASE),
                    ProxyAnon.High: re.compile("^High$", re.IGNORECASE),
                    ProxyAnon.HighKa: re.compile("^High\s*\+?KA$", re.IGNORECASE)}

    def __init__(self):
        self.requestTime = datetime.datetime.utcnow()
        request = HideMyAssRequest()
        response = urllib.request.urlopen(request)
        buffer = response.read()
        body = gzip.decompress(buffer) if response.info().get('Content-Encoding') == 'gzip' else buffer

        soup = BeautifulSoup(body, "html5lib")

        # try to get table by id
        # try to get table by class
        # fall back to just getting the first table
        table = soup.find("table", {"id": self.TableId}) or \
                soup.find("table", self.TableClass) or \
                soup.find("table")

        if table is None:
            raise Exception("No proxy table found")

        # remove all display: none tags
        [tag.decompose() for tag in table(attrs={"style": re.compile("display\s*:\s*none")})]

        fields = {i: self.__match_enum(ProxyField, self.FieldPatterns, header, None)
                  for i, header in enumerate(th.getText() for th in table.find("thead").find("tr").find_all("th"))}

        if None in fields.values():
            raise Exception("Missing field")

        self.proxies = [Proxy({field: self.__get_field(field, cell) for field, cell in
                               [(fields[fieldNumber], cells[fieldNumber]) for fieldNumber in fields]})
                        for cells in [list(row.findAll("td")) for row in table.find("tbody").findAll("tr")]]

    @staticmethod
    def __match_enum(enum, patterns, text, default):
        return next((value for value in enum if patterns[value].search(text) is not None), default)

    def __get_field(self, field, cell):
        cell_text = cell.getText().replace('\n', '').strip()

        if field is ProxyField.LastUpdate:
            # Parse time format [{0}h] [{1}min[s]] [{2}sec[s]]
            tex = re.search('^(?:(\d+)(?:h\s*))?(?:(\d+)\s*mins?\s*)?(?:(\d+)\s*secs?)?$', cell_text)
            time = [int(tex.group(i + 1)) if tex.group(i + 1) is not None else 0 for i in range(3)]
            return self.requestTime + datetime.timedelta(hours=time[0], minutes=time[1], seconds=time[2])
        if field is ProxyField.IpAddress:
            # Inline style block used to hide junk elements.
            # Extract all classes with 'display: none' and remove them.
            style = cell.find("style")
            css = cssutils.parseString(style.getText())

            hidden_css_classes = [rule for rule in
                                  [next((re.search("\.(.+)", cssRule.selectorText).group(1) for prop in cssRule.style if
                                         prop.name == "display" and prop.value == "none"), None) for cssRule in
                                   css.cssRules] if
                                  rule is not None]

            # remove style tag, all hidden elements & rebuild cellText now all the hidden stuff is gone
            style.decompose()
            [tag.decompose() for cssClass in hidden_css_classes for tag in cell.findAll(attrs={'class': cssClass})]
            return cell.getText().replace('\n', '').strip()
        elif field is ProxyField.Protocol:
            return self.__match_enum(ProxyProtocol, self.ProtocolPatterns, cell_text, None)
        elif field is ProxyField.Speed or field is ProxyField.ConnectionTime:
            indicator = cell.find("div", "indicator")
            return re.search("width:\s*(\d+)%;", indicator['style'], re.IGNORECASE).group(1)
        elif field is ProxyField.Anon:
            return self.__match_enum(ProxyAnon, self.AnonPatterns, cell_text, ProxyAnon.Low)
        else:
            return cell_text

