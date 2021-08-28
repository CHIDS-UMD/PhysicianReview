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
import time


# we need headers to disguise our bot as a browser

# headers = {
#     "Connection": "keep-alive",
#     "Cache-Control": "max-age=0",
#     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
#     "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36",
# }

headers = {'User-Agent': 'Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36',}




def decompose_jQuery(d, x):
    # d is input dict; x is the original list
    for k, v in d.items():
        if not v:
            # print('Empty v at {}'.format(k))
            pass
        
        elif type(v) == dict:
            # print('Is a dictionary')
            out = decompose_jQuery(v, x)
            if type(out) == dict: out = decompose_jQuery(out, x) 
            d[k] = out
        
        elif type(v) == list:
            if len(v) == sum([type(v_e) == dict for v_e in v]):
                # print('Is a list of dictionaries')
                out_list = []
                for v_e in v:
                    out = decompose_jQuery(v_e, x) 
                    if type(out) == dict: out = decompose_jQuery(out, x) 
                    out_list.append(out)
                d[k] = out_list
            
        elif type(v) == str:
            # print('v is a string')
            if v[0] == '$' and v in x:
                # print(v)
                # print(v, 'v is start from $')
                d[k] = x[v]
            else:
                pass
        else:
            pass
        
    return d


def process_reviewxpath(review):


    item2xpath = {
        'image': './/img[@class="photo-box-img"]/@src',
        'user_name': './/*[@class="user-display-name"]/text()',
        'user_location':'.//*[@class="user-location responsive-hidden-small"]/b/text()',
        'friends':'.//*[@class="friend-count responsive-small-display-inline-block"]//b/text()',
        'reviews':'.//*[@class="review-count responsive-small-display-inline-block"]//b/text()',
        'rate_score': './/img[@class="offscreen"]/@alt',
        'date': './/*[@class="rating-qualifier"]/text()',
        'comment': './/p[@lang="en"]//text()',
    }

    itemselector2value = {
        'image': lambda x: x.extract()[0] if len(x) == 1 else None,
        'user_name': lambda x: x.extract()[0] if len(x) == 1 else None,
        'user_location': lambda x: x.extract()[0] if len(x) == 1 else None,
        'friends': lambda x: x.extract()[0] if len(x) == 1 else None,
        'reviews': lambda x: x.extract()[0] if len(x) == 1 else None,
        'rate_score': lambda x: x.extract()[0] if len(x) == 1 else None,
        'date': lambda x: x.extract()[0].strip() if len(x) == 1 else None,
        'comment': lambda x: html.unescape('\n'.join(x.extract())).replace('\xa0',''),
    }

    d = {}
    for item, xpath in item2xpath.items():
        # print('\n')
        # print(item)
        selectors = review.xpath(xpath)#.extract()
        values = itemselector2value[item](selectors)
        d[item] = values
        # print(values)
        
        
    return d


def process_xpath(response):
    item2xpath = {
        'blocked_reviews_num': './/*[@class="ysection not-recommended-reviews review-list-wide"]/h3/text()',
        'blocked_reviews': './/*[@class="ysection not-recommended-reviews review-list-wide"]//*[@class="review review--with-sidebar"]',
        'removed_reviews_num': './/*[@class="ysection removed-reviews"]/h3/text()',
        'removed_reviews': './/*[@class="ysection removed-reviews"]//*[@class="review review--with-sidebar"]',
    }


    itemselector2value = {
        'blocked_reviews_num': lambda x: int(x.extract()[0].strip().split(' ')[0]),
        'blocked_reviews': lambda x: [process_reviewxpath(review) for review in x],
        'removed_reviews_num': lambda x: int(x.extract()[0].strip().split(' ')[0]) if len(x) == 1 else 0,
        'removed_reviews': lambda x: [process_reviewxpath(review) for review in x],
    }


    d = {}
    for item, xpath in item2xpath.items():
        # print('\n')
        # print(item)
        selectors = response.xpath(xpath)#.extract()
        values = itemselector2value[item](selectors)
        d[item] = values
        # print(values)
    return d


