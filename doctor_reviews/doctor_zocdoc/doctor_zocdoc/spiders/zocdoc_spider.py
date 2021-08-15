


from scrapy import Spider, Request
from zocdoc.items import ZocdocItem
from scrapy_splash import SplashRequest


class ZocdocSpider(Spider):
	name = 'zocdoc_spider'
	# allowed_url = ['https://www.zocdoc.com/']	
	# start_urls = ['https://www.zocdoc.com/primary-care-doctors/new-york-46063pm#dr_specialty='
	# + str(i) + '&address=New+York%2C+NY&insurance_carrier=-1&insurance_plan=-1&reason_visit=&gender=-1&language=-1&PatientTypeChild=&offset=' + str(i) '&referrerType=&sort_selection=0&name=&searchQuery=&searchQueryGuid=5e59dbf2-0954-449c-a8ed-ec1aa5cd9953&hasNoSearchResults=false&hospitalid=-1&timeFilter=AnyTime&dayFilter=0&procedureChanged=true&languageChanged=false'
	#    	for i in range(151, 251)]
	start_urls = ['https://www.zocdoc.com/']
	
	
	def parse(self, response): #response is from making a request to start_url
		self.website = 'zocdoc'
		doc_url = [
				'https://www.zocdoc.com/doctor/eric-teller-md-6459',
			    'https://www.zocdoc.com/doctor/anthony-leazzo-do-37929',
				'https://www.zocdoc.com/doctor/matsuko-takeshige-do',
				'https://www.zocdoc.com/doctor/natalie-kahanek-md',
				]


		# self.website = 'ratemds'
		# doc_url =['https://www.ratemds.com/doctor-ratings/3447786/KATHERINE+R.-WILSON-Lawrenceville-GA.html/',
		# 		'https://www.ratemds.com/doctor-ratings/352148/Dr-Jeffrey-Heit-Philadelphia-PA.html',
		# 		'https://www.ratemds.com/doctor-ratings/94311/Dr-Charles+W.-Robinett-Birmingham-AL.html',
		# 		'https://www.ratemds.com/doctor-ratings/2903514/dr-wanda-vaughn-fort+smith-ar.html/',
		# 		'https://www.ratemds.com/doctor-ratings/2461756/Dr-SACHIN+S.-JOGAL-Milwaukee-WI.html/',
		# 		'https://www.ratemds.com/doctor-ratings/3696255/MICHELLE+J.-AN}DERSEN-St.+Johns-MI.html/',
		# 		'https://www.ratemds.com/doctor-ratings/3081449/Dr-JONATHAN+L.-SUSA-Hudson-WI.html',
		# 		'https://www.ratemds.com/doctor-ratings/3213435/dr-amy+m.-olin-indianapolis-in.html/',
		# 		'https://www.ratemds.com/doctor-ratings/3710444/JACQUELINE+K.-SHANNON-Milwaukee-WI.html',]


		for url in doc_url:
			yield SplashRequest(url=url, callback = self.parse_doc_page, args = {"wait": 2}, endpoint = "render.html")
			
	def parse_doc_page(self, response):
		print(response.url)
		
		with open('{}_{}.html'.format(self.website, response.url.split('/')[-1].replace('.html', '')), 'w') as f:
			f.write(str(response.body.decode())) 

