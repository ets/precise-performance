import glob, pprint, csv, re
from collections import namedtuple
from datetime import datetime, timedelta
import numpy as np

processed_folder = './data/processed'
pp = pprint.PrettyPrinter(indent=4)

LedgerEntry = namedtuple('LedgerEntry', ['flow', 'balance'])
PerformanceResults = namedtuple('PerformanceResults', ['start', 'end', 'irr','one_month','three_month','six_month','ytd','one_year','three_year','five_year','ten_year'])

"""
Utility class for calculating ledger performance
        
"""

class PerformanceCalculator():

    def __init__(self):
        self.aggregated_ledger = {}

    def add_account_ledger_entry(self, entry_date, flow, balance):
        stmt_key = datetime.strptime(str(entry_date.year) + "-" + str(entry_date.month), '%Y-%m')
        if stmt_key in self.aggregated_ledger:
            combined_flow = flow + self.aggregated_ledger[stmt_key].flow
            combined_balance = balance + self.aggregated_ledger[stmt_key].balance
            self.aggregated_ledger[stmt_key] = LedgerEntry(balance=combined_balance, flow=combined_flow)
        else:
            self.aggregated_ledger[stmt_key] = LedgerEntry(balance=balance, flow=flow)

    def add_account_ledger(self, ledger):
        for entry_date in list(ledger.keys()):
            self.add_account_ledger_entry(entry_date,ledger[entry_date].flow,ledger[entry_date].balance)

    def get_performance_results(self, start_month, target_month):

        ledger_range = list(self.aggregated_ledger.keys())
        ledger_range.sort()

        if len(ledger_range) < 2:
            raise ValueError("Ledger must contain at least two month's of entries for an IRR calculation.")

        if ledger_range[-1] < target_month:
            raise ValueError("Ledger does not cover targeted month {}".format(target_month))


        growth_10k = [10000]
        one_month_return = []
        three_month_return = []
        six_month_return = []
        ytd_return = []
        one_year_return = []
        three_year_return = []
        five_year_return = []
        ten_year_return = []
        irr_flow = []

        for i in range(len(ledger_range) - 1):
            key = ledger_range[i + 1]

            # Only report on keys that fall within our StartDate and TargetMonth window
            if key < start_month or key > target_month:
                continue

            prior_key = ledger_range[i]
            entry = self.aggregated_ledger[key]
            prior_entry = self.aggregated_ledger[prior_key]
            open_balance = prior_entry.balance
            close_balance = entry.balance
            # print("Aggregated close balance for {} was {}".format(key,close_balance))
            flow = entry.flow
            month_return = 0
            if (open_balance + flow)/2 != 0:
                month_return = (close_balance - flow / 2) / (open_balance + flow / 2) - 1
            growth_10k.append( growth_10k[len(growth_10k) - 1] * (1 + month_return))
            one_month_return.append(month_return)
            if i == 1:
                irr_flow.append(-(open_balance + flow / 2))
            else:
                # Need special handling for the last loop iteration
                if i + 2 < len(ledger_range):
                    next_key = ledger_range[i + 2]
                    next_entry = self.aggregated_ledger[next_key]
                    flow_entry = -(flow / 2 + next_entry.flow / 2)
                else:
                    flow_entry = -flow / 2 + close_balance
                irr_flow.append(flow_entry)

            if i > 2:
                three_month_return.append(growth_10k[-1] / growth_10k[-4] - 1)
            if i > 5:
                six_month_return.append(growth_10k[-1] / growth_10k[-7] - 1)
            if i > 11:
                one_year_return.append(growth_10k[-1] / growth_10k[-13] - 1)
                ytd = 0
                mth_offset = i + 1 - key.month
                if growth_10k[mth_offset] != 0:
                    ytd = growth_10k[-1] / growth_10k[mth_offset] - 1
                ytd_return.append(ytd)
            # TODO this YTD calculation is suspect...
            if i > 35:
                three_year_return.append((growth_10k[-1] / growth_10k[-37]) ** (1 / 3) - 1)
            if i > 59:
                five_year_return.append((growth_10k[-1] / growth_10k[-61]) ** (1 / 5) - 1)
            if i > 119:
                ten_year_return.append((growth_10k[-1] / growth_10k[-121]) ** (1 / 10) - 1)


        myirr = (1 + np.irr(irr_flow)) ** min(12, len(ledger_range)) - 1


        return PerformanceResults(start=start_month,end=target_month,irr=myirr,
                                  ytd=ytd_return[-1] if len(ytd_return) > 0 else None,
                                  one_month=one_month_return[-1] if len(one_month_return) > 0 else None,
                                  three_month=three_month_return[-1] if len(three_month_return) > 0 else None,
                                  six_month=six_month_return[-1] if len(six_month_return) > 0 else None,
                                  one_year=one_year_return[-1] if len(one_year_return) > 0 else None,
                                  three_year=three_year_return[-1] if len(three_year_return) > 0 else None,
                                  five_year=five_year_return[-1] if len(five_year_return) > 0 else None,
                                  ten_year=ten_year_return[-1] if len(ten_year_return) > 0 else None)


    def get_earliest_statement_month(self):
        stmts = list(self.aggregated_ledger.keys())
        stmts.sort()
        if len(stmts) < 1:
            raise ValueError("No account statement data is present in the ledger")
        return stmts[0]

    def get_latest_statement_month(self):
        stmts = list(self.aggregated_ledger.keys())
        stmts.sort()
        if len(stmts) < 1:
            raise ValueError("No account statement data is present in the ledger")
        return stmts[-1]

if __name__ == '__main__':

    performance_calculator = PerformanceCalculator()
    # Read all mospire CSVs in the processed folder
    for broker in glob.glob(processed_folder+'/*'):
        for filename in glob.glob(broker+'/*-mospire.csv'):
            print("Reading account data from {}".format(filename))
            tokens = re.split('/|\.',filename)
            broker_name = tokens[4]
            account_name = tokens[5]
            ledger = {} # map of dates to LedgerEntry
            with open(filename, mode='r') as mospire_file:
                csv_reader = csv.reader(mospire_file, delimiter=',')
                for row in csv_reader:
                    stmt_date = datetime.strptime(row[0], '%Y-%m')
                    ledger[stmt_date] = LedgerEntry(balance=float(row[1]), flow=float(row[2]))

            # Convert the raw transaction data into monthly summaries of flow and an end of month balance
            performance_calculator.add_account_ledger(ledger)

    # Start at the beginning
    start_month = performance_calculator.get_earliest_statement_month()

    # Target last month
    target_month = performance_calculator.get_latest_statement_month()

    performance_results = performance_calculator.get_performance_results(start_month, target_month)
    print("\nThe internal rate of return from {:%Y-%m} to {:%Y-%m} of all accounts was {:.3%}".format(start_month, target_month, performance_results.irr))
    if performance_results.one_month:  print("1mth is {0:.3%}".format(performance_results.one_month))
    if performance_results.three_month:  print("3mth is {0:.3%}".format(performance_results.three_month))
    if performance_results.six_month:  print("6mth is {0:.3%}".format(performance_results.six_month))
    if performance_results.ytd:  print("YTD is {0:.3%}".format(performance_results.ytd))
    if performance_results.one_year:  print("1y is {0:.3%}".format(performance_results.one_year))
    if performance_results.three_year:  print("3y is {0:.3%}".format(performance_results.three_year))
    if performance_results.five_year:  print("5y is {0:.3%}".format(performance_results.five_year))
    if performance_results.ten_year:  print("10y is {0:.3%}".format(performance_results.ten_year))


