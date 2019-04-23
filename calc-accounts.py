import glob, pprint, csv, re
from collections import namedtuple
from datetime import datetime, timedelta
import numpy as np

# pull these sensitive parameters from the environment vars
processed_folder = './data/processed'
pp = pprint.PrettyPrinter(indent=4)

LedgerEntry = namedtuple('LedgerEntry', ['flow', 'balance'])

#
# Utility class for calculating IRR.
# Supports a set of named transaction ledgers
#
class IRRCalculator():

    def addLedger(self, ledger_name, ledger):

        self.monthlySummaries = {}
        for entryDate in list(ledger.keys()):
            #TODO use more python fu here, we're just reducing the map to a single summed entry for each month
            stmtKey = datetime.strptime(str(entryDate.year) + "-" + str(entryDate.month), '%Y-%m')
            if stmtKey in self.monthlySummaries:
                self.monthlySummaries[stmtKey].flow += ledger[entryDate].flow
                self.monthlySummaries[stmtKey].balance += ledger[entryDate].balance
            else:
                self.monthlySummaries[stmtKey] = ledger[entryDate]



    def get_irr(self, start_month, target_month):




        if latestStatement.year != targetMonth.year or latestStatement.month < targetMonth.month:
            print("Ignoring " + brokerName + " - " + accountName + " with a latest statement of only [" + str(
                latestStatement) + "]")
        else:
            print("Using " + brokerName + " - " + accountName + " with a latest statement of only [" + str(
                latestStatement) + "]")

        print("Targeting a performance through [" + str(self.targetMonth.year) + "-" + str(self.targetMonth.month) + "]")

        # entry.key = statementdate
        # 0 = flow
        # 1 = close balance
        allStatementKeys = list(self.monthlyLedger.keys())
        allReportableKeys = []
        for i in range(len(allStatementKeys)):
            key = allStatementKeys[i]
            # Only report on keys that fall within our StartDate and TargetMonth window
            if key > datetime.strptime(str(startDate.year) + "-" + str(self.startDate.month),
                                       '%Y-%m') and key <= datetime.strptime(
                    str(targetMonth.year) + "-" + str(targetMonth.month), '%Y-%m'):
                allReportableKeys.append(key)

        irrcalc = IRRCalculator(ledger=allReportableKeys)


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
            priorKey = allReportableKeys[i - 1]
            entry = self.monthlyLedger[key]
            priorEntry = self.monthlyLedger[priorKey]
            openBalance = priorEntry[1]
            closeBalance = entry[1]
            flow = entry[0]
            monthReturn = 0
            if openBalance + flow > 0:
                monthReturn = (closeBalance - flow / 2) / (openBalance + flow / 2) - 1
            growth10k.append(growth10k[len(growth10k) - 1] * (1 + monthReturn))
            oneMonthReturn.append(monthReturn)
            if i == 1:
                irrFlow.append(-(openBalance + flow / 2))
            else:
                flowEntry = -flow / 2 + closeBalance
                if i + 1 < len(allReportableKeys):
                    nextKey = allReportableKeys[i + 1]
                    nextEntry = self.monthlyLedger[nextKey]
                    flowEntry = -(flow / 2 + nextEntry[0] / 2)
                irrFlow.append(flowEntry)

            if i > 2:
                threeMonthReturn.append(growth10k[-1] / growth10k[-4] - 1)
            if i > 5:
                sixMonthReturn.append(growth10k[-1] / growth10k[-7] - 1)
            if i > 11:
                oneYearReturn.append(growth10k[-1] / growth10k[-13] - 1)
                ytd = 0
                mthOffset = i + 1 - key.month
                if growth10k[mthOffset] != 0:
                    ytd = growth10k[-1] / growth10k[mthOffset] - 1
                ytdReturn.append(ytd)

            if i > 35:
                threeYearReturn.append((growth10k[-1] / growth10k[-37]) ** (1 / 3) - 1)
            if i > 59:
                fiveYearReturn.append((growth10k[-1] / growth10k[-61]) ** (1 / 5) - 1)
            if i > 119:
                tenYearReturn.append((growth10k[-1] / growth10k[-121]) ** (1 / 10) - 1)

        myirr = (1 + np.irr(irrFlow)) ** min(12, len(allReportableKeys)) - 1
        print("IRR is {0:.3%}".format(myirr))
        print("1mth is {0:.3%}".format(oneMonthReturn[-1]))
        print("3mth is {0:.3%}".format(threeMonthReturn[-1]))
        print("6mth is {0:.3%}".format(sixMonthReturn[-1]))
        print("YTD is {0:.3%}".format(ytdReturn[-1]))
        print("1y is {0:.3%}".format(oneYearReturn[-1]))
        print("3y is {0:.3%}".format(threeYearReturn[-1]))
        return myirr


if __name__ == '__main__':

    # Read all mospire CSVs in the processed folder
    for broker in glob.glob(processed_folder+'/*'):
        for filename in glob.glob(broker+'/*-mospire.csv'):
            tokens = re.split('/|\.',filename)
            brokerName = tokens[4]
            accountName = tokens[5]
            ledger = {} # map of dates to LedgerEntry
            with open(filename, mode='r') as mospire_file:
                csvReader = csv.reader(mospire_file, delimiter=',')
                for row in csvReader:
                    stmtDate = datetime.strptime(row[0], '%Y-%m')
                    ledger[stmtDate] = LedgerEntry(balance=float(row[1]),flow=float(row[2]))

            # Convert the raw transaction data into monthly summaries of flow and an end of month balance

    # establish a common target date range for the IRR calculation

    # Target last month
    today = datetime.today()
    firstOfMonth = today.replace(day=1)
    lastMonth = firstOfMonth - timedelta(days=1)
    targetMonth = lastMonth.replace(day=1)

    # Ensure we compare the same date range across all accounts
    earliestStatements = []
    # pp.pprint(ledger)
    allDates = list(ledger.keys())
    allDates.sort()
    earliestStatements.append(allDates[0])  # append the first date time in the data
    latestStatement = allDates[-1]
    earliestStatements.sort()
    self.startDate = earliestStatements[-1]

    # Calculate IRR for each account using the common date range
            irr = irrcalc.get_irr(target_month)



