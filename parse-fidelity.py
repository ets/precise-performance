import logging, os, csv, glob, pprint, pickle
from datetime import datetime


# pull these sensitive parameters from the environment vars
raw_folder = './data/raw/fidelity'
processed_folder = './data/processed/fidelity'
accounts = {}
pp = pprint.PrettyPrinter(indent=4)

#
# All environment config is above this line. Everything below is use-case specific data.
#


for filename in glob.glob(raw_folder+'/*.csv'):
    with open(filename) as csvFile:
        csvReader = csv.reader(csvFile, delimiter=',')
        headersRead = False
        for row in csvReader:
            if headersRead and row[1] == '':
                break
            if (not headersRead) and len(row) >= 2 and row[1] == 'Account #':
                # print(f'Column names are {", ".join(row)}')
                headersRead = True
            elif headersRead:
                account = row[1]
                statementDate = datetime.strptime(filename, raw_folder+'/%y%m%d.csv').strftime("%Y-%m-%d")                
                endingBalance = float(row[4])
                marketChange = float(row[3])
                beginningBalance = float(row[2])
                contribution = round(endingBalance - (beginningBalance + marketChange),3)
                
                if account in accounts:
                    accountDict = accounts [account]
                    accountDict [statementDate] = [contribution,endingBalance]
                else:
                    accounts [account] = {statementDate: [contribution,endingBalance]}
                    

for account in accounts:
    pickle.dump( accounts[account], open( processed_folder+"/"+account, "wb" ) )            
    # readData = pickle.load( open( processed_folder+"/"+account, "rb" ) )
    # pp.pprint(readData)
