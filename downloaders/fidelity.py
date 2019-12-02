from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
import time, os, glob, re
from datetime import datetime

class StatementDownloader():
    year_matcher = re.compile('^\d{4}$')

    def __init__(self, driver, temp_dwnld_dir, raw_data_dir, download_timeout=5):
        self._driver = driver
        self._temp_dwnld_dir = temp_dwnld_dir
        self._download_timeout = download_timeout
        self._raw_data_dir = raw_data_dir

    def wait_for_window(self, timeout=2):
        time.sleep(round(timeout / 1000))
        wh_now = self._driver.window_handles
        wh_then = self.vars["window_handles"]
        if len(wh_now) > len(wh_then):
            return set(wh_now).difference(set(wh_then)).pop()

    def download_wait(self):
        seconds = 0
        while seconds < self._download_timeout:
            files = os.listdir(self._temp_dwnld_dir)
            if len(files) > 0:
                for fname in files:
                    if not fname.endswith('.part'):
                        return fname
            time.sleep(0.2)
            seconds += 0.2

        return None

    def downloadStatements(self):
        self._driver.get("https://www.fidelity.com/")

        wait = WebDriverWait(driver, 300)
        element = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, 'Statements')))
        element.click()

        dropdown = self._driver.find_element(By.ID, "select")
        option_texts = []
        for o in dropdown.find_elements(By.XPATH, ".//option"):
            option_texts.append(o.text)
        print(option_texts)
        for option in option_texts:
            if self.year_matcher.match(option):
                print("Processing "+option)
                self._driver.find_element(By.XPATH, ".//option[. = '"+option+"']").click()
                self._driver.find_element(By.CSS_SELECTOR, ".drp-down-box > .muchsmaller").click()
                # actions = ActionChains(self._driver)
                # actions.move_to_element(go_btn).release().perform()
                # go_btn.click()
                print("Selecting data table")
                data_tables = self._driver.find_elements(By.CSS_SELECTOR, ".statement-data-table > table")
                rows = data_tables[1].find_elements(By.XPATH,".//tbody/tr");
                for row in rows:
                    csv_links = row.find_elements(By.CSS_SELECTOR, ".no-rt-border > a")
                    has_csv_stmt = len(csv_links) > 0
                    if has_csv_stmt:
                        stmt_date = row.find_element(By.XPATH, ".//th/abbr").text
                        print("Parsing row for "+stmt_date)
                        csvFilename = self._raw_data_dir + datetime.strptime(stmt_date, '%m/%d/%Y').strftime("%y%m%d") + '.csv'
                        uniq = 2
                        while os.path.isfile(csvFilename):
                            csvFilename = csvFilename[:-4] + '.' + str(uniq) + csvFilename[-4:]
                            uniq = uniq + 1

                        csv_links[0].click()
                        print("Waiting on download for "+stmt_date)
                        filename = self.download_wait()
                        if filename:
                            os.rename(self._temp_dwnld_dir+filename, csvFilename)
                            print("Download complete as: "+csvFilename)
                        else:
                            print("Timed out: failed to download statement for "+stmt_date)




rel_raw_data_dir = "data/raw/fidelity/"
rel_download_dir = "data/temp/"

os.makedirs(name=rel_download_dir,exist_ok=True)
files = glob.glob(rel_download_dir+"*")
for f in files:
    print("Removing file from temp download dir: "+f)
    os.remove(f)

options = Options()
options.headless = False

profile = webdriver.FirefoxProfile()
profile.set_preference("browser.preferences.instantApply",True)
profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/plain, application/octet-stream, application/binary, text/csv, application/csv, application/excel, text/comma-separated-values, text/xml, application/xml")
profile.set_preference("browser.helperApps.alwaysAsk.force",False)
profile.set_preference("browser.download.manager.showWhenStarting",False)
profile.set_preference("browser.download.folderList",2)
profile.set_preference("browser.download.dir", os.getcwd()+"/"+rel_download_dir)


driver = webdriver.Firefox(options=options,firefox_profile=profile)
driver.set_window_size(1440, 900)

dwnld = StatementDownloader(driver=driver,temp_dwnld_dir=rel_download_dir, raw_data_dir=rel_raw_data_dir)
dwnld.downloadStatements()

driver.close()
