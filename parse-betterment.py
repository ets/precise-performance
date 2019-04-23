import logging, os, csv, glob, pprint
from datetime import datetime


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
                # print(f'data row {", ".join(row)}')
                account = row[1]                
                amount = 0
                txnDesc = row[2].lower()
                if "dividend" not in txnDesc: # we're considering dividends same as equity bumps
                    amount = row[3]
                balance = row[4]                
                date = datetime.strptime(row[6], "%Y-%m-%d %H:%M:%S %z")         
                
                if account in accounts:
                    accountDict = accounts [account]
                    accountDict [date] = [float(amount),float(balance)]
                else:
                    accounts [account] = {date: [float(amount),float(balance)]}
    # pp.pprint(accounts)
                    

for accountName in accounts:        
    monthlyLedger = {}
    account = accounts[accountName]
    stmtEntryKeys = list(account.keys())    
    stmtEntryKeys.sort()
    for year in range(stmtEntryKeys[0].year, stmtEntryKeys[-1].year + 1) :
        #print( str(year))
        for month in range(1, 13):
            #print( str(year) + "/" + str(month))
            matchingKeys = [x for x in stmtEntryKeys if x.year == year and x.month == month]
            if len(matchingKeys) < 1:
                statementDate = datetime.strptime( str(year)+'/'+str(month), '%Y/%m')
                monthlyLedger [statementDate] = [0,"Unknown"]   
                #print (statementDate)
            else:
                matchingKeys.sort()                
                balance = account[matchingKeys[-1]][1] # the second cell in the last entry is the last balance for the month
                flow = 0
                for key in matchingKeys:     
                    flow += account[key][0]
                statementDate = datetime.strptime( str(year)+'/'+str(month), '%Y/%m')
                monthlyLedger [statementDate] = [flow, balance]


    monthlyEntries = list(monthlyLedger.keys())
    monthlyEntries.sort()
    balance = 0
    for entry in monthlyEntries:    
        if(monthlyLedger[entry][1] == "Unknown"):
            monthlyLedger[entry][1] = balance # set it to the previous balance
        balance = monthlyLedger[entry][1]
    
    # Store the account data in mospire format
    with open(processed_folder+"/"+accountName+'-mospire.csv', mode='w') as mospire_file:
        mospire_writer = csv.writer(mospire_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for stmtMonth in monthlyLedger:
            flow = monthlyLedger[stmtMonth][0]
            balance = monthlyLedger[stmtMonth][1]
            mospire_writer.writerow([stmtMonth.strftime("%Y-%m"), balance, flow])

    # Store the account data in bogle spreadsheet format
    with open(processed_folder+"/"+accountName+'-bogle.csv', mode='w') as bogle_file:
        bogle_writer = csv.writer(bogle_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for stmtMonth in monthlyLedger:    
            withdrawal = 0
            flow = 0
            if monthlyLedger[stmtMonth][0] > 0:
                flow = monthlyLedger[stmtMonth][0]
            else:
                withdrawal = abs(monthlyLedger[stmtMonth][0])
            balance = monthlyLedger[stmtMonth][1]
            bogle_writer.writerow([stmtMonth.strftime("%Y-%m"), balance, flow, withdrawal])