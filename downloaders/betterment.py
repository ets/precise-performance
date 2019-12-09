
import os

rel_raw_data_dir = "data/raw/betterment/"
os.makedirs(name=rel_raw_data_dir,exist_ok=True)
print("Just use the activity tab from Betterment portal to look at a large date range then click \"Load More Activities\" to see all desired entries.")
print("Download as CSV \"transactions.csv\" and save in "+rel_raw_data_dir)