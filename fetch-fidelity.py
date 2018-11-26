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

#
# All environment config is above this line. Everything below is use-case specific data.
#


# Auth a session
s = requests.Session()
homePage = s.get('https://www.fidelity.com/')
soup = BeautifulSoup(homePage.text, 'html.parser')
loginLinks = soup.find_all('a',href=True, text='Log In')
loginUrl = loginLinks[0]['href']
loginPage = s.get(loginUrl)
soup = BeautifulSoup(loginPage.text, 'html.parser')
loginForms = soup.find_all('form',attrs={'id':'Login'})    
data = {"SSN":fi_username, "PIN":fi_password}
authUrl = urljoin(loginUrl,loginForms[0].get('action'))
r = s.post(authUrl, data=data)
data = []
if r.status_code == 200:                
    statementPage = s.get(fi_statements_url+'/ftgw/fbc/ofstatements/getStatementsList')
    soup = BeautifulSoup(statementPage.text, 'html.parser')
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
                        csvFilename = raw_folder + datetime.strptime(urlParams['c'][0], '%m/%d/%Y').strftime("%y%m%d") + '.csv'
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