def get_blocked_reviews_from_ph_url(ph_url):
    doc_name = ph_url.split('/')[-1]
    start = 0
    url = 'https://www.yelp.com/not_recommended_reviews/{}?not_recommended_start={}'.format(doc_name, start)
    r = requests.get(url, headers = headers)
    print(r.url)
    # load the text to scrapy-type response
    response = TextResponse(r.url, body = r.text, encoding = 'utf-8')


    d = process_xpath(response)
    blocked_reviews_num = int(d['blocked_reviews_num'])
    if blocked_reviews_num <= 10:
        return d
    else:
        for i in range(1, int((blocked_reviews_num)/10) + 1):
            start = i*10
            # print(start)
            url = 'https://www.yelp.com/not_recommended_reviews/{}?not_recommended_start={}'.format(doc_name, start)
            r = requests.get(url, headers = headers)
            print(r.url)
            # load the text to scrapy-type response
            response = TextResponse(r.url, body = r.text, encoding = 'utf-8')
            new_d = process_xpath(response)
            d['blocked_reviews'] += new_d['blocked_reviews']
            # d['removed_reviews'] += new_d['removed_reviews']
            # print()
            # print(new_d['removed_reviews'])
            time.sleep(1)
        return d


def get_physician_info_from_yelp_url(ph_url):

    physician_info = {}
    
    # profile url
    url = ph_url
    r = requests.get(url, headers = headers)
    response = TextResponse(r.url, body = r.text, encoding = 'utf-8')
    xpath = './/script//text()'
    selectors = response.xpath(xpath)
    js_list = selectors.extract()
    l = [i for i in js_list]

    # aim 1: get common questions
    # idx = 14
    json_list = [i for i in l if 'mainEntity' in i]
    if len(json_list) == 1:
        json_string = json_list[0]
        d = json.loads(json_string)
    else:
        d = {}
    physician_info['Questions'] = d

    
    # aim 2: get reviewCount
    json_list = [i for i in l if 'LocalBusiness' in i and 'name' in i]
    if len(json_list) == 1:
        json_string = json_list[0]
        d = json.loads(json_string)
        if 'aggregateRating' in d:
            reviewCount = d['aggregateRating']['reviewCount']
        else:
            reviewCount = 0
    else:
        reviewCount = 0
    physician_info['reviewCount'] = reviewCount


    # aim 3: get physician basic information
    # idx = 19
    # json_string = l[idx]
    json_string = [i for i in l if 'ROOT_QUERY' in i][0]
    x = json_string.replace('<!--', '').replace('-->', '')
    # x = x.replace('&quot;', '"')
    x = html.unescape(x)
    # print(x)
    x = json.loads(x)

    # aim 3.1: business photos
    BusinessPhotos = [[i for i in x[i].values() if 'http' in i]  for i in x if '$BusinessPhoto' in i]
    BusinessPhotos = [i[0] for i in BusinessPhotos  if len(i) == 1] 
    physician_info['BusinessPhotos'] = BusinessPhotos

    # aim 3.2: get buzid info
    root = x['ROOT_QUERY']
    root = decompose_jQuery(root, x)
    business_col = [i for i in root if 'business' in i][0]
    buzid = root[business_col]['id']

    cols = ['verifiedLicenses',
    # '__typename',
    'name',
    # 'categoryGroups',
    'alias',
    # 'externalResources',
    'menuVerbiage',
    # 'yelpMenu',
    'categories',
    # 'serviceUpdateSummary',
    'location',
    # 'serviceArea',
    # 'messaging',
    #'meteredPhoneNumber',
    'phoneNumber',
    # 'shouldHideContactInfoForMultilocationBusinessesExperiment',
    # 'jobPricing',
    'operationHours',
    'consumerAlert',
    # 'organizedProperties({"clientPlatform":"WWW"})',
    'healthInspections',
    'isCommunityQuestionsEnabled',
    'communityQuestions({"first":2})',
    'rating',
    'authoritativeAttributes',
    'containerBusiness',
    # 'map({"height":180,"width":315})',
    # 'map({"height":150,"width":315})',
    'serviceArea({"userType":"consumer"})',
    # 'media', 'buzPhoto'
    'reviewCount',
    'claimability({"useConsumerClaimability":true})',
    'claimability',
    'hasClaimReminderForCurrentUser',
    'alternateNames',
    'priceRange',
    'logo',
    'closedUntil',
    'primaryPhoto',
    'specialties',
    'history',]

    for col in cols:
        physician_info[col] = buzid[col]

    # aim 3.3: get seo info 
    seo_id = root['seoMetadata']['id']
    # [i for i in seo_id]
    # seo_id['__typename']
    bizDetail_col = [i for i in seo_id if 'bizDetails' in i][0]
    bizDetails = seo_id[bizDetail_col]

    bizDetails_id = bizDetails['id']

    cols_second = ['pageTitle', 'metaDescription' ]
    for col in cols_second:
        physician_info[col] = bizDetails_id[col]

    # aim 4: get encid and good reviews
    encid = [i for i in root if 'business' in i][0]
    encid = encid.split(':')[-1].split('"')[1]
    physician_info['encid'] = encid
    
    L = []
    for i in range(int((reviewCount)/10) + 1):
        start = i * 10
        url = 'https://www.yelp.com/biz/{}/review_feed?rl=en&q=&sort_by=date_desc&start={}'.format(encid, start)
        r = requests.get(url, headers = headers)
        print(r.url)
        # load the text to scrapy-type response
        response = TextResponse(r.url, body = r.text, encoding = 'utf-8')

        reviews = response.json()
        L.extend(reviews['reviews'])
        time.sleep(1)

    physician_info['reviews_detailed'] = L

    # aim 5: get blocked reivews
    time.sleep(1)
    d = get_blocked_reviews_from_ph_url(ph_url)
    for k, v in d.items(): physician_info[k] = v
    
    return physician_info


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('--input_path', type = str)
    parser.add_argument('--start',  type=int, default=0, help=' ')
    parser.add_argument('--length', type=int, default=10000, help=' ')
    parser.add_argument('--angry_flag', type=int, default=10, help=' ')
    parser.add_argument('--chunk', type=int, default=500, help=' ')
    args = parser.parse_args()
    

    angry_flag = args.angry_flag

    start = args.start 
    end = args.length + start
    
    input_path = args.input_path
    df = pd.read_pickle(input_path) 
    
    name = 'yelp'
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
                cols = ['Questions', 'reviewCount', 'BusinessPhotos', 'verifiedLicenses', 'name', 'alias', 'menuVerbiage', 
                        'categories', 'location', 'phoneNumber', 'operationHours', 'consumerAlert', 'healthInspections', 
                        'isCommunityQuestionsEnabled', 'communityQuestions({"first":2})', 'rating', 'authoritativeAttributes', 
                        'containerBusiness', 'serviceArea({"userType":"consumer"})', 'claimability({"useConsumerClaimability":true})', 
                        'claimability', 'hasClaimReminderForCurrentUser', 'alternateNames', 'priceRange', 'logo', 'closedUntil', 
                        'primaryPhoto', 'specialties', 'history', 'pageTitle', 'metaDescription', 'encid', 'reviews_detailed',
                        'blocked_reviews_num', 'blocked_reviews', 'removed_reviews_num', 'removed_reviews', 
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
                doc_info = get_physician_info_from_yelp_url(url)
                print('doctor name is: {}'.format(doc_info['name']))
            
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
                    raise(ValueError('Stop here, Yelp is angry!'))
                
                continue

            doc_info['url'] = url
            doc_info['clct_time'] = datetime.now()
            doc_info['source_npi'] = source_npi
            
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

            print('Good    Reviews: reported {} vs collected {}'.format(doc_info['reviewCount'], len(doc_info['reviews_detailed'])))
            print('Blocked Reviews: reported {} vs collected {}'.format(doc_info['blocked_reviews_num'], len(doc_info['blocked_reviews'])))
            print('Removed Reviews: reported {} vs collected {}'.format(doc_info['removed_reviews_num'], len(doc_info['removed_reviews'])))

            print('Save data to: {}'.format(chunk_file))
            
            second = random.randrange(6, 8)
            time.sleep(second)

            e = datetime.now()
            current_time_usage = e - s
            total_sec += current_time_usage.total_seconds()
            succ_url +=1
            print('Time Used: {}; Succ URL: {}; Avg Time: {}'.format(current_time_usage, succ_url, round(total_sec/succ_url, 4)) )
    