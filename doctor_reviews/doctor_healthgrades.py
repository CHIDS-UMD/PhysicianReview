import pandas as pd
from datetime import datetime
import time
import os
import random
import requests
from scrapy.http import TextResponse
from pprint import pprint
from datetime import datetime
import time
import json
import argparse

HEADERS = {
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    # "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36",
    'User-Agent': 'Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36',
    "Accept-Encoding": "gzip,deflate,sdch",
    # "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,zh-TW;q=0.2",
}

# HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36',}



def process_Json(response):
    xpath = './/script[@type="text/javascript"]//text()'
    selectors = response.xpath(xpath)
    js_data = [i for i in selectors.extract()[3].split('\n')  if '= {' in i]
    js_data = {t[0].strip(): json.loads(t[1][:-1]) for t in [i.split(' = ') for i in js_data]}
    return js_data

    
def process_Pes(Pes):
    d = {}
    Pes_Model = Pes['model']
    overall = Pes_Model['overall']
    for item in ['responseCount','reviewCount','actualScore','roundedScore',]:
        d[item] = overall[item]
        
    d['score_aggregates'] = Pes_Model["surveyDistribution"]['aggregates']
    d['lastSurveyDate'] = Pes_Model['lastSurveyDate']
    d['cards'] = Pes_Model['cards']
    # at most 20 reviews
    d['reviews'] = Pes['model']['comments']['results']

    return d


def process_viewModel(viewModel):
    cols = ['npi', 'pwid', 'entityType', 'websiteUrl', 'logoUrl', 'imageUrl', 
     'providerUrl', 'displayName', 'displayNamePossessive', 'providerDisplayFullName', 
     'age', 'genderString', 'badges', 'languages', 
     'hasAutoBiography', 'aboutMe', 'aboutMeVideoUrl', 
     'aboutProvider', 'description', 'generatedbiography', 'autoBiography', 'cityNameAndState', 
     'officeLocations', 'officePhone', 'acceptsNewPatients', 
     'availability', 
     'practicingSpecialties', 'medicalSpecialty', 
     'awardsAndRecognitions', 'boardCertifications', 'insuranceAccepted', 
     'isPrimaryLocationMalpracticeCollected', 'malpractices', 
     'sponsorName', 'boardActions', 'memberships', 
     'education', 'hospitals', 'hasConditions', 
     'hasProcedures',  'existingPatientPhone', 
     'readStoryScrolloffset', 'sanctions', 
     'shouldShowVideoContent', 'showPatientVolumeData', 'showVisitingSection', 
     'specialtyHasClinicalFocus', 'specialtyHeaderText', 'suppressCertifications',
     'suppressSurveys', 'syndication', 'testimonies', 'uconnectEnvironment', 'writeMd',
     'conditionsAndProcedures', 'clinicalFocusItems',]
    d = {}
    for i in cols:
        d[i] = viewModel[i]
    return d


