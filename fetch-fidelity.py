import os, requests, logging
from urllib.parse import urljoin 
from bs4 import BeautifulSoup

# pull these sensitive parameters from the environment vars
fi_username = os.environ['FIDELITY_USERNAME']
fi_password = os.environ['FIDELITY_PASSWORD']
fi_url = 'http://www.fidelity.com'

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
    for year in ['2018','2017','2016','2015']: 
        statementPage = s.get('https://statements.fidelity.com/ftgw/fbc/ofstatements/getStatementsList',data={'dateRangeIndex':'0:'+year})
        soup = BeautifulSoup(statementPage.text, 'html.parser')
        datadivs = soup.find_all("div", {"class": "statement-data-table"}) 
        print("Found "+str(len(datadivs))+" data tables for "+year)
        if (len(datadivs) > 0):
            table = datadivs[-1].find('table')
            rows = table.find_all('tr')
            print("Last table has "+str(len(rows))+" rows")
            for row in rows:
                cols = row.find_all('td')
                if (len(cols) > 6):
                    data.append(cols[-1]) 
        else:
            print (year+" had no statement-data-table")
            
print(data)

            





# data = requests.get('https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=MSFT&apikey=demo&datatype=csv')
# if response.status_code == 200:
#             # Open file and write the content
#             with open(filename, 'wb') as file:
#                 # A chunk of 128 bytes
#                 for chunk in response:
#                     file.write(chunk)