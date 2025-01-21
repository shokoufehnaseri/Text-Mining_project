#booking.com scraper
#by 
# Shokoufe Naseri 466750
# Jan Szczepanek 463471

#note: Jupyter Notebook is not used in case you want to run it - the scraper is based on scrapy

import scrapy
from bs4 import BeautifulSoup
from booking_scraper.items import BookingItem
import re
from selenium import webdriver
import time
import pyautogui # for the date backup - brutal but will work 100% of the time if the other methods fail (they like to do that sometimes)
import numpy as np
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC

class BookingSpider(scrapy.Spider):
    name = 'booking' #we write this into cmd when we want to start the scraper
    allowed_domains = ['booking.com'] #self-explainatory
    start_urls = ['https://www.booking.com/berlin', 'https://www.booking.com/osaka', 'https://www.booking.com/warsaw'] #booking has this wonderful feature with its structure - we could even automate this in the future to just type in the cities
    check = 0 #this variable will come in handy later
#setup the driver
    def __init__(self, *args, **kwargs):
            super(BookingSpider, self).__init__(*args, **kwargs) #for starting the spider
            self.driver = webdriver.Chrome() #we're using firefox

    def parse(self, response):
        #fetch an url from the list
        self.driver.get(response.url)
        #wait for the cookies button for 5 seconds - booking doesn't really ban people and we're not doing anything illegal (we've read the tos)
        time.sleep(5)

        #try to find the cookies button
        cookies_button_xpath = '//*[@id="onetrust-accept-btn-handler"]'
        content = None
        try:
            content = self.driver.find_element("xpath", cookies_button_xpath) # finds the button
        except Exception as e:
            self.logger.error(f"Failed to find cookies button: {e}")# we will delete this later, now im just using it for debug
        #if the button exists, click it. if not, ignore it
        if content: content.click() # clicks the button
    #this next code is the date selector. Its written this way to have a backup. The xpaths dont work 100% of the time, hence we use pyautogui as a backup 
        try:
            if self.check == 0:
                start_xpath='//*[@id="calendar-searchboxdatepicker"]/div/div[1]/div/div[2]/table/tbody/tr[1]/td[4]/span' #start date button xpath
                WebDriverWait(self.driver, 15).until(EC.visibility_of_element_located((By.XPATH, start_xpath))) #wait and find the button
                start_date =  WebDriverWait(self.driver, 6).until(
                    EC.element_to_be_clickable((By.XPATH, start_xpath))
                )# relative xpath
                start_date.click() #click the button no1
                time.sleep(np.random.chisquare(1)+1)

                end_date_xpath='//*[@id="calendar-searchboxdatepicker"]/div/div[1]/div/div[2]/table/tbody/tr[1]/td[7]/span' #same goes here for the end date
                WebDriverWait(self.driver, 5).until(EC.visibility_of_element_located((By.XPATH, end_date_xpath)))
                end_date = WebDriverWait(self.driver, 6).until(
                    EC.element_to_be_clickable((By.XPATH, end_date_xpath))
                )
                time.sleep(np.random.chisquare(1)+1)
                end_date.click()
                self.check = 1 # indicate not to select the date again

        except:
            # the date version with pyautogui. We only do it once, if the check variable is == 0. It clicks the given pixels on the screen - a unelegant but effective method in case the primary method fails.
            search_button = None
            if self.check == 0:
                time.sleep(3)
                pyautogui.click(1358, 1050) #pixels for a 1920x1680 screen, that's why its the backup not the primary
                time.sleep(1)
                pyautogui.click(1427, 1050)
                time.sleep(2)


            time.sleep(5)
            self.check = 1 #change the check variable to 0, so that we dont choose the date for the second time. The date is stored in cache once chosen

#click the search button - this action is repeated for each city
        search_button = self.driver.find_element('xpath', "//div[contains(@class,'e22b782521 d12ff5f5bf')]//button[contains(@type,'submit')]")
        search_button.click()