def process_xpath(response):
    item2xpath = {
        'biography': './/*[@data-qa-target="premium-biography"]//text()',
        # 'strengths_item': './/li[@class="provider-strengths-item"]',
        # 'rate_score': './/p[@class="score"]//text()',
        # 'rate_num': './/p[@class="survey-count"]//text()',
        # 'rate_details':'.//table[@class="rating-table"]//text()', 
    }
    itemselector2value = {
        'biography': lambda x: x.extract(),
        #  'strengths_item': lambda x: [''.join(i.xpath('.//div//text()').extract()[:4]) for i in x],
        # 'rate_score': lambda x: float(x.extract()[0]), 
        # 'rate_num': lambda x: int(x.extract()[1]), 
        # 'rate_details': lambda x: x.extract(), 
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


def scrapy_healthgraders_physician(url):


    # as we cannot use Download Middleware in Scrapy, requests are used here instead.
    r = requests.get(url, headers = HEADERS)
    # load the text to scrapy-type response
    response = TextResponse(r.url, body = r.text, encoding = 'utf-8')

    js_data = process_Json(response)
    # print([i for i in js_data])
    Pes = js_data['pageState.pes']
    d1 = process_Pes(Pes)

    viewModel = js_data['pageState.viewModel']
    d2 = process_viewModel(viewModel)


    d3 = process_xpath(response)

    d = dict(d1, **d2, **d3)
    return d


def get_healthgraders_reviews(url, reviewCount):

    review_url = 'https://www.healthgrades.com/api4/providerprofile/comments'
    pwid = url.split('-')[-1]
    # pagenum = 1
    perPage = 10
    
    L = []
    
    for pagenum in range(1, int(reviewCount / perPage) + 2):
        forms = {
            'currentPage': str(pagenum), 
            'includeAllAnswers': 'ture',
            'perPage': str(perPage),
            'pwid': pwid.upper(),
            'sortOption': str(1)
        }
        print(forms)

        r = requests.post(review_url, headers = HEADERS, data = forms)

        d = r.json().get('results', [])
        if type(d) != list: d = []
        print(len(d))
        L.append(d)
        
    return sum(L, [])


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('--input_path', type = str)
    parser.add_argument('--start',  type=int, default=0, help=' ')
    parser.add_argument('--length', type=int, default=10000, help=' ')
    parser.add_argument('--chunk', type=int, default=100, help=' ')
    parser.add_argument('--angry_flag', type=int, default=3, help=' ')
    args = parser.parse_args()
    
    # db_connection_str = 'mysql+pymysql://root:@localhost:3306/doctorinfo_sample?charset=utf8'
    # db_connection = create_engine(db_connection_str)
    # df = pd.read_sql('SELECT * FROM physicians_sample', con=db_connection)

    start = args.start 
    end = args.length + start
    # angry_flag = args.angry_flag

    input_path = args.input_path
    
    df = pd.read_pickle(input_path) 
    
    name = 'healthgrades'
    url_list = df[-df[name].isna()][name].to_list()
    # print(df.shape)
    # print(len(url_list))
    end = len(url_list) if len(url_list) < end else end
    url_list = url_list[start:end]

    OutputFolder = input_path.replace('.p', '_s{}_e{}'.format(start, end)).replace('Data', 'Output')
    Error_Output_path = os.path.join(OutputFolder, name +   '_errorlog.txt') # Output_path.replace('.p', '_errorlog.txt')
    
    if not os.path.exists(OutputFolder): 
        os.makedirs(OutputFolder)
    
    
    print('Read doctor list from: \t{}\nSave results to:\t{}\nSave Error Log to:\t{}'.format(input_path, OutputFolder, Error_Output_path))

    
    # save the results to tmp_path
    pkl_files = [os.path.join(OutputFolder, i) for i in os.listdir(OutputFolder) if '.p' in i]
    for file in pkl_files:
        print('\n' + file )

    # get collected urls:
    # if len(pkl_files) > 0:
    #     collected_NPIs = pd.concat([pd.read_pickle(file) for file in pkl_files])['url'].to_list()
    # else:
    #     collected_NPIs = []

    # print('\n\nCollected url {}'.format(len(collected_NPIs)))

    # flag = 0
    # angry_flag = int(angry_flag)
    # L = []

    chunk = int(args.chunk)
    ## Loop the doctors
    error_list = []


    # old_chunk_id = -1 # the first one is 0.
    # empty_Result = True
    total_sec = 0
    succ_url = 0
    total_start_time = datetime.now()
    for idx, urls in enumerate(url_list):

        # current url's chunk_id
        chunk_id = int(idx / chunk)
        new_s = start + chunk_id*chunk
        new_e = start + (chunk_id+1)*chunk if start + (chunk_id+1)*chunk < end else end
        chunk_name = '{}_s{}_e{}.p'.format(name, new_s, new_e)
        chunk_file = os.path.join(OutputFolder, chunk_name)

        # generate Results
        if idx % chunk == 0:
            # if mean the end, then create a Result.
            print('\n\nChunk {}: Generate the new Result for the new Chunk...'.format(chunk_id))
            if os.path.isfile(chunk_file):
                Result = pd.read_pickle(chunk_file) 
            else:
                cols = ['responseCount', 'reviewCount', 'actualScore', 'roundedScore', 'score_aggregates', 
                        'lastSurveyDate', 'cards', 'reviews', 'npi', 'pwid', 'entityType', 'websiteUrl', 
                        'logoUrl', 'imageUrl', 'providerUrl', 'displayName', 'displayNamePossessive', 
                        'providerDisplayFullName', 'age', 'genderString', 'badges', 'languages', 
                        'hasAutoBiography', 'aboutMe', 'aboutMeVideoUrl', 'aboutProvider', 'description', 
                        'generatedbiography', 'autoBiography', 'cityNameAndState', 'officeLocations', 
                        'officePhone', 'acceptsNewPatients', 'availability', 'practicingSpecialties', 
                        'medicalSpecialty', 'awardsAndRecognitions', 'boardCertifications', 'insuranceAccepted', 
                        'isPrimaryLocationMalpracticeCollected', 'malpractices', 'sponsorName', 'boardActions', 
                        'memberships', 'education', 'hospitals', 'hasConditions', 'hasProcedures', 
                        'existingPatientPhone', 'readStoryScrolloffset', 'sanctions', 'shouldShowVideoContent', 
                        'showPatientVolumeData', 'showVisitingSection', 'specialtyHasClinicalFocus', 
                        'specialtyHeaderText', 'suppressCertifications', 'suppressSurveys', 'syndication', 
                        'testimonies', 'uconnectEnvironment', 
                        'writeMd', 'conditionsAndProcedures', 'clinicalFocusItems', 'biography', 'url', 'clct_time']
                Result = pd.DataFrame(columns = cols)
                # Result.to_pickle(chunk_file)

        # we have a Result now by any cases.
        for url in urls: 
            # case 1
            if url in Result['url'].values:
                # assert url in Result['url'].values
                print('pass URL: {}'.format(url))
                continue 

            # case 2
            
        
            try:
                print('\n\nidx {} & {}: '.format(start + idx, idx) + url)
                doc_info = scrapy_healthgraders_physician(url)
                print('doctor name is: {}'.format(doc_info['providerDisplayFullName']))
            
            except Exception as e:
                # case 2.e1
                print('Encounter the error {}. \nGo to next one...'.format(str(e)))
                error_list.append({'idx':idx, 'url':url, 'error': str(e), 'time': str(datetime.now())})
                pd.DataFrame(error_list).to_csv(Error_Output_path)
                continue

            # need to further explore?
            reviewCount = doc_info['reviewCount']
            print('Reported reviews {} v.s. collected reviews {}'.format(reviewCount, len(doc_info['reviews'])))
            
            if reviewCount > len(doc_info['reviews']):
                print('We need to collect more reviews: {} vs {}'.format(len(doc_info['reviews']), reviewCount))
                reviews = get_healthgraders_reviews(url, reviewCount)  
                commentIds = [i['commentId'] for i in doc_info['reviews']]

                # for ind, commentId in enumerate(commentIds):
                    # print(commentId)
                    # commentId_new = reviews[ind]['commentId']
                    # print(b)
                    # assert commentId == commentId_new

                if len(reviews) != reviewCount:
                    print('Reported reviews {} is not equal to collected reviews {}'.format(reviewCount, len(reviews)))
                    doc_info['reviewCount'] = len(reviews)

                doc_info['reviews'] = reviews
        
            print('reivew number: {}'.format(len(doc_info['reviews'])))
            doc_info['url'] = url
            doc_info['clct_time'] = datetime.now()
            
            try:
                Result2 = Result.append(doc_info, ignore_index=True)
                Result2.to_pickle(chunk_file.replace('.', '_tmp.'))
                Result2 = pd.read_pickle(chunk_file.replace('.', '_tmp.'))
                os.remove(chunk_file.replace('.', '_tmp.'))
            
            except Exception as e:
                # case 2.e2
                print('Writing Errors {}. \nGo to next one...'.format(str(e)))
                error_list.append({'idx':idx,  'url':url, 'error': 'FileIOError:'+str(e), 'time': str(datetime.now())})
                pd.DataFrame(error_list).to_csv(Error_Output_path)
                continue

            Result = Result.append(doc_info, ignore_index=True)
            Result.to_pickle(chunk_file)
            print('Save data to: {}'.format(chunk_file))

            e = datetime.now()
            current_time_usage = e - s
            total_sec += current_time_usage.total_seconds()
            succ_url +=1
            current_time = datetime.now()
            total_time_used = current_time - total_start_time
            print('CurrentTime: {}; Time Used: {}; Succ URL: {}; Avg Time: {}; Total Time {}'.format(current_time, current_time_usage, succ_url, round(total_sec/succ_url, 4), total_time_used) )

            second = random.randrange(3, 6)
            time.sleep(second)
            s = datetime.now()
    
        