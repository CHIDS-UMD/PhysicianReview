
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
from twilio.rest import Client
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


# def get_doctor_info(DoctorDF):
#     doctor_infolist = []
#     for _, row in DoctorDF.iterrows():
#         # most results: fistname is before lastname
#         if row['MiddleName'] == None:
#             doctor_info = "{} {} {} {} {} {}".format(row['FirstName'], row['LastName'], 
#                                                   row['Primaryspecialty'], 
#                                                   row['City'], row['State'],
#                                                   row['Zip.Code'])
#         else:
#             doctor_info = "{} {} {} {} {} {} {}".format(row['FirstName'], row['MiddleName'],  row['LastName'], 
#                                                   row['Primaryspecialty'], 
#                                                   row['City'], row['State'],
#                                                   row['Zip.Code'])
            
            
#         # print(doctor_info)
#         doctor_infolist.append([row['NPI'], doctor_info])

#     return doctor_infolist


def get_doctor_google_result(keyword, pages = 2, timeout = 10):
    
    searched_urls = []
    
    # first two pages
    for page_number in range(pages):
        url = "https://www.google.com/search?q=%s&start=%s" % (keyword, (page_number)*10)
        # print(url)
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        
        # try:
        #     r = requests.get(url, headers=HEADERS, timeout=10)
        # except:
        #     r = scraper.get(url, headers=HEADERS, timeout=10)
            
            
        response = TextResponse(r.url, body = r.text, encoding = 'utf-8')

        # with open('preview.html', 'w') as f:
        #     f.write(str(response.body.decode()))
        
        
        d = response.selector.xpath('.//div[@class="g"]//div[@data-hveid]//a/@href').extract()
        # pprint(d)
        d = [i for i in d if 'http' in i and 'googleusercontent' not in i and 'translate.google.com' not in i]
        
        print('From ULR {}'.format(url))
        print('Get {} results'.format(len(d)))
        searched_urls = searched_urls + d
        
    return searched_urls



if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('--input_path', type = str)
    parser.add_argument('--start',  type=int, default=0, help=' ')
    parser.add_argument('--length', type=int, default=10000, help=' ')
    parser.add_argument('--angry_flag', type=int, default=3, help=' ')
    parser.add_argument('--auth_token', type=str, default=3, help=' ')
    parser.add_argument('--account_sid', type=str, default=3, help=' ')
    # parser.add_argument('--your_phonenumber', type=str, default=3, help=' ')
    args = parser.parse_args()
    
    # db_connection_str = 'mysql+pymysql://root:@localhost:3306/doctorinfo_sample?charset=utf8'
    # db_connection = create_engine(db_connection_str)
    # df = pd.read_sql('SELECT * FROM physicians_sample', con=db_connection)
    try:
        auth_token = args.auth_token
        account_sid = args.account_sid  
        client = Client(account_sid, auth_token)
    except:
        client = None
        print('No SMS Client')




    start = args.start 
    end = args.length + start
    angry_flag = args.angry_flag

    DocListDF_path = args.input_path
    Output_path = DocListDF_path.replace('Data', 'Output').replace('.p', '_GoogleSearch_s{}_e{}.p'.format(start, end))
    print('Read data from\t{}\nSave results to\t{}\n'.format(DocListDF_path, Output_path))
    
    df = pd.read_pickle(DocListDF_path) 
    # cols = ['cId', 'crawlFlag', 'NPI',  'LastName', 'FirstName',
    #         'MiddleName',  'City', 'State', 'Zip.Code', 'Primaryspecialty']
    # DoctorDF = df[cols]
    # doctor_infolist = get_doctor_info(DoctorDF)

    doctor_infolist = df['keyword'].to_list()


    end = len(doctor_infolist) if len(doctor_infolist) < end else end
    doctor_infolist = doctor_infolist[start:end]

    # save the results to tmp_path

    if os.path.exists(Output_path):
        GoogleResult = pd.read_pickle(Output_path)
        collected_NPIs = GoogleResult['NPI'].to_list()
    else:
        GoogleResult = pd.DataFrame(columns = ['NPI', 'searched_urls', 'clct_time'])
        collected_NPIs = GoogleResult['NPI'].to_list()
        
    print('\n\nCollected NPI {}'.format(len(collected_NPIs)))

    flag = 0
    angry_flag = int(angry_flag)
    # L = []
    for idx, doctor_info in enumerate(doctor_infolist):
        
        NPI, keyword = doctor_info
        
        # print(NPI)
        if NPI in collected_NPIs:
            print('ignore NPI:\t', NPI)
            continue
            
        # start searching from here.
        print('\n\n{} & {}\t'.format(start + idx, idx) + str(datetime.now()), '\t', keyword, NPI)

        if flag == angry_flag:
            print('Stop here: Google is angry!')
            if client: 
                message = client.messages.create(body =  "Failed ! Google is Angry! Save as {}, with current idx {}.".format(Output_path, start + idx),
                        from_ = "+16106012683 ", to = "+12405243597", )

            break


        searched_urls = get_doctor_google_result(keyword, pages = 2)
        if len(searched_urls) == 0:
            flag += 1
            print('No results for:', NPI, keyword, '\tflag is {}/{}\t'.format(flag, angry_flag))
            continue

        # status = 1
        timestamp = str(datetime.now())
        
        d = {
            'NPI': NPI, 
            'searched_urls': searched_urls,
            'clct_time': timestamp
        }

        # L.append(d)

        GoogleResult = GoogleResult.append(d, ignore_index=True)
        GoogleResult.to_pickle(Output_path)
        second = random.randrange(0, 5)
        time.sleep(second)
        
    if flag < angry_flag and client:
        message = client.messages.create(body =  "Success ! Save as {}, with current idx {}.".format(Output_path, start + idx),
                    from_ = "+16106012683 ", to = "+12405243597", )


