from scrapy import Spider
from scrapy_splash import SplashRequest
from scrapy.selector import Selector

from .cyfra import znajdzCyfreKontrolna
from .script import clear_list, find_missing_books
from ..items import KsiegiItem
import logging

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
logging.getLogger().addHandler(console_handler)

lua_script = """
function main(splash, args)
    assert(splash:go(args.url))
    
  while not splash:select('input#kodWydzialuInput') do
    splash:wait(0.1)
  end

    local input1_selector = "input#kodWydzialuInput"
    local input2_selector = "input#numerKsiegiWieczystej"
    local input3_selector = "input#cyfraKontrolna"

    local input1 = splash:select(input1_selector)
    assert(input1:send_keys(args.values['kod']))
    assert(splash:wait(0))
    
    local input2 = splash:select(input2_selector)
    assert(input2:send_keys(args.values['numer']))
    assert(splash:wait(0))
    
    local input3 = splash:select(input3_selector)
    assert(input3:send_keys(args.values['cyfraKontrolna']))
    assert(splash:wait(0))
    
    local button_selector = "button#wyszukaj"

    assert(splash:select(button_selector):mouse_click())

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
        # missingBooks = find_missing_books()
        # for numb in missingBooks:
        for numb in range(67500, 68500):
            numerKsiegi = str(numb).zfill(8)

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

        requestPayload = response.request.__dict__['_meta']['splash']['args']['values']
        ksiegaPayload = requestPayload['kod'] + '/' + requestPayload['numer'] + '/' + requestPayload['cyfraKontrolna']

        try:
            numerKsiegi = Selector(text=daneKsiegi).xpath(
                '//*[@id="content-wrapper"]/div/div[3]/div[1]/div[2]/div/text()').get().strip()
        except (AttributeError, TypeError):
            errorInfo = " ".join(clear_list(Selector(text=daneKsiegi).xpath(
                '//*[@id="content-wrapper"]/div/div[2]/div/p//text()').getall()))
            wrongKsiega = KsiegiItem()
            wrongKsiega['numerKsiegi'] = ksiegaPayload
            wrongKsiega['errorMessage'] = errorInfo
            yield wrongKsiega
        except Exception as e:
            self.logger.error(f"Error at numerKsiegi during {ksiegaPayload},{e.__class__}, {e.__doc__}")
            return
        try:
            polozenie = clear_list(Selector(text=daneKsiegi).xpath(
                '//*[@id="content-wrapper"]/div/div[3]/div[6]/div[2]/div/descendant-or-self::*/text()').getall())
        except Exception as e:
            self.logger.error(f"Error at polozenie during {ksiegaPayload},{e.__class__}, {e.__doc__}")
            return

        try:
            wlasciciel = clear_list(Selector(text=daneKsiegi).xpath(
                '//*[@id="content-wrapper"]/div/div[3]/div[7]/div[2]/div/descendant-or-self::*/text()').getall())
        except Exception as e:
            self.logger.error(f"Error at wlasciciel during {ksiegaPayload},{e.__class__}, {e.__doc__}")
            return

        numeryDzialek = []
        try:
            typKsiegi = Selector(text=daneKsiegi).xpath(
                '//*[@id="content-wrapper"]/div/div[3]/div[2]/div[2]/div/text()').get()
            if "GRUNTOWA" in typKsiegi:
                tr_elements = Selector(text=tresciKsiegi).xpath('//tr[td[contains(., "Numer działki")]]')
                for tr in tr_elements:
                    numer = tr.xpath('.//td[@class="csBDane"]/text()').get()
                    numeryDzialek.append(numer)
        except Exception as e:
            self.logger.error(f"Error at numeryDzialek during {ksiegaPayload},{e.__class__}, {e.__doc__}")
            return

        pelnaKsiega = KsiegiItem()
        pelnaKsiega['numerKsiegi'] = numerKsiegi
        pelnaKsiega['polozenieDzialki'] = polozenie
        pelnaKsiega['wlascicielKsiegi'] = wlasciciel
        pelnaKsiega['numeryDzialek'] = numeryDzialek

        yield pelnaKsiega
