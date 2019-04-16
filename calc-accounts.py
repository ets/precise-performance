import logging, os, glob, pprint, csv, re
from datetime import datetime, timedelta
from dateutil.rrule import rrule, DAILY, MONTHLY
import numpy as np

# pull these sensitive parameters from the environment vars
processed_folder = './data/processed'
data = {}
pp = pprint.PrettyPrinter(indent=4)

#
# All environment config is above this line. Everything below is use-case specific data.
#

today = datetime.today()
firstOfMonth = today.replace(day=1)
lastMonth = firstOfMonth - timedelta(days=1)
targetMonth = lastMonth.replace(day=1)
print("Targeting a performance through ["+str(targetMonth.year)+"-"+str(targetMonth.month)+"]")
earliestStatements = []
latestStatements = []
consolidatedByMonth = {}

for broker in glob.glob(processed_folder+'/*'):
    for filename in glob.glob(broker+'/*-mospire.csv'):
        tokens = re.split('/|\.',filename)        
        brokerName = tokens[4]        
        accountName = tokens[5]
        readData = {}
        with open(filename, mode='r') as mospire_file:
            csvReader = csv.reader(mospire_file, delimiter=',')
            for row in csvReader:
                stmtDate = datetime.strptime(row[0], '%Y-%m')
                readData[stmtDate] = [float(row[1]),float(row[2])]

        # pp.pprint(readData)
        allDates = list(readData.keys())
        allDates.sort()
        earliestStatements.append( allDates[0] ) #append the first date time in the data
        latestStatement = allDates[-1] 
        if latestStatement.year != targetMonth.year or latestStatement.month < targetMonth.month:
            print("Ignoring "+brokerName+" - "+accountName+" with a latest statement of only ["+str(latestStatement)+"]")
            continue
        else:
            print("Using "+brokerName+" - "+accountName+" with a latest statement of only ["+str(latestStatement)+"]")
        entryKeys = list(readData.keys())
        for stmtDate in entryKeys:
            stmtKey = datetime.strptime( str(stmtDate.year)+"-"+str(stmtDate.month) , '%Y-%m') 
            if stmtKey in consolidatedByMonth:  
                consolidatedByMonth[stmtKey][0] += readData[stmtDate][0]
                consolidatedByMonth[stmtKey][1] += readData[stmtDate][1]
            else:
                consolidatedByMonth[stmtKey] = readData[stmtDate]
                
        if brokerName in data:
            brokerData = data [brokerName]
            brokerData [accountName] = readData
        else:
            data [brokerName] = {accountName: readData}

earliestStatements.sort()
startDate = earliestStatements[-1]
earliestStatements = None

# entry.key = statementdate
# 0 = flow
# 1 = close balance 
allStatementKeys = list(consolidatedByMonth.keys())
allReportableKeys = []
for i in range(len(allStatementKeys)):
    key = allStatementKeys[i]    
    # Only report on keys that fall within our StartDate and TargetMonth window
    if key > datetime.strptime( str(startDate.year)+"-"+str(startDate.month), '%Y-%m') and key <= datetime.strptime( str(targetMonth.year)+"-"+str(targetMonth.month), '%Y-%m'):
        allReportableKeys.append(key)

allStatementKeys = None
allReportableKeys.sort()

growth10k = [10000]
oneMonthReturn = []
threeMonthReturn = []
sixMonthReturn = []
ytdReturn = []
oneYearReturn = []
threeYearReturn = []
fiveYearReturn = []
tenYearReturn = []
irrFlow = []

for i in range(len(allReportableKeys)):
    key = allReportableKeys[i]
    priorKey = allReportableKeys[i-1]
    entry = consolidatedByMonth[key]
    priorEntry = consolidatedByMonth[priorKey]
    openBalance = priorEntry[1]
    closeBalance = entry[1]
    flow = entry[0]                 
    monthReturn = 0
    if openBalance + flow > 0:
        monthReturn = (closeBalance-flow/2)/(openBalance+flow/2) - 1        
    growth10k.append(growth10k[len(growth10k)-1] * (1 + monthReturn))
    oneMonthReturn.append(monthReturn)
    if i == 1:
        irrFlow.append( -(openBalance + flow/2) ) 
    else:
        flowEntry = -flow/2+closeBalance
        if i+1 < len(allReportableKeys):
            nextKey = allReportableKeys[i+1]
            nextEntry = consolidatedByMonth[nextKey]
            flowEntry = -(flow/2 +  nextEntry[0]/2)
        irrFlow.append( flowEntry ) 

    if i > 2:
        threeMonthReturn.append( growth10k[-1] / growth10k[-4] - 1)
    if i > 5:
        sixMonthReturn.append( growth10k[-1] / growth10k[-7] - 1)
    if i > 11:
        oneYearReturn.append( growth10k[-1] / growth10k[-13] - 1)
        ytd = 0
        mthOffset = i + 1 - key.month       
        if growth10k[mthOffset] != 0:
            ytd = growth10k[-1]/growth10k[mthOffset] - 1
        ytdReturn.append(ytd)     

    if i > 35:
        threeYearReturn.append( (growth10k[-1] / growth10k[-37])**(1/3) - 1)
    if i > 59:
        fiveYearReturn.append( (growth10k[-1] / growth10k[-61])**(1/5) - 1)
    if i > 119:
        tenYearReturn.append( (growth10k[-1] / growth10k[-121])**(1/10) - 1)
        
        
myirr = ( 1 + np.irr(irrFlow)) ** min(12, len(allReportableKeys) ) - 1
print ( "IRR is {0:.3%}".format(myirr) )
print ( "1mth is {0:.3%}".format(oneMonthReturn[-1]) )
print ( "3mth is {0:.3%}".format(threeMonthReturn[-1]) )
print ( "6mth is {0:.3%}".format(sixMonthReturn[-1]) )
print ( "YTD is {0:.3%}".format(ytdReturn[-1]) )
print ( "1y is {0:.3%}".format(oneYearReturn[-1]) )
print ( "3y is {0:.3%}".format(threeYearReturn[-1]) )

