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

    def __init__(self):
        self.aggregated_ledgers = {}

    def addLedger(self, ledger_name, ledger):
        monthly_summaries = {}
        for entry_date in list(ledger.keys()):
            #TODO use more python fu here, we're just reducing the map to a single summed entry for each month
            stmt_key = datetime.strptime(str(entry_date.year) + "-" + str(entry_date.month), '%Y-%m')
            if stmt_key in monthly_summaries:
                monthly_summaries[stmt_key].flow += ledger[entry_date].flow
                monthly_summaries[stmt_key].balance += ledger[entry_date].balance
            else:
                monthly_summaries[stmt_key] = ledger[entry_date]

        self.aggregated_ledgers[ledger_name] = monthly_summaries


    def get_irr(self, ledger_name, start_month, target_month):

        target_ledger = self.aggregated_ledgers[ledger_name]

        if target_ledger is None:
            raise ValueError("Ledger named {} not found.".format(ledger_name))

        ledger_range = list(target_ledger.keys())
        ledger_range.sort()

        if ledger_range[-1] < target_month:
            raise ValueError("Ledger does not cover targeted month {}".format(target_month))

        if ledger_range[0] > start_month:
            raise ValueError("Ledger does not cover start month")


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

        for i in range(len(ledger_range)):
            key = ledger_range[i]

            # Only report on keys that fall within our StartDate and TargetMonth window
            if key < start_month or key > target_month:
                continue

            prior_key = ledger_range[i - 1]
            entry = target_ledger[key]
            prior_entry = target_ledger[prior_key]
            open_balance = prior_entry.balance
            close_balance = entry.balance
            flow = entry.flow
            month_return = 0
            if open_balance + flow > 0:
                month_return = (close_balance - flow / 2) / (open_balance + flow / 2) - 1
            growth_10k.append(growth_10k[len(growth_10k) - 1] * (1 + month_return))
            one_month_return.append(month_return)
            if i == 1:
                irr_flow.append(-(open_balance + flow / 2))
            else:
                flow_entry = -flow / 2 + close_balance
                if i + 1 < len(ledger_range):
                    next_key = ledger_range[i + 1]
                    next_entry = target_ledger[next_key]
                    flow_entry = -(flow / 2 + next_entry.flow / 2)
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

            if i > 35:
                three_year_return.append((growth_10k[-1] / growth_10k[-37]) ** (1 / 3) - 1)
            if i > 59:
                five_year_return.append((growth_10k[-1] / growth_10k[-61]) ** (1 / 5) - 1)
            if i > 119:
                ten_year_return.append((growth_10k[-1] / growth_10k[-121]) ** (1 / 10) - 1)

        myirr = (1 + np.irr(irr_flow)) ** min(12, len(ledger_range)) - 1
        print("IRR is {0:.3%}".format(myirr))
        print("1mth is {0:.3%}".format(one_month_return[-1]))
        print("3mth is {0:.3%}".format(three_month_return[-1]))
        print("6mth is {0:.3%}".format(six_month_return[-1]))
        print("YTD is {0:.3%}".format(ytd_return[-1]))
        print("1y is {0:.3%}".format(one_year_return[-1]))
        print("3y is {0:.3%}".format(three_year_return[-1]))
        return myirr


if __name__ == '__main__':

    irr_calculator = IRRCalculator()
    # Read all mospire CSVs in the processed folder
    for broker in glob.glob(processed_folder+'/*'):
        for filename in glob.glob(broker+'/*-mospire.csv'):
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
            ledger_name = broker_name+"-"+account_name
            irr_calculator.addLedger(ledger_name,ledger)

            # Target last month
            today = datetime.today()
            last_month = today.replace(day=1) - timedelta(days=1)
            target_month = last_month.replace(day=1)
            # override the above with an target in range
            target_month = list(ledger.keys())[-1]

            # Start at the beginning
            start_month = list(ledger.keys())[0]

            irr_calculator.get_irr(ledger_name,start_month,target_month)


