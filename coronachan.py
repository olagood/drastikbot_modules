import requests
from bs4 import BeautifulSoup

url = 'https://www.worldometers.info/coronavirus/'

class Module:
    def __init__(self):
        self.commands = ['corona', 'coronachan']
        self.helpmsg = [
            "Usage: .corona or .coronachan",
            " ",
            "Useful stats related to 2019-nCov"]

def main(i, irc):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')

    cases = extract_from_page('Coronavirus Cases:', soup)
    deaths = extract_from_page('Deaths:', soup)
    recovered = extract_from_page('Total Cured:', soup)

    irc.privmsg(
        i.channel,
        (f"\x02Total cases:\x0F {cases} | "
         f"\x02Dead:\x0F \x0304{deaths}\x0F | " 
         f"\x02Recovered:\x0F \x0303{recovered}\x0F | "
         f"\x02Source:\x0F {url}")
    )

def extract_from_page(text, soup):
    return soup.body.find(text=text).parent.parent.find("div", { "class": "maincounter-number" }).find("span").text
