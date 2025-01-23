from urllib.request import Request, urlopen 
from bs4 import BeautifulSoup
import json
import re

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
import time



url = "https://www.lieferando.de/speisekarte/gastrooma-mnchen?utm_campaign=foodorder&utm_medium=organic&utm_source=google&shipping=delivery&rwg_token=AJKvS9X6iWbr8a6ECZAx_sfRF8_JtHQWAbX8HYfKbuGk7G-IMB3SyPoZ5aPRsMZHYGXanDfa4iWezXLUTldufH2BSRDxanOecA%3D%3D"
#url = "https://www.lieferando.de/speisekarte/dodo-pizza-1"


def accept_cookies(driver):
    try:
        cookie_banner = driver.find_element(By.TAG_NAME, 'pie-cookie-banner')
        shadow_root = driver.execute_script('return arguments[0].shadowRoot', cookie_banner)
        accept_cookies_button = shadow_root.find_element(By.CSS_SELECTOR, 'pie-button[data-test-id="actions-necessary-only"]')
        accept_cookies_button.click()
        print("Accepted necessary cookies")
    except Exception as e:
        print(f"Failed to accept necessary cookies: {e}")



def get_restaurant_address(driver):
    response = {"street": "", "number": "", "error": False}
    try: 
        data_script = driver.find_element(By.XPATH, '//script[@type="application/ld+json"]')
        json_data = data_script.get_attribute("innerHTML")
        data = json.loads(json_data)
        street_address = data.get("address", {}).get("streetAddress", {})
        
        if not street_address:
            response["error"] = True
            return response
        
        # Avoids extra information that could be given after symbols , . (
        regex_match = re.match(r'^[^,(.]+', street_address)
        if not regex_match:
            response["error"] = True
            return response
        
        clean_street_address = regex_match.group(0).strip()
        response["street"] = clean_street_address

        # finding house number
        regex_match2 = re.search(r'\b\d+[a-zA-Z]?\b', clean_street_address)
        if regex_match2:
            street_number = regex_match2.group()
            response["number"] = street_number

    except Exception as e:
        print(f"Failed to extract street address: {e}")
        response["error"] = True
    
    finally:
        return response
    


def provide_location(driver, street: str, number: str):
    try:
        input_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@aria-label="Ort suchen"]'))
        )
        print("found locaton input element")
        
        if input_element:
            location = street
            
            if number:
                location += f" {number}"

            input_element.send_keys(location) 
            time.sleep(1)   
            li_location_option = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//li[@role="option"]'))
            )

            if li_location_option:
                li_location_option.click()
                print("Clicked location suggestion")
                
                input_house_number = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Enter building number or name"]'))
                )

                if input_house_number:
                    # "1" as fallback value that will 100% exist (real address)
                    input_house_number.send_keys(number if number else "1")
                    button_confirm = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, '//button[@data-qa="location-panel-street-number"]'))
                    )

                    if button_confirm:
                        button_confirm.click()
                        print("Clicked confirm address button")
                        time.sleep(1)
                    else:
                        button_confirm_disabled = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, '//button[@data-qa="location-panel-street-number-disabled"]'))
                        )
                        if button_confirm_disabled:
                            print("Error: 'Confirm address' button is disabled.")
                        else:
                            print("Unexpected error occured when clicking confirm button")
                else:
                    print("House number input either wasn't required or failed to appear")

            else:
                print("Failed to find and click location suggestion <li> element")

        else:
            print("Failed to locate location input element")
    except Exception as e:
        print(f"Unexpected error when providing location: {e}")



# Finds and clicks 1st food item in 1st food category to trigger Lieferando's location modal
# Afterwards location is bypassed with provide_location() above
def handle_location_popup(driver, street, number):
    try:
        section_food_1 = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//section[@data-qa="item-category"]'))
        )
        print("Triggering location popup: found 1st food section")
        div_food_1 = section_food_1.find_element(By.XPATH, './/div[@role="button"]')
        print("Triggering location popup: found 1st food item in section")
        div_food_1.click()
        print("Triggering location popup: clicked food item")
        time.sleep(1)

        provide_location(driver, street, number)
        
        # now need to close opened item card
        close_food_item_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@data-qa="item-details-card"]//span[@role="button"]'))
        )
        print("found 'close' button on 1st food item")
        close_food_item_button.click()
        print("pressed 'close' button on 1st food item")

    except Exception as e:
        print(f"Unexpected error when triggering location popup to appear: {e}")



