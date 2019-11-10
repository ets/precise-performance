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
            self.add_account_ledger_entry(entry_date,flow=ledger[entry_date].flow,balance=ledger[entry_date].balance)

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
        monthly_performance = []
        irr_flow = []
        ytd_return = None

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


        for mth in range(len(target_range)):
            monthly_performance.append( (growth_10k[-1] / growth_10k[-(mth+1)]) ** (1 / (int((mth-1)/12)+1) ) - 1)

        months_calculated = len(growth_10k)
        if months_calculated > key.month:
            ytd_return = (growth_10k[-1] / growth_10k[-key.month - 1]) - 1

        myirr = (1 + np.irr(irr_flow)) ** min(12, len(target_range)) - 1

        return { "start":start_month.strftime("%Y-%m"), "end":target_month.strftime("%Y-%m"), "irr":myirr, "ytd":ytd_return, "monthly_performance":monthly_performance}


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
        for filename in glob.glob(broker+'/*Traditional IRA-mospire.csv'):
            print("Reading account data from {}".format(filename))
            tokens = re.split('/|\.',filename)
            broker_name = tokens[4]
            account_name = tokens[5]
            ledger = {} # map of dates to LedgerEntry
            with open(filename, mode='r') as mospire_file:
                csv_reader = csv.reader(mospire_file, delimiter=',')
                for row in csv_reader:
                    stmt_date = datetime.strptime(row[0], '%Y-%m').date()
                    ledger[stmt_date] = LedgerEntry(balance=float(row[2]), flow=float(row[1]))

            # Convert the raw transaction data into monthly summaries of flow and an end of month balance
            performance_calculator.add_account_ledger(ledger)

    performance_results = performance_calculator.get_performance_results()
    print("\nThe internal rate of return from {} to {} of all accounts was {:.3%}".format(performance_results["start"], performance_results["end"], performance_results["irr"]))
    if performance_results["ytd"]:  print("YTD is {0:.3%}".format(performance_results["ytd"]))
    for mth_idx in range(1,len(performance_results["monthly_performance"])):
        print("{0}th is {1:.3%}".format(mth_idx,performance_results["monthly_performance"][mth_idx]))




