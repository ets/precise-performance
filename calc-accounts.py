import logging, os, glob, pprint, pickle, re
from datetime import datetime, timedelta
from dateutil.rrule import rrule, DAILY, MONTHLY

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
    for filename in glob.glob(broker+'/*.pickle'):
        tokens = re.split('/|\.',filename)        
        brokerName = tokens[4]        
        accountName = tokens[5]
        readData = pickle.load( open( filename, "rb" ) )
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
            stmtKey = str(stmtDate.year)+"-"+str(stmtDate.month)
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

# for dt in rrule(MONTHLY, dtstart=startDate, until=today):
#     # print(dt) 
#     brokers = list(data.keys())
for entry in consolidatedByMonth:    
    entryYearMonth = datetime.strptime( entry, '%Y-%m')
    if entryYearMonth >= datetime.strptime( str(startDate.year)+"-"+str(startDate.month), '%Y-%m') and entryYearMonth <= datetime.strptime( str(targetMonth.year)+"-"+str(targetMonth.month), '%Y-%m'):
        print(entry)
        print(consolidatedByMonth[entry])
