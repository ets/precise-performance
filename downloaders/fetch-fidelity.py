import os, requests, logging
from urllib.parse import urlparse, urljoin, parse_qs
from bs4 import BeautifulSoup
from datetime import datetime

# pull these sensitive parameters from the environment vars
fi_username = os.environ['FIDELITY_USERNAME']
fi_password = os.environ['FIDELITY_PASSWORD']
fi_url = 'http://www.fidelity.com'
fi_statements_url = 'https://statements.fidelity.com'
raw_folder = './data/raw/fidelity/'

plain_cookie = 'JSESSIONID=0C9E1D5991EC5B9375418FF47788FF30; eotvc=""; eotvc_ts=-1; AcctInfoC=AAAGEAAAA/QAAAQIYRrsUcDLxpF431TiSIeta/pojukA2yICf9wU2hE4vpihb8UdmashO9c9hbasjb9unlQWak97OtvG0TVJS6rR/pobpgQmIOwnBlBiopmvhiwqRNy/UpuPRNDGJ6gcpsO0emUtgfkCaWLVWkUHIJ835AO8mFqRA184*IbLi8ZjQj1Ypwg2cv0NZ3/vnQ2b/lzF2Xe4*PuqzxhQVLyCImxWI7enYVi1BE*UXK*A8EcdvQTBWCN4jjciYua4tNHxobLaND2ymlfX2cHbcEV5FRsMNF80yTRmbzsfPStKpSdBESqL5Xk9rZ42zTMveLav2PSy87OsGU2fOut2b/jf8deLOJh8x5sbcQ0vJAVSt3t1VQ9d*4iMwiFJM7KktGa0aKRFZKvBVlg8bPBiCVJ7hOBqzS*J1944jeDuAvFNonjjLaKwyQzxnDRuJxuT160seiPTcei5bp3W/XeEE1cmAtiM1qSLz55EZjvaVYN/QnV/Xm43JAixs5SZ2rusu/fLGGijsmybWI2lBTuVyevcnsU2Jw5EP0kI/qEop10je3dYC9WtWz8yNWpvqj/VW7xDMItUmSvDnOib9xK1tsxOGUHbKVnE42rhCx0CYWHQ*yJnTuy4w*MPXLoVo2LRkkTK3XKbRUgylDOLVaRWsbJtvRkjpd8rhOlLmrDWXsua3pl/ZdMI5hQbiErrGY8BpEQX8BneHvma*javhmnHooicJY7xdl0XXuqwpqaPlXfUCrsuiu0EFS9xmn4Jgy1Y/M6c68nF45*H78ESvUztWZRMrLNeQ1HIXvgYKJmbluuv/g045V036kS1i3JD4j7LCsvvnVFs0K/NJNUSTOE/T*3QPtTGOLlht1eodRs6M9UM4W2TqO7U9s5MosZbt3JZzRApRC6suqKPQVAxkA6kRTXU4QQoFrnJGRYvrOTb5tVA3zu52Mi2q/4OJGWZVmrYMFKYhSghb1YKTrW*DZr3bQkDDiHl9DwKA0yG*3Zs3qKBjQUP7h31huLmGFnRaansiHcOG7Yq5WsPIo*885yIRxsRHTtOyhCxjIDO0xErq3fMTZOH1hRUJ2e10lK*u9NkRQlIvrdce6jrV6a5E2oBtwOWCZC7bGrAMbeksJYhH5C*cxlbzljsFhKYgNyyRuSG71DQVWFULOTYRmJXhwF1fLHKcUxTHBRqjFrf*dzI4nH5uKqv19R0PX8dTPhisO/nXzYaaYHjEA1kZVUQpih3/g47bJpmYSTYArIGhJNHUO3Mb40uXh8*ZxfC6H*BBuQmHrtdd4L0lnLS*NK8BAIeR4to4WA7THxW6nXtUHpZuDLZ2rOIRNBoVhF*hIk558vquzsQpfNoGf0FQzw53UVNGN6Kwt3bSCu4qxK22Cyy; B=AAAAAQAAAAkAAAAgmoPXpq1Af2M2bfg5BoxcV01b6WkRkyHTiHlICbO10ZE=; RtAzC=A3YqOF6acE2OvioL^YfDAZMbonE^OgMieMeA6RFLoVKxOPVwdTEQwi^rw7wBBetuwrHVxUXw9kLU4erDi^8VZK2e_XgsbsVQ^X_DAtcUFztlBGeDiIuw4_kQ64dIK9pFNnRDMUVkTOzbe6v3s18dR1ms2GNObe3nJTlQvh1MeqPxUVAm4johKQ3MqwZMiPMFOBYJ6YgTe7VAtd8N8yLqyzpcZab3e6hHNqmy4sTXpZQ5dlAIpbw0^Vtu0^fbD1I^1gsWMB^VEFGPt7Qyq2ykaav435grrCD6IUGJMfvMgw_j0SEWRB800V8HS0Z3ZSU65B1tx8Z1kiOTfBpzQhxQfAdYZ62x5Ssnc7TEzwiniKNZDGwrzi8ZWs4qln_bOrS30QGePQ14tyH^TEYSdiMfa8Eu8KVygFw8UXxhOnIhhgi9QM1KXvqMsbuej64M77TA2MZ0Pv1paeBjXEafol8RsAxVRdq^kVknWRb7iKfi2kmbEXCzh8WnFNhNC_Vd8LQmHA; _abck=ADFF82D8B569AF54BCBDCE39FB3250D1~0~YAAQX5TcF1gnFntuAQAAfpUYmwIF+HZG3kL5DRnMxGy2CZDvngkgLmPi+diPU22IswyshKtw1AaDmiugdxj5c6VptC+OTMCqB7Fleu7FkYt2Noyp3Vfpm5WAjsPHmvaQi8Ye1MOem0TIrHGuH9XpbSL11BlzyJfQYa8Z7jis9WSbNhqFPiZx3dP6V5r3gm903AtqMeEvcayjggp3EAhmDeZ4OT65f3MyyMOA1hF/P/OVViL1wKeznszgQ266Uj1dkBasutGxQZMOn6J9w2D4UDhsl5dfYc/wop//PInWo/ae4npStWWt90SIEJUghpZ3UumYK1f/8bzOcwjWn53BnQ==~-1~-1~-1; MC=ms1GLxhFnpMWxQ1sbxt5oZHEf7QSAlyDzdcKCEgVIAFe7gAPqjMGBAAKADIGBV3Z4YwABgkAAAABBwoABwUFABMN7i7avcR8DBHWuQ^byLVKqncDEQYLG2RqLmNoZi5yYQIcAAAAAAAAAyYBAyoBAAAAAAAAP03; cvi=p1=5c83cdd70a08481520015eee000faa33&p2=ee2edabdc47c0c11d6b90f9bc8b54aaa77&p3=01&p4=06&p5=&p6=&p7=ee2edabdc47c0c11d6b90f9bc8b54aaa77&p8=06&p21=&p22=&p99=; s_pers=%20visitStart%3D1552141788578%7C1583677788578%3B%20s_dfa%3Dfidelitycom%7C1567605413003%3B%20gpv_c11%3DFid.com%2520web%257Cmoney%2520movement%257Ctransfer%257CTransfer%2520Money%2520Shares%2520Hub%2520Page%7C1567605413759%3B; s_vi=[CS]v1|2E41E6EE0507B695-40000110E0000279[CE]; __CT_Data=gpv=8&ckp=tld&dm=fidelity.com&apv_178_www43=8&cpv_178_www43=8&rpv_178_www43=8; WRUIDAWS=2172650773955199; AMCV_EDCF01AC512D2B770A490D4C%40AdobeOrg=-330454231%7CMCAID%7C2E41E6EE0507B695-40000110E0000279%7CMCMID%7C55931904923412464892226562101359611638%7CMCAAMLH-1557675916%7C6%7CMCAAMB-1557675916%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1557078306s%7CNONE%7CMCCIDH%7C-1181058235%7CvVersion%7C3.1.2%7CMCIDTS%7C18022; RtEntC=Axa_4ePz7d1UTlE3WM1Ja5f_5MijvtMFxEJ9RsaiZAqMsvVD1fwpkLpzyzD5Sng1aP^7QDzadPrEr5znsbjkEnqPZVei29OOLLkpTDAs3R37eImyaONBzZgQmeksvg8YpQ; cinfo=mstatus[N]:ctype[X]; s_sess=%20s_cc%3Dtrue%3B%20s_sq%3D%3B; afc.initialSessionID=80ED01655028D5EC96290D252C5F0206; fvid=5c83cdd70a08481520015eee000faa33; ak_bmsc=1A46053A231BB5DDBD637D79195B4746A5FE2DBD11120000E7DDD95D12E67F20~plZD/ioFsB6WP0f9bMAzEteARyoarqbOXJ53hwV5IF3Pp8tBOMIusLBmKnUTLnbewQJxCAf6jFg7iMAoWcv7pdbTU3s58/Eff7PZMAQsP7NnxjfjxosiqbjjA0kqsOTdOl4uted7f3iJWhdle6neXcjVaMwwztIt9J4wT7m/slLRhm48jc4UsevchfOMfph2G3oG2I+30B70hKjIjSVyVHAV3PbDygThE+KewicCKEThg=; bm_sz=8DDFD9B303A5184402967E8184F34725~YAAQvS3+pYEmnYxuAQAARNEKmwUbhlo0ypUK7uaooODBdTPXh/+V7QBIyzP3mmSFCZ1v5mfvgqJw/uHDs4UpQDoj72XzvGSc/u5pWsN/tZyuubmZ4Qm8Ah1OBFWYq5rAC4oPNvysntjAcoreHi/TAje3SMwfZ2IsoaqJY3wD0RL604jrV3BC8ajT7NgR94KjfLI=; bm_sv=228F445F183D006A0FACE78D18322D6D~V8LrLjG73/avI42PmA3wZGju5eRXb5BhNNA8oEQ6bYrKiV6RTiuG9YaDsWPqq3pkp5d7Q4K6WyR39u1CmGXp/mLqxsWbTyxpu/5lRhyYrZKznbtgMXK+54Z4EHehmNygWkJkje+kQvVqvq5IPI24KYdLrUPSY7qDXkgyM/RndSg=; bm_mi=FA235F0C24ECF4BCAADFCFC17140585A~rKwQXyUm8j37RRbmdUueRGomSRF1Hxj1OQjMkTqF8vCy0dLP2fXiJzCFFDTqYiaQNQBAbNTrckmovAqSXk3k5tRDDcfgqy46wfLYBqPLelXQmKswFb4HcDZMEUIu6zsUWqgfOtM6pO374wIhabVnxtIEkc55sIauiQqls2xSJT1Rx6sR+ZXtjE/B322lUgoA0P0sVAYMLQ5NJM9JyPHoPcdSBnld0qYDtTZNZxRtKJg=; AKA_A2=A; ATC=mx5UDc1Da1gCxJRX620pPdx8A^ld2eHTXdnv413Z4Yw; FC=Jh5uR8tYV8cAB8kYNl_pg9aGfgW_B_fxlPxumJsgpTyOYMvynhX7NX_eal1mJ7CzXqKjTqY5FbUlSr^Va9xe0AEjiAXn8QFzWkyyFIobdp7330wTiW7rr3mt7inhnYPWL2vxpwmDEFIrkULLijUizrIrVLfCbYbBPZpbGnfD473t50jdEDnQbJDEpEZ8Pjg2I2wPpuLRvrNviLq60LrtpZA8oNdW3_x2GisuxqwHHiiTz5k_HDLPx8aMvururY66d5xyMqPmMGfyRimAEYgYhgadcN0cSmh8G70z2AvBr4kXGbYKsubLgZ623VjuYA2rcgPN7mIDIBKOwleQ58SQ5E2n8cct0xhf7SsIsm0oIyVoWM20MWO5a6knwi2LUlRcP03; RC=3O3D6PqypZy9BqxBsUJThp4p2l1FY9yy^qhaYL7A9dVXcaeWwEY8I8rYWuhDqJAMoYRzxDAmQDWxBKtC4L4LbFWC1mSpcupEFxBAgEunw8YYd1u0bbwf3tB7TGx6PcIP4TooKjmhzLiHwK8oWWjnwMuPOV5SX^CbTRnp_U1pBRRIkxIosQBMxcEmqK01EblFVNxcRxrSpnfklHl06EOfs6lNliAEpgEE5V^43PNT2iDmsVrCm8F90gx9b47Kz6zdflbdr04rTU2Qt^SNY^44oAKFK6wouVL6abc6gokgoAXmDvMcGkMcPEQimrd5sztnV^Gkqy_uCS7DO9ksGmgea2xiNePFpkqwjDcr9PT1lSgqfIfH5_TltRNRhU9V8pmtIAxjf2JFborM1z5sTsxT7_6kcQds7fn6ysXF^hsl1lCVgVtr5IQIUHJPu1pNZxg9LGxkkD7i3HpmYwA61mtBuOi2EaHZrxH_vejIn_D2oPijnRtUPE_27Bqik6UQrqjRpFi8LMco7B7bF_bwFYnLxXg^Wa3vNn1FCj3hHcB4ZczR47Ohmj1V8IE2ZK6b2UUotkAk3FVAuvdxBAhPz_YacBLX0yCfCjVuAiBew3vII^VAQXjESn4ZbNGnoT0NIstVEedccINvg^tTnIFdrSyL5RPXrQmrzW^CnDv0ogy4R89Gad32vpnxJDPLtZY1bU0qx1Yf7bxcAXeBM^J0YdLLMkkHMF4InlgFO3niBGEHU3hy0cygNsWivEuPMReMoz1NjO2XjoWcIR8N^Jgc6xAsiQI5hnmZqKffEWngrbEdim1uytcahgodTMMqHEeRRDJLrKkGyTpV07WiFRrsnncgZ_5m02JNnMUfdb41IYyuF4bRIqRsrhwgztC5_hws1rlfnQoD02Vgnvhdzu9lUxuCbRxJLC4oR4OTRlDrXIQn_YBvcizfuNbs4qS_19H3xzyr7pWdWAQ5YasWSZxb8ePj2i28DHNlRjCZukRDSkB0Dv5S1hKN4xvmDcf3ZzbSODtcpWLd8wrIzm3tYa3COlXJ4Og2^eRcskhfJe38DyMYRz1e_RyrCI69MSSmPS895Ut_nPG4Gl8h6v5XS26q2Vs2wXOfogAAWRcmC_K81tNxaHxwAsU0BszESeZz8qajpuvbwyGZLJjUUosfDDmrPgMw_cBjArRo6kpe6Yl^_EdQgr4pCHAtiNTAPSawhsDoXS6eJ2pq_5Q^5SRaLhQnuf5Hb6TwY91AtmKPcoWciMMo9Of7vRH_p8PNNYT0W2BqcPiSayCjNxQ7Q_1JpdE0SNTvuhuvmYvKowWWXxWx6RNGKDGkdes0P6Dp2OZZQS1Bacg1oj0qlXYRmalMD^y7b8Bd1vy^IYDQbfRu_VQftqALgFHaP714VIcFFP62KUVW8UWKk17z8g^s4U9_4G3kY2xaSEGaIfZzylaoy^zjadepPKkfXGaDu2rDHQ63Gx5knRqIK40Kahr722gDFs38jqft372dSidqeNx5WWjo3ezVdoQOgwhceWlYHkjp7YWd9LRAhVKYvuz6iOYg^qz6^yAYa5CXjOiGhjYcswW0gFPs5HA93DGIV1gpt5BP_lVC5c1x13dxlL_dazVzajXHxNYhOCwhkT1zfwgjz2b4olqNaB9H^ksHoGwKpMprf1SEf9crKrvAz8NuvtOUJGvYPBQP^OnkWhOv1bDbOaBv^h_9SGMP03; SC=guRL7Y6qQV^H0H^XIukWU3n^5t5lma7KycpCfgKPxsVdEySrg2yQTouFLKs0RLc4mc7NFeOcOZIebbuHnWOxt8XKMs8w16oVGZ_u4Z5He5NM_9bpS9ADxX91DAaeTD3GrnFUU2FxunCkFDJ4XAdVBUiEcG5cYbXbTepoyCwjfA_E0a0NtSMsdO6lqRtEk61vQ8dYL9B6m3TcGvRap_YhesBeAtpzP9uKFJTQVe2B5whIxBpiXNqiZ2^5UfwwfY1RP03; pmcrtp2=289933322.5190.0000; zpc=RTP2'

