import logging, os, csv, glob, pprint
from datetime import datetime


# pull these sensitive parameters from the environment vars
raw_folder = '../data/raw/fidelity'
processed_folder = '../data/processed/fidelity'
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
                statementDate = datetime.strptime(filename[:indexOfDate], raw_folder+'/%y%m%d')
                endingBalance = float(row[4])
                marketChange = float(row[3])
                beginningBalance = float(row[2])
                flow = round(endingBalance - (beginningBalance + marketChange), 3)
                
                if account in accounts:
                    accountDict = accounts [account]
                    accountDict [statementDate] = [flow, endingBalance]
                else:
                    accounts [account] = {statementDate: [flow, endingBalance]}
    # pp.pprint(accounts)
                    

for account in accounts:    
    # Fidelity BS hack here...
    # Search for months that are missing statement data and assume no transactions or balance changes 
    statementMonths = list(accounts[account].keys())
    for year in range(statementMonths[0].year, statementMonths[-1].year + 1):
        for month in range(1, 13):
            matchingMonths = [x for x in statementMonths if x.year == year and x.month == month]
            if len(matchingMonths) < 1:
                statementDate = datetime.strptime( str(year)+'/'+str(month), '%Y/%m')
                accountDict = accounts [account]
                accountDict [statementDate] = [0,"Unknown"]   
                #print (statementDate)

    # pull the list of keys again since I've modified the source dict    
    statementMonths = list(accounts[account].keys())
    statementMonths.sort()
    balance = 0
    for stmtMonth in statementMonths:    
        if(accounts[account][stmtMonth][1] == "Unknown"):
            accounts[account][stmtMonth][1] = balance # set it to the previous balance
        balance = accounts[account][stmtMonth][1]

    # Store the account data in mospire format
    with open(processed_folder + "/" + account + '-mospire.csv', mode='w') as mospire_file:
        mospire_writer = csv.writer(mospire_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for stmtMonth in statementMonths:
            flow = accounts[account][stmtMonth][0]
            balance = accounts[account][stmtMonth][1]
            mospire_writer.writerow([stmtMonth.strftime("%Y-%m-%d"), flow, balance])

    # Store the account data in bogle spreadsheet format
    with open(processed_folder+"/"+account+'-bogle.csv', mode='w') as bogle_file:
        bogle_writer = csv.writer(bogle_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for stmtMonth in statementMonths:    
            withdrawal = 0
            flow = 0
            if accounts[account][stmtMonth][0] > 0:
                flow = accounts[account][stmtMonth][0]
            else:
                withdrawal = abs(accounts[account][stmtMonth][0])
            balance = accounts[account][stmtMonth][1]
            bogle_writer.writerow([stmtMonth.strftime("%Y-%m"), balance, flow, withdrawal])