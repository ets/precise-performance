import logging, os, csv, glob, pprint, pickle
from datetime import datetime, timedelta


# pull these sensitive parameters from the environment vars
raw_folder = './data/raw/betterment'
processed_folder = './data/processed/betterment'
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
            if not headersRead :
                # print(f'Column names are {", ".join(row)}')
                headersRead = True
            elif headersRead:
                account = row[1]                
                amount = 0
                txnDesc = row[2].lower()
                if "dividend" not in txnDesc:
                    amount = row[3]
                balance = row[4]
                date = datetime.strptime(row[6], "%Y-%m-%d %H:%M:%S %z")         
                
                if account in accounts:
                    accountDict = accounts [account]
                    accountDict [date] = [amount,balance]
                else:
                    accounts [account] = {date: [amount,balance]}
    # pp.pprint(accounts)
                    

for account in accounts:    
    statementMonths = list(accounts[account].keys())
    for year in range(statementMonths[0].year, statementMonths[-1].year):
        for month in range(1, 13):
            matchingMonths = [x for x in statementMonths if x.year == year and x.month == month]
            if len(matchingMonths) < 1:
                statementDate = datetime.strptime( str(year)+'/'+str(month)+"/21", '%Y/%m/%d')
                accountDict = accounts [account]
                accountDict [statementDate] = [0,"Unknown"]   
                print (statementDate)

    # pull the list of keys again since I've modified the source dict    
    statementMonths = list(accounts[account].keys())
    statementMonths.sort()
    balance = 0
    for stmtMonth in statementMonths:    
        if(accounts[account][stmtMonth][1] == "Unknown"):
            accounts[account][stmtMonth][1] = balance # set it to the previous balance
        balance = accounts[account][stmtMonth][1]
    
    # Store the account data
    pickle.dump( accounts[account], open( processed_folder+"/"+account, "wb" ) )            
    # readData = pickle.load( open( processed_folder+"/"+account, "rb" ) )
    # pp.pprint(readData)

    with open(processed_folder+"/"+account+'-bogle.csv', mode='w') as bogle_file:
        bogle_writer = csv.writer(bogle_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for stmtMonth in statementMonths:    
            withdrawal = 0
            contribution = 0
            if accounts[account][stmtMonth][0] > 0:
                contribution = accounts[account][stmtMonth][0]
            else:
                withdrawal = abs(accounts[account][stmtMonth][0])
            balance = accounts[account][stmtMonth][1]
            bogle_writer.writerow([stmtMonth.strftime("%Y-%m-%d"),balance,contribution,withdrawal])