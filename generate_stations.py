from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pickle

class UKTrainStationScraper:
    # uses the wikipedia page https://en.wikipedia.org/wiki/UK_railway_stations
    # to create a dictionary where keys are station names and values are the matching
    # station codes
    def __init__(self):
        options = Options()
        self.browser = Chrome(options=options)
        self.url = "https://en.wikipedia.org/wiki/UK_railway_stations_%E2%80%93_"
        self.station_dict = {}

    def __del__(self):
        self.browser.close()

    def add_stations_to_dict(self):
        # iterates over every letter and adds all the stations that begin with
        # that letter and their code to station_dict
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for letter in letters:
            self.browser.get(self.url + letter)
            table_rows = self.browser.find_elements(By.CLASS_NAME, "vcard")
            for row in table_rows:
                row_elements = row.find_elements(By.TAG_NAME, "td")
                self.station_dict[row_elements[0].text] = row_elements[2].text
                # print(f"{row_elements[0].text} - {row_elements[2].text}")

    
scraper = UKTrainStationScraper()
scraper.add_stations_to_dict()

# save to pickle file station_list.pickle
with open("station_list.pickle", "wb") as file:
    pickle.dump(scraper.station_dict, file)