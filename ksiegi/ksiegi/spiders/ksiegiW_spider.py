from scrapy import Spider
from scrapy_splash import SplashRequest
from scrapy.selector import Selector
import re

from .cyfra import znajdzCyfreKontrolna
from ..items import KsiegiItem

lua_script = """
function main(splash, args)
    assert(splash:go(args.url))

  while not splash:select('input#kodWydzialuInput') do
    splash:wait(0.1)
  end
      -- CSS selectors for the input fields
    local input1_selector = "input#kodWydzialuInput"
    local input2_selector = "input#numerKsiegiWieczystej"
    local input3_selector = "input#cyfraKontrolna"

    -- Fill the input fields
    local input1 = splash:select(input1_selector)
    assert(input1:send_keys(args.values['kod']))
    assert(splash:wait(0))
    
    local input2 = splash:select(input2_selector)
    assert(input2:send_keys(args.values['numer']))
    assert(splash:wait(0))
    
    local input3 = splash:select(input3_selector)
    assert(input3:send_keys(args.values['cyfraKontrolna']))
    assert(splash:wait(0))
    
    -- CSS selector for the button
    local button_selector = "button#wyszukaj"

    -- Click the button
    assert(splash:select(button_selector):mouse_click())

    -- Wait for some time to let the page process the click
      while not splash:select('button#powrotDoKryterii') do
    splash:wait(0.1)
  end

  local html1= splash:html()
  local html2= ''

   local button_trescKW = splash:select('button#przyciskWydrukZwykly')
   if button_trescKW then
    assert(button_trescKW:mouse_click())
    while not splash:select('input.text1') do
    splash:wait(0.1)
  end
    html2= splash:html()
  end


  return {
  htmlDaneKsiegi=html1,
  htmlTrescKsiegi=html2
  }
end
    """


class KsiegiSpider(Spider):
    name = "ksiegiW"

    def start_requests(self):
        url = "https://przegladarka-ekw.ms.gov.pl/eukw_prz/KsiegiWieczyste/wyszukiwanieKW"
        kodWydzialu = "BI1B"
        # for numb in range(67000, 67030):
        #     numerKsiegi = str(numb).zfill(8)
        numerKsiegi = "00067027"
        cyfraKontrolna = znajdzCyfreKontrolna(kodWydzialu + numerKsiegi)
        payload = {
            "kod": kodWydzialu,
            "numer": numerKsiegi,
            "cyfraKontrolna": cyfraKontrolna,
        }

        yield SplashRequest(url, callback=self.parse, endpoint="execute",
                            args={"lua_source": lua_script,
                                  url: "https://przegladarka-ekw.ms.gov.pl/eukw_prz/KsiegiWieczyste/wyszukiwanieKW",
                                  "values": payload},
                            dont_filter=True)

    def parse(self, response):
        daneKsiegi = response.data['htmlDaneKsiegi']
        tresciKsiegi = response.data['htmlTrescKsiegi']

        numerKsiegi = Selector(text=daneKsiegi).xpath(
            '//*[@id="content-wrapper"]/div/div[3]/div[1]/div[2]/div/text()').get().strip()

        polozenie = re.sub(r'\s+', " ", Selector(text=daneKsiegi).xpath(
            '//*[@id="content-wrapper"]/div/div[3]/div[6]/div[2]/div/p/text()').get().strip())
        print(polozenie)
        wlasciciel = Selector(text=daneKsiegi).xpath(
            '//*[@id="content-wrapper"]/div/div[3]/div[7]/div[2]/div/p/text()').get().strip()

        numeryDzialek = []
        typKsiegi = Selector(text=daneKsiegi).xpath(
            '//*[@id="content-wrapper"]/div/div[3]/div[2]/div[2]/div/text()').get().strip()
        if "GRUNTOWA" in typKsiegi:
            tr_elements = Selector(text=tresciKsiegi).xpath('//tr[td[contains(., "Numer działki")]]')
            for tr in tr_elements:
                numer = tr.xpath('.//td[@class="csBDane"]/text()').get()
                numeryDzialek.append(numer)

        pelnaKsiega = KsiegiItem()
        pelnaKsiega['numerKsiegi'] = numerKsiegi
        pelnaKsiega['polozenieDzialki'] = polozenie
        pelnaKsiega['wlascicielKsiegi'] = wlasciciel
        pelnaKsiega['numeryDzialek'] = numeryDzialek

        yield pelnaKsiega
