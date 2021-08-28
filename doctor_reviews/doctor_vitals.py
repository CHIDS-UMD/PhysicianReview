import pandas as pd
import json
import os
from scrapy.http import TextResponse
from pprint import pprint
import cloudscraper
from datetime import datetime
import time
import json
import argparse
import random

# HEADERS = {
#     "Connection": "keep-alive",
#     "Cache-Control": "max-age=0",
#     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
#     # "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36",
#     'User-Agent': 'Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36',
#     "Accept-Encoding": "gzip,deflate,sdch",
#     # "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,zh-TW;q=0.2",
# }

HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36',}




def scrape_under_cloudflare(url, headers = HEADERS, min_sec = 10):
    print("Request url: {}".format(url))
    
    while True:
        scraper = cloudscraper.create_scraper()
        r = scraper.get(url, headers = headers)
        # load the text to scrapy-type response
        response = TextResponse(r.url, body = r.text, encoding = 'utf-8')

        if 'Cloudflare to restrict access' not in str(response.body.decode()):
            print("\tSucc!!!")
            break
        else:
            print("\tFail...")
            second = random.randrange(min_sec, min_sec + 1)
            time.sleep(second)
            
    return response

def process_Json(response):
    xpath = './/script//text()'
    selectors = response.xpath(xpath)
    js_data = selectors.extract()
    json_str = [i for i in js_data[1].split('};')][0].split('__INITIAL_STATE__=')[-1] + '}'
    
    try:
        js_data = json.loads(json_str)
    except:
        js_data = json_str
        print(js_data)
        
    return js_data


def process_Vitals(url, min_sec = 10):
    
    print('\n=========\nExplore Doctor Profile URL: {}'.format(url))
    response = scrape_under_cloudflare(url, min_sec = min_sec)
    # print('get info from url: {}'.format(url))
    js_data = process_Json(response)
    profile = js_data['profile']

    # fill the data
    profile_data = {}
    for i in [
        # id
        'npi',  'providerid', 'intid', 'entityid_s', 'sponsorid',
        # type
        'display_type', 'profiletype', 'type', 
        # names
        'firstname', 'middlename', 'lastname',  'fullname',  
        # demo
        'gender', 'langspoken',
        # bio
        'about_bio', 'bio_s', 'photourl', 'providerwebsiteurl', 'profileurl','video','quick_facts',
        # practicing,
        'isDentist','is_legacy_provider',  'years_of_experience', 
        'acceptsnewpatients', 'specialty_nimvs', 
        'fallback_specialties', 'fallback_specialty', 'provider_expertise', 
        # awards and certification
        'degreeabbr', 'certifications', 'awards', 'total_awards',
        # education
         'education_nimvs', 
        # hosptial
        'location_nimvs', 'hospital_nimvs','displayhospitals',
        'city', 'state', 'postalcode', 'geolocation', 
        # insurance
        'insurance_facet',  
        # rating and review
        'number_of_ratings', 
        'ratings_per_star', 'rating_score','rating_overview',
        'review_count', 'review_questions', 'recent_reviews',]:

        # print('\n\n'+ i)
        # pprint(profile.get(i, None))
        profile_data[i] = profile.get(i, None)
        
        
    if profile_data['number_of_ratings'] > len(profile_data['recent_reviews']): 
        # keep ascending
        number_of_ratings = profile_data['number_of_ratings'] 
        review_urls = ['{}/reviews?page={}&sort=updated_at_dt%20asc'.format(url, page) 
                       for page in range(1, int(number_of_ratings/12) + 2)]
        profile_data['review_urls'] = review_urls
        
        all_reviews = []
        success_review_urls = []
        for page_idx, review_url in enumerate(review_urls):
            print('\n* Work at page {}'.format(page_idx))
            response = scrape_under_cloudflare(review_url, min_sec = min_sec)
            
            js_data = process_Json(response)
            # print([i for i in js_data])
            reviews = js_data['profile']['reviews']
                
            # all or nothing
            # try:
            #     js_data = process_Json(response)
            #     # print([i for i in js_data])
            #     reviews = js_data['profile']['reviews']
            # except:
            #     print('Failure to parse reviews json from URL: {}'.format(review_url))
            #     continue

            all_reviews = all_reviews + reviews
            print('review number: {}'.format(len(reviews)))
            success_review_urls.append(review_url)
            
        profile_data['review_urls'] = review_urls
        profile_data['success_review_urls'] = success_review_urls
        profile_data['reviews'] = all_reviews
    else:
        profile_data['review_urls'] = []
        profile_data['success_review_urls'] = []
        profile_data['reviews'] = profile_data['recent_reviews']
        
        
    # profile_data['url'] = url
    assert len(profile_data['review_urls']) == len(profile_data['success_review_urls'])
    assert len(profile_data['reviews']) == profile_data['number_of_ratings']
        
        
        
    d = profile_data
    print('\nFor physician {}, get reviews {} vs {}\n======'.format(d['fullname'], len(d['reviews']), d['number_of_ratings']))
    return profile_data


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('--input_path', type = str)
    parser.add_argument('--start',  type=int, default=0, help=' ')
    parser.add_argument('--length', type=int, default=10000, help=' ')
    # parser.add_argument('--angry_flag', type=int, default=3, help=' ')
    parser.add_argument('--chunk', type=int, default=500, help=' ')
    args = parser.parse_args()
    
    start = args.start 
    end = args.length + start
    
    input_path = args.input_path
    df = pd.read_pickle(input_path) 
    
    name = 'vitals'
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
    total_sec = 0
    succ_url = 0
    min_sec = 1
    total_start_time = datetime.now()
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
                cols = ['npi', 'providerid', 'intid', 'entityid_s', 'sponsorid', 'display_type', 'profiletype', 'type', 
                        'firstname', 'middlename', 'lastname', 'fullname', 'gender', 'langspoken', 'about_bio', 'bio_s',
                        'photourl', 'providerwebsiteurl', 'profileurl', 'video', 'quick_facts', 
                        'isDentist', 'is_legacy_provider', 'years_of_experience', 'acceptsnewpatients', 'specialty_nimvs', 
                        'fallback_specialties', 'fallback_specialty', 'provider_expertise', 'degreeabbr', 
                        'certifications', 'awards', 'total_awards', 'education_nimvs', 'location_nimvs', 
                        'hospital_nimvs', 'displayhospitals', 'city', 'state', 'postalcode', 'geolocation',
                        'insurance_facet', 'number_of_ratings', 'ratings_per_star', 'rating_score', 'rating_overview', 
                        'review_count', 'review_questions', 'recent_reviews', 'review_urls', 
                        'success_review_urls', 'reviews', 'url', 'clct_time']
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
                doc_info = process_Vitals(url, min_sec)
                print('doctor name is: {}'.format(doc_info['fullname']))
            
            except Exception as e:
                print('Encounter the error {}. \nGo to next one...'.format(str(e)))
                error_list.append({'idx':idx, 'url':url, 'error': str(e), 'time': str(datetime.now())})
                pd.DataFrame(error_list).to_csv(Error_Output_path)

                if 'Cloudfare' in str(e):
                    print('Cloudfare is angry, stop here!')
                    break
                else:
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
    

    