# function that extracts data from single food item 
def extract_food_item_data(driver, item, category_name):
    response = {
        "category": category_name, 
        "title": "", 
        "details": "", 
        "product_info": "",
        "price": "",
        "img_url": ""
    }
    try:
        item.click()
        
        # extracting food item name
        h2_food_name = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.XPATH, '//div[@data-qa="item-details-card"]//h2[@data-qa="heading"]'))
        )
        response["title"] = h2_food_name.text
        
        # extracting general food details 
        div_food_details = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.XPATH, '//div[@data-qa="item-details-card"]//div[@data-qa="text"]'))
        )
        response["details"] = div_food_details.text  

        # extracting food item image src
        img = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.XPATH, '//div[@data-qa="item-details-card"]//img'))
        )
        response["img_url"] = img.get_attribute("src")
        
        # close food item (acts as real user)
        close_food_item_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@data-qa="item-details-card"]//span[@role="button"]'))
        )
        close_food_item_button.click()
        print("Closed food item successfully.")
        time.sleep(0.5)
        print("\n")
        print(response)
        print("\n")

    except Exception as e:
        print(f"Unexpected error when extracting data from a list item: {e}")



# main function for handling data extraction
def handle_data_extraction(driver):
    extracted_data = []
    food_sections = driver.find_elements(By.XPATH, '//section[@data-qa="item-category"]')
    index = 0

    for section in food_sections:

        if index == 0:
            h2_food_section= section.find_element(By.XPATH, './/div//h2[@data-qa="heading"]')
            
            if h2_food_section:
                food_category = h2_food_section.text
                print(f"Found food category name: '{food_category}'")
                
                # <li> items aren't clickable but their deep indirect children divs are
                clickable_food_items = section.find_elements(By.XPATH, './/div[@role="button"]')
                print("Found all clickable food item button divs")

                # going through every food item
                for item in clickable_food_items:
                    extract_food_item_data(driver, item, food_category)

            else:
                print("Failed to find food section name")
        index += 1


def main():
    try:
        #request = Request(url=url, headers={'User-Agent': 'Mozilla/5.0'})
        #data = urlopen(request).read()
        #soup = BeautifulSoup(data, "html.parser")
        
        options = uc.ChromeOptions()
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.geolocation": 2  # Block geolocation requests
        })
        driver = uc.Chrome(use_subprocess=False, headless=False, options=options)
        driver.get(url)
        time.sleep(5)
        accept_cookies(driver)
        
        addr = get_restaurant_address(driver)
        if not addr["error"]:
            print(f"Got the address! \nStreet: {addr["street"]} House number: {addr["number"]}")
            handle_location_popup(driver, addr["street"], addr["number"])
            print("Started data extraction...")
            handle_data_extraction(driver)
        else:
            print("Error trying to obtain restaurant address. Closing driver...")
        

        driver.close() # closes the tab opened by driver
        driver.quit() # quits driver completely
    
        '''list_item = soup.find('li', {'data-item-id': "929076143"})
        if list_item:
            
            # finding title
            h2_element = list_item.find('h2') 
            if h2_element:
                print(f"Title DE: {h2_element.text}")
            else:
                print("No <h2> element found inside this <li> element.") 
            
            # finding details
            details_div = list_item.find('div', {'data-qa': 'text'})
            if details_div:
                print(f"Product Details DE: {details_div.text}")
            else:
                print("No <div> element with attribute 'data-qa' found inside this <li> element")
            
            # Use Playwright to click the button and extract the product info dynamically
            with sync_playwright() as playwright:
                run(playwright=playwright, url=url)
                
        else:
            print("No <li> element found")'''
        

    except Exception as e:
        print(f"An error has occured: {e}")

if __name__ == "__main__":
    main()

