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
            self.browser.get(self.url + letter) # add the letter to the end of the url
            table_rows = self.browser.find_elements(By.TAG_NAME, "tr")

            for i in range(0, len(table_rows)): # for every row in the table
                if i != 0 and i != len(table_rows) - 1: # ignore the first and last rows
                    row_elements = table_rows[i].find_elements(By.TAG_NAME, "td") # get all columns for this row

                    if len(row_elements) >= 3: # check if the row is long enough to have a station name & code
                        self.station_dict[row_elements[0].text.lower()] = row_elements[2].text.lower()

    
scraper = UKTrainStationScraper()
scraper.add_stations_to_dict()

print(scraper.station_dict)

# save to pickle file station_list.pickle
# with open("./chatbot_data/station_list.pickle", "wb") as file:
#     pickle.dump(scraper.station_dict, file)