#we have to click the genius button - this refers to some random loyalty programme
        button1 = None
        try:
            button1 = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//button[@aria-label="Dismiss sign-in info."]')))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", button1) #jumps to the button
            button1.click() #clicks the button
            print("Button clicked successfully!")
        except Exception as e:
            self.logger.error(f"Failed to find genius button: {e}")# we will delete this later, now im just using it for debug
        
        
        #this part scrolls down and loads in more hotels - we can extend it to load in large amounts of hotels, for now it loads them in once
        show_more_clicked = False #a check to do it once
        while not show_more_clicked:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") #this scrolls down
            try:
                show_more_button = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='c82435a4b8 f581fde0b8']//button[@type='button']")))
                show_more_button.click() #tries to click the button - if it succeeds then the loop turns off
                show_more_clicked = True
                break
            except:
                time.sleep(2)
                continue #if it doesnt find the button, the loop reiterates

        time.sleep(5) #the scraper waits so that the pages load in
        #the part below calls the next function - parse_hotel. 
        page_source = self.driver.page_source # we get the page source to plug into bs4 - so selenium downloads the links to the hotels, which are then scraped in the next function (parse_hotel)
        soup = BeautifulSoup(page_source, 'html.parser')
        hotel_links = []
        for a in soup.find_all('a', href=True): #we are getting the list of hotel links to then scrape (or scrap)
            if 'https://www.booking.com/hotel/' in a['href']: # we want just the hotel links, nothing more
                hotel_links.append(a['href'])
        for hotel_link in hotel_links: #this is where the fun part begins 
             yield response.follow(hotel_link, callback = self.parse_hotel) #this calls the next function, with the hotel link as the response variable for the next bs4 instance



#scraping the data from hotel sites with bs4 - this function iterates over all the links, as we can see above
    def parse_hotel(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h2', class_='d2fee87262 pp-header__title').get_text(strip=True) #strip whitespaces - later the .text method will be used
        address = soup.find('span', class_='hp_address_subtitle js-hp_address_subtitle jq_tooltip').get_text(strip=True)
        prereg_rating = soup.find('div', class_='a3b8729ab1 d86cee9b25').get_text(strip=True)
        rating = re.search(r'(\d+\.\d+)', prereg_rating) #we remove text to get just the digits
        if rating: rating = rating.group(1) #if a match is found, the main rating is set as the stripped value
        other_ratings = soup.find_all('div', class_='ccb65902b2 efcd70b4c4') # we get a list of ratings from the site. we have tried to get the ratings one by one but this has proven more effective
#the price part - a bit more complex, we have to find the table and then parse the table. for this, we had to use selenium, as bs4 does not really support xpaths
        find_element_by_xpath = lambda xpath: self.driver.find_element('xpath', xpath) # lambda function - it is not really useful and using it more than once caused the scraper to go crazy
        self.driver.get(response.url) #we plug selenium with the perticular hotels link
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        price_raw = find_element_by_xpath("//tr[contains(@class,'js-rt-block-row e2e-hprt-table-row hprt-table-cheapest-block hprt-table-cheapest-block-fix js-hprt-table-cheapest-block')]//td[contains(@class,'')]//div[contains(@class,'hprt-price-block')]//div[contains(@class,'prco-wrapper bui-price-display prco-sr-default-assembly-wrapper')]//div//div//div[contains(@class,'bui-price-display__value prco-text-nowrap-helper prco-inline-block-maker-helper prco-f-font-heading')]//span[@class='prco-valign-middle-helper']")
        price_reg = re.search(r'\d+', price_raw.text) #we remove 'zł'
        if price_reg: price = price_reg.group() #the same deal as with the rating. For some reason it works this way, i'm not sure how to explain it
        try:
            input = self.driver.find_element('xpath', "//input[@id=':re:']") # we get the city from the search input (which is apparently stored within cache) - its different often...
        except: 
            input = self.driver.find_element('xpath', "//input[@id=':rg:']") #...as such, we are prepared for all scenarios
        city = input.get_attribute("value") # as the input xpath leads us to a list of all this elements attributes, we select the value attribute which was autofilled.
    



#'saving' the scraped data - this goes through items.py, to the BookingItem() function. thats why we imported this file
        item = BookingItem()
        item['name'] = name
        item['address'] = address
        item['city'] = city
        item['rating'] = rating
        item['rating1'] = other_ratings[0].text #personell
        item['rating2'] = other_ratings[1].text #amenities
        item['rating3'] = other_ratings[2].text #comfort
        item['rating4'] = other_ratings[3].text # cleanliness
        item['rating5'] = other_ratings[4].text #subjective price/quality ratio 
        item['price'] = price


        yield item

