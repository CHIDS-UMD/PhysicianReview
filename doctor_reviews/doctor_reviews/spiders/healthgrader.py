import scrapy
import json
from pprint import pprint

class HealthgraderSpider(scrapy.Spider):
    name = 'healthgrader'
    # allowed_domains = ['healthgrader.com']
    # start_urls = ['http://healthgrader.com/']

    def start_requests(self):
        url = 'https://www.healthgrades.com/providers/ella-gray-3mpy5'
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):

        review_url = 'https://www.healthgrades.com/api4/providerprofile/comments'
        pwid = response.url.split('-')[-1]
        pagenum_list = [1]
        for pagenum in pagenum_list:

            forms = {
                'currentPage': str(pagenum), 
                'includeAllAnswers': 'ture',
                'perPage': str(10),
                'pwid': pwid.upper(),
                'sortOption': str(1)
            }
            print(forms)
            yield scrapy.FormRequest(review_url, 
                                     method = 'POST', 
                                     formdata = forms, 
                                     callback = self.parse_reviews)
    
    def parse_reviews(self, response):

        print('\n\n==================\n\n')
        pprint(response.headers)
        print('\n\n==================\n\n')
        pprint(response.json())

