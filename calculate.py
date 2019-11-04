import glob, pprint, csv, re
from collections import namedtuple
from datetime import datetime
import numpy as np

processed_folder = './data/processed'
pp = pprint.PrettyPrinter(indent=4)

LedgerEntry = namedtuple('LedgerEntry', ['flow', 'balance'])

"""
Utility class for calculating ledger performance
        
"""

class PerformanceCalculator():

    def __init__(self):
        self.aggregated_ledger = {}

    def add_account_ledger_entry(self, entry_date, flow, balance):
        stmt_key = datetime.strptime(str(entry_date.year) + "-" + str(entry_date.month), '%Y-%m').date()
        if stmt_key in self.aggregated_ledger:
            combined_flow = flow + self.aggregated_ledger[stmt_key].flow
            combined_balance = balance + self.aggregated_ledger[stmt_key].balance
            self.aggregated_ledger[stmt_key] = LedgerEntry(balance=combined_balance, flow=combined_flow)
        else:
            self.aggregated_ledger[stmt_key] = LedgerEntry(balance=balance, flow=flow)

    def add_account_ledger(self, ledger):
        for entry_date in list(ledger.keys()):
            self.add_account_ledger_entry(entry_date,ledger[entry_date].flow,ledger[entry_date].balance)

    def get_performance_results(self, start_month=None, target_month=None):

        if start_month is None:
            start_month = self.get_earliest_statement_month()

        if target_month is None:
            target_month = self.get_latest_statement_month()

        ledger_range = list(self.aggregated_ledger.keys())
        ledger_range.sort()
        target_range = [i for i in ledger_range if i >= start_month and i <= target_month]

        if len(target_range) < 2:
            raise ValueError("Targeted range must contain at least two month's of entries for an IRR calculation.")

        if target_range[-1] < target_month:
            raise ValueError("Targeted range does not cover targeted month {}".format(target_month))


        growth_10k = [10000]
        one_month_return = []
        two_month_return = []
        three_month_return = []
        four_month_return = []
        five_month_return = []
        six_month_return = []
        ytd_return = []
        one_year_return = []
        three_year_return = []
        five_year_return = []
        ten_year_return = []
        irr_flow = []

        for i in range(len(target_range)):
            key = target_range[i]
            entry = self.aggregated_ledger[key]
            close_balance = entry.balance
            flow = entry.flow

            if i > 0:
                prior_key = target_range[i - 1]
                prior_entry = self.aggregated_ledger[prior_key]
                open_balance = prior_entry.balance
            else: # for first entry in ledger, infer the open balance
                open_balance = close_balance - flow
                # priming entry into IRR Flow is uniquely calculated
                irr_flow.append(-(open_balance + flow / 2))

            # IRR Flow calculation needs special handling for the last loop iteration
            if i + 1 < len(target_range):
                next_key = target_range[i + 1]
                next_entry = self.aggregated_ledger[next_key]
                flow_entry = -(flow / 2 + next_entry.flow / 2)
            else:
                flow_entry = -flow / 2 + close_balance
            irr_flow.append(flow_entry)

            # print("Aggregated close balance for {} was {}".format(key,close_balance))

            month_return = 0
            if (open_balance + flow)/2 != 0:
                month_return = (close_balance - flow / 2) / (open_balance + flow / 2) - 1
            growth_10k.append( growth_10k[len(growth_10k) - 1] * (1 + month_return))
            one_month_return.append(month_return)
            if i > 1:
                two_month_return.append(growth_10k[-1] / growth_10k[-4] - 1)
            if i > 2:
                three_month_return.append(growth_10k[-1] / growth_10k[-4] - 1)
            if i > 3:
                four_month_return.append(growth_10k[-1] / growth_10k[-4] - 1)
            if i > 4:
                five_month_return.append(growth_10k[-1] / growth_10k[-4] - 1)
            if i > 5:
                six_month_return.append(growth_10k[-1] / growth_10k[-7] - 1)
            if i > 11:
                one_year_return.append(growth_10k[-1] / growth_10k[-13] - 1)
            if i > 35:
                three_year_return.append((growth_10k[-1] / growth_10k[-37]) ** (1 / 3) - 1)
            if i > 59:
                five_year_return.append((growth_10k[-1] / growth_10k[-61]) ** (1 / 5) - 1)
            if i > 119:
                ten_year_return.append((growth_10k[-1] / growth_10k[-121]) ** (1 / 10) - 1)

            ytd = 0
            if len(growth_10k) > key.month:
                ytd = (growth_10k[-1] / growth_10k[ -key.month-1 ]) - 1
            ytd_return.append(ytd)

        myirr = (1 + np.irr(irr_flow)) ** min(12, len(target_range)) - 1


        return { "start":start_month.strftime("%Y-%m"), "end":target_month.strftime("%Y-%m"), "irr":myirr
                  , "ytd":ytd_return[-1] if len(ytd_return) > 0 else None
                  , "one_month":one_month_return[-1] if len(one_month_return) > 0 else None
                  , "two_month":two_month_return[-1] if len(two_month_return) > 0 else None
                  , "three_month":three_month_return[-1] if len(three_month_return) > 0 else None
                  , "four_month":four_month_return[-1] if len(four_month_return) > 0 else None
                  , "five_month":five_month_return[-1] if len(five_month_return) > 0 else None
                  , "six_month":six_month_return[-1] if len(six_month_return) > 0 else None
                  , "one_year":one_year_return[-1] if len(one_year_return) > 0 else None
                  , "three_year":three_year_return[-1] if len(three_year_return) > 0 else None
                  , "five_year":five_year_return[-1] if len(five_year_return) > 0 else None
                  , "ten_year":ten_year_return[-1] if len(ten_year_return) > 0 else None}


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
                    stmt_date = datetime.strptime(row[0], '%Y-%m').date()
                    ledger[stmt_date] = LedgerEntry(balance=float(row[1]), flow=float(row[2]))

            # Convert the raw transaction data into monthly summaries of flow and an end of month balance
            performance_calculator.add_account_ledger(ledger)

    performance_results = performance_calculator.get_performance_results()
    print("\nThe internal rate of return from {:%Y-%m} to {:%Y-%m} of all accounts was {:.3%}".format(performance_results["start"], performance_results["end"], performance_results["irr"]))
    if performance_results["one_month"]:  print("1mth is {0:.3%}".format(performance_results["one_month"]))
    if performance_results["three_month"]:  print("3mth is {0:.3%}".format(performance_results["three_month"]))
    if performance_results["six_month"]:  print("6mth is {0:.3%}".format(performance_results["six_month"]))
    if performance_results["ytd"]:  print("YTD is {0:.3%}".format(performance_results["ytd"]))
    if performance_results["one_year"]:  print("1y is {0:.3%}".format(performance_results["one_year"]))
    if performance_results["three_year"]:  print("3y is {0:.3%}".format(performance_results["three_year"]))
    if performance_results["five_year"]:  print("5y is {0:.3%}".format(performance_results["five_year"]))
    if performance_results["ten_year"]:  print("10y is {0:.3%}".format(performance_results["ten_year"]))


