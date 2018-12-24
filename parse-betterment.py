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
                print(f'data row {", ".join(row)}')
                account = row[1]                
                amount = 0
                txnDesc = row[2].lower()
                if "dividend" not in txnDesc: # we're considering dividends same as equity bumps
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
    monthlyLedger = {}
    statementEntries = list(accounts[account].keys())    
    statementEntries.sort()
    for year in range(statementEntries[0].year, statementEntries[-1].year):
        print( str(year))
        for month in range(1, 13):
            print( str(year) + "/" + str(month))
            matchingEntries = [x for x in statementEntries if x.year == year and x.month == month]
            if len(matchingEntries) < 1:
                statementDate = datetime.strptime( str(year)+'/'+str(month)+"/21", '%Y/%m/%d')
                monthlyLedger [statementDate] = [0,"Unknown"]   
                print (statementDate)
            else:
                matchingEntries.sort()                
                balance = matchingEntries[-1][1] # the second cell in the last entry is the last balance for the month
                contribution = 0
                for entry in matchingEntries:     
                    contribution += entry[0]
                statementDate = datetime.strptime( str(year)+'/'+str(month)+"/21", '%Y/%m/%d')
                monthlyLedger [statementDate] = [contribution,balance]   
                pp.pprint(matchingEntries)


    monthlyEntries = list(monthlyLedger.keys())
    monthlyEntries.sort()
    balance = 0
    for entry in monthlyEntries:    
        if(monthlyLedger[entry][1] == "Unknown"):
            monthlyLedger[entry][1] = balance # set it to the previous balance
        balance = monthlyLedger[entry][1]
    
    # Store the account data
    pickle.dump( monthlyLedger, open( processed_folder+"/"+account, "wb" ) )            
    # readData = pickle.load( open( processed_folder+"/"+account, "rb" ) )
    # pp.pprint(readData)

    with open(processed_folder+"/"+account+'-bogle.csv', mode='w') as bogle_file:
        bogle_writer = csv.writer(bogle_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for stmtMonth in monthlyLedger:    
            withdrawal = 0
            contribution = 0
            if monthlyLedger[stmtMonth][0] > 0:
                contribution = monthlyLedger[stmtMonth][0]
            else:
                withdrawal = abs(monthlyLedger[stmtMonth][0])
            balance = monthlyLedger[stmtMonth][1]
            bogle_writer.writerow([stmtMonth.strftime("%Y-%m-%d"),balance,contribution,withdrawal])