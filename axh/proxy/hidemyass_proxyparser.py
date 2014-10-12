import datetime
import gzip
import re
import urllib
from bs4 import BeautifulSoup
from axh.proxy.proxyparser import Proxy, ProxyField, ProxyAnon, ProxyProtocol
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


class HideMyAssProxyParser:
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

        if response.info().get('Content-Encoding') == 'gzip':
            buf = response.read()
            body = gzip.decompress(buf)
        else:
            body = response.read()

        soup = BeautifulSoup(body, "html5lib")

        # try to get table by id
        table = soup.find("table", {"id": HideMyAssProxyParser.TableId})

        # try to get table by class
        if table is None:
            table = soup.find("table", HideMyAssProxyParser.TableClass)

        # fall back to just getting the first table
        if table is None:
            table = soup.find("table")

        if table is None:
            raise Exception("No proxy table found")

        # remove all display: none tags
        pattern = re.compile("display\s*:\s*none")
        for tag in table(attrs={"style": pattern}):
            tag.decompose()

        fieldNumbers = dict()
        fieldNumber = 0
        for header in map(lambda x: x.getText(), table.find("thead").find("tr").find_all("th")):
            for field in HideMyAssProxyParser.FieldPatterns:
                if HideMyAssProxyParser.FieldPatterns[field].search(header):
                    fieldNumbers[fieldNumber] = field
            fieldNumber += 1

        self.proxies = list()
        rows = table.find("tbody").findAll("tr")
        for row in rows:
            cells = list(row.findAll("td"))
            values = dict()
            for fieldNumber in fieldNumbers:
                cell = cells[fieldNumber]
                field = fieldNumbers[fieldNumber]
                values[field] = HideMyAssProxyParser.__getField(self, field, cell)
            proxy = Proxy(values)
            self.proxies.append(proxy)

    @staticmethod
    def __getHiddenCssClasses(cssRules):
        pattern = re.compile("\.(.+)")
        hiddenCssClasses = map(
            lambda rule: next((pattern.search(rule.selectorText).group(1) for prop in rule.style if prop.name == "display" and prop.value == "none"), None),
            cssRules)
        return list(filter(lambda rule: rule is not None, hiddenCssClasses))

    def __getField(self, field, cell):
        if field is ProxyField.LastUpdate:
            cellText = cell.getText().replace('\n', '').strip()
            tex = re.search('^(?:(\d+)(?:h\s*))?(?:(\d+)\s*mins?\s*)?(?:(\d+)\s*secs?)?$', cellText)
            hours = int(tex.group(1)) if tex.group(1) is not None else 0
            minutes = int(tex.group(2)) if tex.group(2) is not None else 0
            seconds = int(tex.group(3)) if tex.group(3) is not None else 0
            return self.requestTime + datetime.timedelta(hours = hours, minutes = minutes, seconds = seconds)
        if field is ProxyField.IpAddress:
            style = cell.find("style")
            css = cssutils.parseString(style.getText())
            hiddenCssClasses = HideMyAssProxyParser.__getHiddenCssClasses(css.cssRules)
            #remove style tag
            style.decompose()

            # remove all hidden elements
            for cssClass in hiddenCssClasses:
                for tag in cell.findAll(attrs={'class':cssClass}):
                    tag.decompose()

            return cell.getText().replace('\n', '').strip()
        elif field is ProxyField.Protocol:
            cellText = cell.getText().replace('\n', '').strip()
            for protocol in ProxyProtocol:
                if HideMyAssProxyParser.ProtocolPatterns[protocol].search(cellText) is not None:
                    return protocol
        elif field is ProxyField.Speed or field is ProxyField.ConnectionTime:
            indicator = cell.find("div", "indicator")
            return re.search("width:\s*(\d+)%;", indicator['style'], re.IGNORECASE).group(1)
        elif field is ProxyField.Anon:
            cellText = cell.getText().replace('\n', '').strip()
            for protocol in ProxyAnon:
                if HideMyAssProxyParser.AnonPatterns[protocol].search(cellText) is not None:
                    return protocol
            return ProxyAnon.Low
        else:
            return cell.getText().replace('\n', '').strip()

