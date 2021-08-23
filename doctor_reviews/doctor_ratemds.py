import cloudscraper
import requests
import pandas as pd
import re
import json
import requests
from scrapy.http import TextResponse
from pprint import pprint
import cloudscraper
import time
import os
import pandas as pd
import json
import argparse
import random
from datetime import datetime


headers = {
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36",
}
min_sec = 0


def scrape_under_cloudflare_with_2captcha(url, 
                                          headers = headers, 
                                          min_sec = 0, 
                                          provider = None,
                                          api_key = None):
    print("Request url: {}".format(url))
    
    while True:
        scraper = cloudscraper.create_scraper(
          interpreter='nodejs',
          captcha={
            'provider': provider,
            'api_key': api_key,
          }
        )
        try:
            r = scraper.get(url, headers = headers, timeout = 10)
            response = TextResponse(r.url, body = r.text, encoding = 'utf-8')
            print("\tSucc!!!")
            break
            
        except:
            print("\tFail...")
            second = random.randrange(min_sec, min_sec + 1)
            time.sleep(second)
            
    return response


def get_reviews_from_ph_url(ph_url, ratingCount, headers, min_sec, provider,  api_key):
    L = []
    for page in range(int((ratingCount-1) / 10) + 1):
        # print(page)
        review_url = '{}?json=true&page={}'.format(ph_url, page)


        # url = review_url
        # print(url)
        response = scrape_under_cloudflare_with_2captcha(review_url, 
                                                         headers = headers, 
                                                         min_sec = min_sec, 
                                                         provider = provider,
                                                         api_key = api_key)
        # have a look at its body
        # print(str(response.body.decode()))
        reviews = response.json()['results']
        print('\tGet Reviews {} from last url.'.format(len(reviews)))
        L = L + reviews
    return L


def get_physician_info_from_ratemd_url(ph_url, headers, min_sec, provider, api_key):

    doc_info = {}


    response = scrape_under_cloudflare_with_2captcha(ph_url, 
                                                        headers = headers, 
                                                        min_sec = min_sec, 
                                                        provider = provider,
                                                        api_key = api_key)
    
    xpath = './/script//text()'
    selectors = response.xpath(xpath)

    js_texts = selectors.extract()
    js_texts = [i for i in js_texts]

    # step 1:
    json_string = [i for i in js_texts if 'aggregateRating' in i][0]
    # print(json_string)
    data = json.loads(json_string)


    ratingCount = int(data['aggregateRating']['ratingCount'])

    for col in ['address', 'image', 'name', 'telephone']:
        doc_info[col] = data[col]
        
    for col in ['bestRating', 'ratingCount', 'ratingValue']:
        doc_info[col] = float(data['aggregateRating'][col])

    # step 2:
    # idx = 19
    json_string = [i for i in js_texts if 'window.DATA.Header_props = JSON.parse(' in i][0]
    string_clean = json_string.split(";\n")[1].split(' = JSON.parse(')[1][:-1]
    # string_clean

    x = string_clean
    x = json.loads(x)
    doctor_json = json.loads(x)['doctor']
    for k, v in doctor_json.items():
        doc_info[k] = v

    reviews = get_reviews_from_ph_url(ph_url, ratingCount, headers, min_sec, provider,  api_key )
    doc_info['reviews'] = reviews

    return doc_info

    
if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('--input_path', type = str)
    parser.add_argument('--start',  type=int, default=0, help=' ')
    parser.add_argument('--length', type=int, default=10000, help=' ')
    parser.add_argument('--chunk', type=int, default=500, help=' ')
    parser.add_argument('--provider', type=str, default='500', help=' ')
    parser.add_argument('--api_key', type=str, default='500', help=' ')
    args = parser.parse_args()
    
    # provider, api_key
    provider = args.provider
    api_key = args.api_key
    
    start = args.start 
    end = args.length + start
    
    input_path = args.input_path
    df = pd.read_pickle(input_path) 
    
    name = 'ratemds'
    url_list = df[-df[name].isna()][name].to_list()
    # print(df.shape)
    # print(len(url_list))
    end = len(url_list) if len(url_list) < end else end
    url_list = url_list[start:end]


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
    for idx, urls in enumerate(url_list):

        # current url's chunk_id
        chunk_id = int(idx / chunk)
        new_s = start + chunk_id*chunk
        new_e = start + (chunk_id+1)*chunk if start + (chunk_id+1)*chunk < end else end
        chunk_name = '{}_s{}_e{}.p'.format(name, new_s,  new_e)
        chunk_file = os.path.join(OutputFolder, chunk_name)

        # generate Results
        if idx % chunk == 0:
            print('\n\nChunk {}: Generate the new Result for the new Chunk...'.format(chunk_id))
            if os.path.isfile(chunk_file):
                Result = pd.read_pickle(chunk_file) 
            else:
                cols = ['address', 'image', 'name', 'telephone', 'bestRating', 'ratingCount', 
                        'ratingValue', 'slug', 'created', 'modified', 'id', 'doctor_locations', 
                        'specialty', 'specialty_name', 'specialty_html_title', 'specialty_html_title_plural',
                        'gender', 'url', 'facet_url', 'verified', 'images', 'full_name', 'full_name_specialty', 
                        'rating', 'city_name', 'owner_id', 'location', 'bio', 'accepting_patients', 
                        'insurance_plans', 'doctor_schools', 'doctor_languages', 'doctor_specialties', 
                        'doctor_expertises', 'doctor_insurance_plans', 'awards', 'publications', 
                        'rating_concierge_enabled', 'rating_emails_subscribed', 'rating_emails', 
                        'doctor_ad_specialties', 'doctor_ad_cities', 'ad_specialties_cap', 'ad_cities_cap', 
                        'DEPRECATED_hide_ratings', 'sample_rating_comment', 'sample_rating_pk', 
                        'customer_id', 'appointments_available', 'appointments_enabled', 'appointments_email', 
                        'appointments_message', 'appointments_thank_you_message', 'accepting_virtual_appointments',
                        'gallery_enabled', 'ratings_disabled', 'specialty_name_plural', 'force_login', 'vanity_specialty',
                        'doctor_alert', 'rankings', 'geocode_address', 'location_url', 'reviews', 
                        'url', 'clct_time']

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
                doc_info = get_physician_info_from_ratemd_url(url, headers, min_sec, provider, api_key)
                print('doctor name is: {}'.format(doc_info['name']))
            
            except Exception as e:
                print('Encounter the error {}. \nGo to next one...'.format(str(e)))
                error_list.append({'idx':idx, 'url':url, 'error': str(e), 'time': str(datetime.now())})
                pd.DataFrame(error_list).to_csv(Error_Output_path)
                continue

            doc_info['url'] = url
            doc_info['clct_time'] = datetime.now()

            
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

            print('Reviews: reported {} vs collected {}'.format(int(doc_info['ratingCount']), len(doc_info['reviews'])))
  
            print('Save data to: {}'.format(chunk_file))
            
            second = random.randrange(3, 6)
            time.sleep(second)

            e = datetime.now()
            print('Time Used:', e - s )
    