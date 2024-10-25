import scrapy
from bs4 import BeautifulSoup
from booking_scraper.items import BookingItem
import re
from selenium import webdriver
import time
import pyautogui # for the date - brutal but will work

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

class BookingSpider(scrapy.Spider):
    name = 'booking'
    allowed_domains = ['booking.com']
    start_urls = ['https://www.booking.com/berlin', 'https://www.booking.com/osaka', 'https://www.booking.com/warsaw']
    check = 0
#the selenium part - scrolling through the site
    def __init__(self, *args, **kwargs):
            super(BookingSpider, self).__init__(*args, **kwargs)
            self.driver = webdriver.Firefox()

    def parse(self, response):
        self.driver.get(response.url)
        time.sleep(5)
        cookies_button_xpath = '//*[@id="onetrust-accept-btn-handler"]'
        content = None
        try:
            content = self.driver.find_element("xpath", cookies_button_xpath) # finds the button
        except Exception as e:
            self.logger.error(f"Failed to find cookies button: {e}")# we will delete this later, now im just using it for debug
        if content: content.click() # clicks the button
        
        search_button = None
        if self.check == 0:
            time.sleep(3)
            pyautogui.click(1358, 965)
            time.sleep(1)
            pyautogui.click(1427, 967)
            time.sleep(2)
        search_button = self.driver.find_element('xpath', "//div[contains(@class,'e22b782521 d12ff5f5bf')]//button[contains(@type,'submit')]")
        search_button.click()
            

        time.sleep(5)
        self.check = 1

#we have to click the genius button
        button1 = None
        try:
            button1 = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//button[@aria-label="Dismiss sign-in info."]')))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", button1) #jumps to the button
            button1.click() #clicks the button
            print("Button clicked successfully!")
        except Exception as e:
            self.logger.error(f"Failed to find genius button: {e}")# we will delete this later, now im just using it for debug

        #doesn't work for now
        # button = None
        # try:
        #     button = self.driver.find_element('xpath', "//div[@class='c82435a4b8 f581fde0b8']//button[@type='button']") #see more button
        #     self.driver.execute_script("arguments[0].scrollIntoView(true);", button) #jumps to the button
        #     button.click() #clicks the button
        #     print("Button clicked successfully!")
        # except Exception as e:
        #     self.logger.error(f"Failed to find load-more button: {e}")# we will delete this later, now im just using it for debug
        

        show_more_clicked = False
        while not show_more_clicked:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") #this scrolls fown
            try:
                show_more_button = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='c82435a4b8 f581fde0b8']//button[@type='button']")))
                show_more_button.click() #tries to click the button - if it succeeds then the loop turns off
                show_more_clicked = True
                break
            except:
                continue #if it doesnt find the button, the loop reiterates

        time.sleep(5) #the scraper waits so that the pages load in
        page_source = self.driver.page_source # we get the page source to plug into bs4
        soup = BeautifulSoup(page_source, 'html.parser')
        hotel_links = []
        for a in soup.find_all('a', href=True): #we are getting the list of hotel links to then scrape
            if 'https://www.booking.com/hotel/' in a['href']:
                hotel_links.append(a['href'])
        for hotel_link in hotel_links:
             yield response.follow(hotel_link, callback = self.parse_hotel)



#scraping the data from hotel sites
    def parse_hotel(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h2', class_='d2fee87262 pp-header__title').get_text(strip=True)
        address = soup.find('span', class_='hp_address_subtitle js-hp_address_subtitle jq_tooltip').get_text(strip=True)
        prereg_rating = soup.find('div', class_='a3b8729ab1 d86cee9b25').get_text(strip=True)
        rating = re.search(r'(\d+\.\d+)', prereg_rating)
        if rating: rating = rating.group(1)
        other_ratings = soup.find_all('div', class_='ccb65902b2 efcd70b4c4')
#the price part - a bit more complex, we have to find the table and then parse the table
        self.driver.get(response.url)
        price = self.driver.find_element('xpath', "//tr[contains(@class,'js-rt-block-row e2e-hprt-table-row hprt-table-cheapest-block hprt-table-cheapest-block-fix js-hprt-table-cheapest-block')]//td[contains(@class,'')]//div[contains(@class,'hprt-price-block')]//div[contains(@class,'prco-wrapper bui-price-display prco-sr-default-assembly-wrapper')]//div//div//div[contains(@class,'bui-price-display__value prco-text-nowrap-helper prco-inline-block-maker-helper prco-f-font-heading')]//span[@class='prco-valign-middle-helper']")



#'saving' the scraped data
        item = BookingItem()
        item['name'] = name
        item['address'] = address
        item['rating'] = rating
        item['rating1'] = other_ratings[0].text
        item['rating2'] = other_ratings[1].text
        item['rating3'] = other_ratings[2].text
        item['rating4'] = other_ratings[3].text
        item['rating5'] = other_ratings[4].text
        item['price'] = price.text


        yield item

