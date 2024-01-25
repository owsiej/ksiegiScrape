from scrapy import Spider
from scrapy_splash import SplashRequest
from scrapy.selector import Selector
import base64

from .cyfra import znajdzCyfreKontrolna
from .script import clear_list, find_missing_books_by_book_file, find_missing_books_by_error_file
from ..items import KsiegiItem
import logging

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
logging.getLogger().addHandler(console_handler)

lua_script = """
function main(splash, args)
    assert(splash:go(args.url))
   
   local function wait_for_element(selector)
        while not splash:select(selector) do
            splash:wait(0.1)
        end
    end
    
  wait_for_element('input#kodWydzialuInput')

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

    wait_for_element('button#powrotDoKryterii') 

  local html1= splash:html()
  local html2= ''
  local html3= ''
  local html4= ''
 
   local button_trescKW = splash:select('button#przyciskWydrukZwykly')
   if button_trescKW then
    assert(button_trescKW:mouse_click())
    wait_for_element('input.text1')
    html2= splash:html()
    else
      return {
  htmlDaneKsiegi=html1,
  htmlTrescKsiegi=html2,
  htmlRoszczeniaKsiegi=html3,
  htmlHipotekaKsiegi=html4
  }
  end

   local button_roszczeniaKW = splash:select('input[value="Dział III"]')
    assert(button_roszczeniaKW:mouse_click())
    assert(splash:wait(0.1))
    wait_for_element('td.csTTytul')
    while splash:select('td.csTTytul'):text()~="DZIAŁ III - PRAWA, ROSZCZENIA I OGRANICZENIA" do
    splash:wait(0.5)
    end
    html3= splash:html()
    assert(splash:wait(0.1))
    
    local button_hipotekaKW = splash:select('input[value="Dział IV"]')
    assert(button_hipotekaKW:mouse_click())
    assert(splash:wait(0.1))
    wait_for_element('td.csTTytul')
    while splash:select('td.csTTytul'):text()~="DZIAŁ IV - HIPOTEKA" do
    splash:wait(0.5)
    end
    html4= splash:html()
    assert(splash:wait(0.1))
    


  return {
  htmlDaneKsiegi=html1,
  htmlTrescKsiegi=html2,
  htmlRoszczeniaKsiegi=html3,
  htmlHipotekaKsiegi=html4
  }
end
    """


class KsiegiSpider(Spider):
    name = "ksiegiW"

    def start_requests(self):
        url = "https://przegladarka-ekw.ms.gov.pl/eukw_prz/KsiegiWieczyste/wyszukiwanieKW"
        kodWydzialu = "BI1B"
        handle_httpstatus_list = [400]
        # missingBooks = find_missing_books_by_book_file()
        # for numb in missingBooks:
        for numb in range(2500, 3000):
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

        requestPayload = response.request.__dict__['_meta']['splash']['args']['values']
        ksiegaPayload = requestPayload['kod'] + '/' + requestPayload['numer'] + '/' + requestPayload['cyfraKontrolna']

        if response.status == 400:
            self.logger.error(f'Received a 400 status code for KSIĘGA: {ksiegaPayload}')
            return
        daneKsiegi = response.data['htmlDaneKsiegi']
        tresciKsiegi = response.data['htmlTrescKsiegi']
        roszczeniaKsiegi = response.data['htmlRoszczeniaKsiegi']
        hipotekaKsiegi = response.data['htmlHipotekaKsiegi']

        # imgdata = base64.b64decode(response.data['image'])
        # filename = f"{requestPayload['numer']}.png"
        # with open(filename, 'wb') as f:
        #     f.write(imgdata)

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
            return
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

        try:
            typKsiegi = " ".join(clear_list(Selector(text=daneKsiegi).xpath(
                '//*[@id="content-wrapper"]/div/div[3]/div[2]/div[2]/div/text()').getall()))
        except Exception as e:
            self.logger.error(f"Error at typKsiegi during {ksiegaPayload},{e.__class__}, {e.__doc__}")
            return

        dzialki = []

        trNumbersDzialki = Selector(text=tresciKsiegi).xpath('//tr[td[contains(., "Numer działki")]]')
        trUrlsDzialki = Selector(text=tresciKsiegi).xpath('//tr[td[contains(., "Identyfikator działki")]]')

        if len(trNumbersDzialki) == len(trUrlsDzialki):
            for trNumb, trUrl in zip(trNumbersDzialki, trUrlsDzialki):
                numer = trNumb.xpath('.//td[@class="csBDane"]/text()').get()
                url = trUrl.xpath('.//a/@href').get()
                dzialki.append({
                    "numerDzialki": numer,
                    "linkDzialki": url
                })
        else:
            for trNumb in trNumbersDzialki:
                numer = trNumb.xpath('.//td[@class="csBDane"]/text()').get()
                dzialki.append({
                    "numerDzialki": numer,
                })

        trRoszczenia = Selector(text=roszczeniaKsiegi).xpath(
            '//td[@class="csPodTytulClean"]').get()
        roszczenia = 'Tak' if trRoszczenia else "Nie"

        hipoteki = []

        trRodzajHipoteki = Selector(text=hipotekaKsiegi).xpath('//tr[td[contains(., "Rodzaj hipoteki")]]')
        trSumaHipoteki = Selector(text=hipotekaKsiegi).xpath('//tr[td[contains(., "Suma (słownie), waluta")]]')

        for trRodzaj, trSuma in zip(trRodzajHipoteki, trSumaHipoteki):
            rodzaj = trRodzaj.xpath('.//td[@class="csBDane"]/text()').get()
            suma = trSuma.xpath('.//td[2]/b/text()').get()
            hipoteki.append({
                "rodzajHipoteki": rodzaj,
                "sumaHipoteki": suma
            })

        pelnaKsiega = KsiegiItem()
        pelnaKsiega['numerKsiegi'] = numerKsiegi
        pelnaKsiega['polozenieDzialki'] = polozenie
        pelnaKsiega['wlascicielKsiegi'] = wlasciciel
        pelnaKsiega['dzialki'] = dzialki
        pelnaKsiega['typKsiegi'] = typKsiegi
        pelnaKsiega['roszczeniaPrawaOgraniczeniaKsiegi'] = roszczenia
        pelnaKsiega['hipotekaKsiegi'] = hipoteki

        yield pelnaKsiega
