import os
import requests
import pandas as pd
import time
import requests
from scrapy.http import TextResponse
import json
import html
import argparse
import random
from datetime import datetime
from scrapy.http import HtmlResponse
from selenium import webdriver
import time
from datetime import datetime
from urllib.parse import urlencode


headers = {
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36",
}
        
def get_review(review_selector):
    d = {}
    d['comment'] = review_selector.xpath('.//*[@itemprop="reviewBody"]//span/text()').extract_first()
    d['date'] = review_selector.xpath('.//*[@itemprop="datePublished"]/text()').extract_first()
    d['patientName'] = review_selector.xpath('.//*[@itemprop="author"]/text()').extract_first()
    d['patient_type'] = review_selector.xpath('.//*[@data-test="review-source"]/text()').extract_first()
    d['overallRating'] = review_selector.xpath('.//*[@data-test="stars-svg-wrapper"]/svg/@data-rating').extract_first()
    return d

def get_complete_reviews_from_selenium(url, reviewCount, REVIEW_PER_PAGE, webdriver_path):
    options = webdriver.ChromeOptions()
    # options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    # options.add_argument('--headless')

    driver = webdriver.Chrome(webdriver_path, options=options)
    driver.get(url)
    driver.title
    time.sleep(2)
    
    xpath = './/button[@data-test="reviews-read-more-button"]'
    
    for _ in range(int(reviewCount / REVIEW_PER_PAGE )):
        more_result_button = driver.find_element_by_xpath(xpath)
        print(more_result_button)
        driver.execute_script("arguments[0].click();", more_result_button)
        time.sleep(1)
        
    response = HtmlResponse(driver.current_url, body=driver.page_source, encoding='utf-8')
    reviews = response.xpath('//div[@itemprop="reviews"]')
    reviews = [get_review(i) for i in reviews]
    # len(reviews)
    driver.quit()
    return reviews


def get_physician_info_from_zocdoc_url(ph_url, REVIEW_PER_PAGE, webdriver_path, use_webdriver, proxyapi):
    doc_info = {}
    
    r = requests.get('http://api.scraperapi.com/', params=urlencode({'api_key': proxyapi, 'url': ph_url}))
    # r = requests.get('http://localhost:8050/render.html', params={'url': ph_url, 'wait':0})
    response = TextResponse(r.url, body = r.text, encoding = 'utf-8')
    
    xpath = './/script//text()'

    json_data = response.xpath(xpath).extract()
    # len(json_data)

    json_string = [i for i in json_data if 'window.__REDUX_STATE__ = JSON.parse(' in i][0]
    json_info = [i for i in json_string.split(';\n') if 'window.__REDUX_STATE__ = JSON.parse(' in i][0]

    json_info = json_info.split('JSON.parse(')[1][:-1] # remove prefix
    # x = x[:-1] # remove suffix
    # json_info

    x = json_info
    x = json.loads(x)
    x = json.loads(x) # yes, double json.load operations


    # (1) basic profile
    col = 'profile'; profile = x[col]

    cols = [ 'providerId', 'isMentalHealthProvider',
        'doesProviderHaveInNetworkInsurances', 
        'commonVirtualVisitReasons', 'customDimensions', 'brandingVanityUrl']

    for col in cols: doc_info[col] = profile[col]

    # (2) provider
    profile_data_provider = profile['data']['provider']

    cols = ['isOnlyInNetworkBookable','acceptsNewPatients','errorCode','id','monolithId','status',
        'profileUrl','isApproved','prenominal','postnominal','firstName',
        'lastName','directoryIds', 'approvedFullName', 'nameInSentence','newPatientAppointmentsAsIntroCalls',
        'genderIdentity', 'frontEndCirclePictureUrl', 'frontEndSquarePictureUrl', 'showPhotoWithCircleCss', 'smallPictures',
        'averageRating', 'averageBedsideRating','averageWaitTimeRating',
        'isPreview','personIdentifierSource', 'dataProvidedBy', 'dataProvidedByUrl',
        'mayChargeAdditionalCopay','onlySeesChildren', 'optOutOfRatings', 'previewSummary',
        'highlyRecommendPercentage', 'lowWaitTimedPercentage', 'hasNewPatientAvailability',
        'isTopRebookingProvider', 'hasVirtualLocations',
        'selfPaySettings', 'sellingPoints', 'approvedNonVirtualLocations', 'practices',
        'providerLocations', 'relevantSpecialty', 'mainSpecialtyId','specialties','approvedLocations',
        'statement', 'defaultProcedureId', 'hospitalAffiliations', 'certifications', 'education',
        'memberships', 'typedMemberships','awards','badges', 'languages','npi',
        'inNetworkInsurance','procedures','popularProcedures','isBookable','seo','reviewCount',
        'reviews', 'properties', 'trustedInsuranceRating', 'providerBadges','locations',
        'sortedLocations', 'numVirtualLocations',]

    for col in cols: doc_info[col] = profile_data_provider[col]

    doc_info['complete_reviews'] = False if doc_info['reviewCount'] > len(doc_info['reviews']) else True


    reviewCount = doc_info['reviewCount']

    if doc_info['complete_reviews'] == False and use_webdriver == True:
        reviews = get_complete_reviews_from_selenium(ph_url, reviewCount, 
                                                    REVIEW_PER_PAGE, webdriver_path)

        print('\nReviews: reported {} vs collected {}'.format(reviewCount, len(reviews)))
        if len(reviews) == reviewCount: doc_info['complete_reviews'] = True 
        
        doc_info['reviews'] = reviews
    
    return doc_info


