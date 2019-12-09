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
        self._driver.get("https://personal.vanguard.com/web/cfv/secure-overview-webapp/")

        # wait = WebDriverWait(driver, 300)
        # element = wait.until(EC.element_to_be_clickable((By.ID, 'USER')))
        #
        # self._driver.find_element(By.ID, "USER").click()
        # self._driver.find_element(By.ID, "USER").send_keys("Your username")
        # self._driver.find_element(By.ID, "PASSWORD").click()
        # self._driver.find_element(By.ID, "PASSWORD").send_keys("Your password")
        # self._driver.find_element(By.CSS_SELECTOR, "span:nth-child(2) > .vuiButton").click()

        element = wait.until(EC.element_to_be_clickable((By.ID, 'sncTabSetActivityTab')))
        element.click()
        element = wait.until(EC.element_to_be_clickable((By.ID, 'statementsNavigation')))
        element.click()

        option_texts = []
        years_table = self._driver.find_element(By.CSS_SELECTOR, ".vg-SelOneMenuDropDownScroll > table")
        for row in years_table.find_elements(By.XPATH, ".//tbody/tr"):
            option_texts.append(row.find_element(By.XPATH, ".//td").get_attribute('value'))
        for option in option_texts:
            if self.year_matcher.match(option):
                print("Processing "+option)

                element = self._driver.find_element(By.CSS_SELECTOR, "body")
                actions = ActionChains(self._driver)
                actions.move_to_element(element).perform()

                print("Selecting option")
                self._driver.find_element(By.ID, "StmtSummaryForm:YearFilterMenu_text").click()
                self._driver.find_element(By.ID, "StmtSummaryForm:YearFilterMenu_aTag").click()
                print("Looking for: "+option)
                element = wait.until(EC.element_to_be_clickable((By.XPATH, ".//*[@id='scroll-StmtSummaryForm:YearFilterMenu']//td[contains(.,'"+option+"')]")))
                element.click()
                
                element = self._driver.find_element(By.CSS_SELECTOR, ".selected")
                actions = ActionChains(self._driver)
                actions.move_to_element(element).perform()
                self._driver.find_element(By.ID, "StmtSummaryForm:goFilterButtonInput").click()
                print("Clicked the update button")
                # wait until the dropdown shows that current option is selected
                wait.until(EC.text_to_be_present_in_element( (By.XPATH, ".//*[@id='StmtSummaryForm:stmtDataTabletbody0']//tr[2]/td[1]"), option ))

                print("Looking for data table rows")
                for row in self._driver.find_elements(By.XPATH,".//*[@id='StmtSummaryForm:stmtDataTabletbody0']//tr"):
                    links = row.find_elements(By.CSS_SELECTOR, "a")
                    if len(links) == 1:
                        # print("Looking for date")
                        # print(row.get_attribute('innerHTML'))
                        stmt_date = row.find_element(By.XPATH, ".//td[1]").text
                        print("Parsing row for "+stmt_date)
                        pdfFilename = self._raw_data_dir + datetime.strptime(stmt_date, '%m/%d/%Y').strftime("%y%m%d") + '.pdf'
                        uniq = 2
                        offset = 6 + len(self._raw_data_dir)
                        while os.path.isfile(pdfFilename):
                            pdfFilename = pdfFilename[:offset] + '.' + str(uniq) + pdfFilename[-4:]
                            uniq = uniq + 1

                        links[0].click()
                        print("Waiting on download for "+stmt_date)
                        filename = self.download_wait()
                        if filename:
                            os.rename(self._temp_dwnld_dir+filename, pdfFilename)
                            print("Download complete as: "+pdfFilename)
                        else:
                            print("Timed out: failed to download statement for "+stmt_date)




rel_raw_data_dir = "data/raw/vanguard/"
rel_download_dir = "data/temp/"

os.makedirs(name=rel_raw_data_dir,exist_ok=True)
os.makedirs(name=rel_download_dir,exist_ok=True)
files = glob.glob(rel_download_dir+"*")
for f in files:
    print("Removing file from temp download dir: "+f)
    os.remove(f)

options = Options()
options.headless = False

profile = webdriver.FirefoxProfile()
profile.set_preference("browser.preferences.instantApply",True)
profile.set_preference("browser.helperApps.neverAsk.openFile", "application/pdf, application/octet-stream, application/x-winzip, application/x-pdf, application/x-gzip")
profile.set_preference("pdfjs.disabled", True);
profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf,application/octet-stream")
profile.set_preference("browser.helperApps.alwaysAsk.force",False)
profile.set_preference("browser.download.manager.showWhenStarting",False)
profile.set_preference("browser.download.folderList",2)
profile.set_preference("browser.download.dir", os.getcwd()+"/"+rel_download_dir)
profile.set_preference("plugin.disable_full_page_plugin_for_types", "application/pdf")

driver = webdriver.Firefox(options=options,firefox_profile=profile)
driver.set_window_size(1440, 900)

dwnld = StatementDownloader(driver=driver,temp_dwnld_dir=rel_download_dir, raw_data_dir=rel_raw_data_dir)
dwnld.downloadStatements()

driver.close()

