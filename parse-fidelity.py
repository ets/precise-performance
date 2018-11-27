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
                indexOfDate = len(raw_folder) + 7
                statementDate = datetime.strptime(filename[:indexOfDate], raw_folder+'/%y%m%d').strftime("%Y-%m-%d")                
                endingBalance = float(row[4])
                marketChange = float(row[3])
                beginningBalance = float(row[2])
                contribution = round(endingBalance - (beginningBalance + marketChange),3)
                
                if account in accounts:
                    accountDict = accounts [account]
                    accountDict [statementDate] = [contribution,endingBalance]
                else:
                    accounts [account] = {statementDate: [contribution,endingBalance]}
    # pp.pprint(accounts)
                    

for account in accounts:
    pickle.dump( accounts[account], open( processed_folder+"/"+account, "wb" ) )            
    # readData = pickle.load( open( processed_folder+"/"+account, "rb" ) )
    # pp.pprint(readData)
    with open(processed_folder+"/"+account+'-bogle.csv', mode='w') as bogle_file:
        bogle_writer = csv.writer(bogle_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for stmtMonth in accounts[account].keys():            
            withdrawal = 0
            contribution = 0
            if accounts[account][stmtMonth][0] > 0:
                contribution = accounts[account][stmtMonth][0]
            else:
                withdrawal = abs(accounts[account][stmtMonth][0])
            balance = accounts[account][stmtMonth][1]
            bogle_writer.writerow([stmtMonth,balance,contribution,withdrawal])