if __name__ == '__main__':

    REVIEW_PER_PAGE = 50
    webdriver_path = '_source/chromedriver_macm1'
 
    parser = argparse.ArgumentParser()

    parser.add_argument('--input_path', type = str)
    parser.add_argument('--start',  type=int, default=0, help=' ')
    parser.add_argument('--length', type=int, default=10000, help=' ')
    parser.add_argument('--chunk', type=int, default=500, help=' ')
    # parser.add_argument('--provider', type=str, default='500', help=' ')
    # parser.add_argument('--api_key', type=str, default='500', help=' ')
    parser.add_argument('--webdriver', type=int, default=0, help=' ')
    parser.add_argument('--angry', type=int, default=10, help=' ')
    parser.add_argument('--proxyapi', type=str, default='None', help=' ')
    args = parser.parse_args()


    angry_flag = args.angry
    proxyapi = args.proxyapi
    
    # provider, api_key
    use_webdriver = True if args.webdriver == 1 else False
    # print(use_webdriver, type(use_webdriver))
    # provider = args.provider
    # api_key = args.api_key
    
    start = args.start 
    end = args.length + start
    
    input_path = args.input_path
    df = pd.read_pickle(input_path) 
    
    name = 'zocdoc'
    url_list = df[-df[name].isna()][name].to_list()
    source_npi_list = df[-df[name].isna()]['NPI'].to_list()
    # print(df.shape)
    # print(len(url_list))
    end = len(url_list) if len(url_list) < end else end
    url_list = url_list[start:end]
    source_npi_list = source_npi_list[start:end]
    assert len(url_list) == len(source_npi_list)


    OutputFolder = input_path.replace('.p', '_s{}_e{}'.format(start, end)).replace('Data', 'Output')
    Error_Output_path = os.path.join(OutputFolder, name +   '_errorlog.txt') # Output_path.replace('.p', '_errorlog.txt')
    
    if not os.path.exists(OutputFolder): 
        os.makedirs(OutputFolder)
    
    # print('Read data from\t{}\nSave results to\t{}\n'.format(input_path, Output_path))
    print('Read doctor list from: \t{}\nSave results to:\t{}\nSave Error Log to:\t{}'.format(input_path, OutputFolder, Error_Output_path))


    # save the results to tmp_path
    pkl_files = [os.path.join(OutputFolder, i) for i in os.listdir(OutputFolder) if '.p' in i]
    for file in pkl_files:
        print('\n' + file )

    chunk = int(args.chunk)
    ## Loop the doctors
    error_list = []

    min_sec = 1
    angry_events = 0
    old_idx = 0
    total_sec = 0
    succ_url = 0
    total_start_time = datetime.now()
    for idx, urls in enumerate(url_list):

        # current url's chunk_id
        chunk_id = int(idx / chunk)
        new_s = start + chunk_id*chunk
        new_e = start + (chunk_id+1)*chunk if start + (chunk_id+1)*chunk < end else end
        chunk_name = '{}_s{}_e{}.p'.format(name, new_s,  new_e)
        chunk_file = os.path.join(OutputFolder, chunk_name)
        source_npi = source_npi_list[idx]

        # generate Results
        if idx % chunk == 0:
            print('\n\nChunk {}: Generate the new Result for the new Chunk...'.format(chunk_id))
            if os.path.isfile(chunk_file):
                Result = pd.read_pickle(chunk_file) 
            else:
                cols = ['providerId', 'isMentalHealthProvider', 'doesProviderHaveInNetworkInsurances', 'commonVirtualVisitReasons', 
                        'customDimensions', 'brandingVanityUrl', 'isOnlyInNetworkBookable', 'acceptsNewPatients', 
                        'errorCode', 'id', 'monolithId', 'status', 'profileUrl', 'isApproved', 'prenominal', 
                        'postnominal', 'firstName', 'lastName', 'directoryIds', 'approvedFullName',
                        'nameInSentence', 'newPatientAppointmentsAsIntroCalls', 'genderIdentity', 
                        'frontEndCirclePictureUrl', 'frontEndSquarePictureUrl', 'showPhotoWithCircleCss',
                        'smallPictures', 'averageRating', 'averageBedsideRating', 'averageWaitTimeRating', 
                        'isPreview', 'personIdentifierSource', 'dataProvidedBy', 'dataProvidedByUrl', 'mayChargeAdditionalCopay', 
                        'onlySeesChildren', 'optOutOfRatings', 'previewSummary', 'highlyRecommendPercentage',
                        'lowWaitTimedPercentage', 'hasNewPatientAvailability', 'isTopRebookingProvider', 'hasVirtualLocations', 
                        'selfPaySettings', 'sellingPoints', 'approvedNonVirtualLocations', 'practices', 'providerLocations', 
                        'relevantSpecialty', 'mainSpecialtyId', 'specialties', 'approvedLocations', 'statement', 'defaultProcedureId',
                        'hospitalAffiliations', 'certifications', 'education', 'memberships', 'typedMemberships', 'awards', 'badges', 
                        'languages', 'npi', 'inNetworkInsurance', 'procedures', 'popularProcedures', 'isBookable', 'seo', 
                        'reviewCount', 'reviews', 'properties', 'trustedInsuranceRating', 'providerBadges', 'locations', 
                        'sortedLocations',  'numVirtualLocations', 'complete_reviews',
                        'url', 'clct_time', 'source_npi']

                Result = pd.DataFrame(columns = cols)
                # Result.to_pickle(chunk_file)

        # we have a Result now by any cases.
        for url in urls:
            # case 1
            if url in Result['url'].values:
                # if url not in Result['url'].values:
                #     print('url is not in collected_NPIs', url)
                #     print(chunk_file)
                # assert url in Result['url'].values
                print('pass URL: {}'.format(url))
                continue 

            # case 2
            s = datetime.now()

            try:
                print('\n\nidx {} & {}: '.format(start + idx, idx) + url)
                doc_info = get_physician_info_from_zocdoc_url(url, REVIEW_PER_PAGE, webdriver_path, use_webdriver, proxyapi)
                print('doctor name is: {}'.format(doc_info['approvedFullName']))
            
            except Exception as e:
                print('Encounter the error {}. \nGo to next one...'.format(str(e)))
                error_list.append({'idx':idx, 'url':url, 'error': str(e), 'time': str(datetime.now())})
                pd.DataFrame(error_list).to_csv(Error_Output_path)
                if old_idx == idx - 1:
                    angry_events += 1
                else:
                    angry_events = 1
                # update old_idx

                print('Last Error occur at idx:', old_idx)
                old_idx = idx
                if angry_events >= angry_flag:
                    raise(ValueError('Stop here, Zocdoc is angry!'))
                
                continue

            doc_info['url'] = url
            doc_info['clct_time'] = datetime.now()
            doc_info['source_npi'] = source_npi
            
            print('Reviews: reported {} vs collected {}'.format(doc_info['reviewCount'], len(doc_info['reviews'])))


            Result2 = Result.append(doc_info, ignore_index=True)
            Result2.to_pickle(chunk_file.replace('.', '_tmp.'))
            Result2 = pd.read_pickle(chunk_file.replace('.', '_tmp.'))
            os.remove(chunk_file.replace('.', '_tmp.'))


            try:
                Result2 = Result.append(doc_info, ignore_index=True)
                Result2.to_pickle(chunk_file.replace('.', '_tmp.'))
                Result2 = pd.read_pickle(chunk_file.replace('.', '_tmp.'))
                os.remove(chunk_file.replace('.', '_tmp.'))
            except:
                # case 2.e2
                print('Writing Errors {}. \nGo to next one...'.format(str(e)))
                error_list.append({'idx':idx,  'url':url, 'error': 'FileIOError:'+str(e), 'time': str(datetime.now())})
                pd.DataFrame(error_list).to_csv(Error_Output_path)
                continue

            Result = Result.append(doc_info, ignore_index=True)
            Result.to_pickle(chunk_file)

            
            print('Save data to: {}'.format(chunk_file))
            
            second = random.randrange(3, 6)
            time.sleep(second)

            e = datetime.now()
            current_time_usage = e - s
            total_sec += current_time_usage.total_seconds()
            succ_url +=1
            current_time = datetime.now()
            total_time_used = current_time - total_start_time
            print('CurrentTime: {}; Time Used: {}; Succ URL: {}; Avg Time: {}; Total Time {}'.format(current_time, current_time_usage, succ_url, round(total_sec/succ_url, 4), total_time_used) )
    