#
# All environment config is above this line. Everything below is use-case specific data.
#


# Auth a session
s = requests.Session()
dict_cookie = dict(p.strip().split('=',1) for p in plain_cookie.split('; '))
# print(dict_cookie)
cj = requests.utils.cookiejar_from_dict(dict_cookie)
sess = requests.Session()
sess.cookies = cj

statementPage = s.get(fi_statements_url+'/ftgw/fbc/ofstatements/getStatementsList')
soup = BeautifulSoup(statementPage.text, 'html.parser')
print(statementPage.text)
statementListForm = soup.find('form',attrs={'name':'statementList'})
hidden_tags = statementListForm.find_all("input", type="hidden")
postData = {}
for tag in hidden_tags:
     postData[tag.get('name')] = tag.get('value')

for year in ['2018','2017','2016','2015']:
    postData['dateRangeIndex'] = '0:'+year
    statementPage = s.post(fi_statements_url+'/ftgw/fbc/ofstatements/getStatementsList',data=postData)
    # with open("statement.html", 'w') as f:
    #     f.write(statementPage.text)
    soup = BeautifulSoup(statementPage.text, 'html.parser')
    datadivs = soup.find_all("div", {"class": "statement-data-table"})
    print("Found "+str(len(datadivs))+" data tables for "+year)
    if (len(datadivs) > 0):
        table = datadivs[-1].find('table')
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            links = row.find_all('a',href=True)
            if len(links) > 0 :
                parsedLink = urlparse(links[-1]['href'])
                urlParams = parse_qs(parsedLink.query)
                if 'download' in urlParams and urlParams['download'][0] == 'y' and len(urlParams['c']) > 0:
                    # This is a row with a CSV download
                    statementDate = urlParams['c'][0]
                    csvFilename = raw_folder + datetime.strptime(statementDate, '%m/%d/%Y').strftime("%y%m%d") + '.csv'
                    uniq = 1
                    while os.path.isfile(csvFilename):
                        csvFilename = csvFilename[:-4] + '.'+uniq+'.' + csvFilename[-4:]
                        uniq = uniq + 1
                    csvResponse = s.get(fi_statements_url+links[-1]['href'])
                    with open(csvFilename, 'w') as f:
                        f.write(csvResponse.text)

    else:
        print (year+" had no statement-data-table")
            

            





# data = requests.get('https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=MSFT&apikey=demo&datatype=csv')
# if response.status_code == 200:
#             # Open file and write the content
#             with open(filename, 'wb') as file:
#                 # A chunk of 128 bytes
#                 for chunk in response:
#                     file.write(chunk)