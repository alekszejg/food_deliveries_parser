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


def cleanup_driver(driver, quit=True):
    try:
        driver.close()  # Close the browser tab
        driver.quit()   # Quit the browser entirely  
        print("Driver successfully cleaned up.")
    except Exception as e:
        print(f"!!! Error during driver cleanup: {e}")
    finally:
        if quit:
            exit()


def initialize_driver(url):
    driver = None
    try:
        options = uc.ChromeOptions()
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.geolocation": 2  # Block geolocation requests
        })
        driver = uc.Chrome(use_subprocess=False, headless=False, options=options)
        driver.get(url)
        print("Initialized driver and accessed url.")
        return driver
    except Exception as e:
        print("!!! Error during driver initialization. {e}")
        if driver:
            cleanup_driver(driver)
        


def accept_cookies(driver):
    cookie_banner = None
    # accessing cookie banner element
    try:
        # check DOM presence not visibility, since it's shadow DOM
        cookie_banner = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'pie-cookie-banner'))
        )
    except: 
        print(f"!!! Error: cookie banner wasn't found.")
        cleanup_driver(driver)
    
    # accessing accept cookies button through shadow root
    try:   
        shadow_root = driver.execute_script('return arguments[0].shadowRoot', cookie_banner)
        accept_cookies_btn = shadow_root.find_element(By.CSS_SELECTOR, 'pie-button[data-test-id="actions-necessary-only"]')
        accept_cookies_btn.click()
        print("Accepted necessary cookies.")
    except Exception as e:
        print(f"!!! Unexpected Error during when accessing shadow root or its accept cookies button. {e}")
        cleanup_driver(driver)


def get_restaurant_address(driver):
    try: 
        script = driver.find_element(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
        json_data = script.get_attribute("innerHTML")
        data = json.loads(json_data)
        address = data.get("address", {}).get("streetAddress", {})
        
        if not address:
            print("!!! Error: address wasn't provided by restaurant")
            cleanup_driver(driver)
        
        # Avoids extra information after symbols ,.(
        regex_match1 = re.match(r'^[^,(.]+', address.strip())
        if not regex_match1:
            print("!!! Unexpected Error in regex during address cleanup")
            cleanup_driver(driver)
            
        clean_address = regex_match1.group(0).strip()
        street_number = None

        # check for street number
        regex_match2 = re.search(r'\b\d+[a-zA-Z]?\b', clean_address)
        if regex_match2:
            street_number = regex_match2.group()

        print(f"Obtained restaurant's address. Street: {clean_address}, number: {street_number}")
        return (clean_address, street_number)
            
    except Exception as e:
        print(f"!!! Unexpected Error during restaurant's address extraction. {e}")
        cleanup_driver(driver)
    
    

def fill_loc_prompt(driver, street, number):
    try:
        street_input = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[aria-label="Ort suchen"]'))
        )
        my_loc = f"{street} {number or ''}".strip()
        street_input.send_keys(my_loc)
    except Exception as e:
        print(f"! Unexpected Error when accessing location <input> element. {e}")
        cleanup_driver(driver)
    
    try:
        address_suggestion = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'li[role="option"]'))
        )
        address_suggestion.click()
    except Exception as e:
        print(f"!!! Unexpected Error when accessing or interacting with address suggestion. {e}")
        cleanup_driver(driver)

    street_num_input = None
    try:
        street_num_input = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[placeholder="Enter building number or name"]'))
        )
        street_num_input.send_keys(number if number else "1") # 1 as fallback
    except:
        print("Street number prompt didn't appear. Likely no error")
        return
    
    if street_num_input:
        try:
            confirm_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-qa="location-panel-street-number"]'))
            )
            confirm_button.click()
        except Exception as e:
            print(f"!!! Unexpected Error when accessing or interacting with 'Confirm Address' button. {e}")
            cleanup_driver(driver)
    
    

def handle_loc_prompt(driver, street, number):
    # Triggers Lieferando's location prompt to appear by clicking 1st menu item
    try:
        food_section_1 = driver.find_element(By.CSS_SELECTOR, 'section[data-qa="item-category"]')
        clickable_food_div = food_section_1.find_element(By.CSS_SELECTOR, 'div[role="button"]')
        clickable_food_div.click()
    except Exception as e:
        print(f"!!! Unexpected Error when triggering location popup to appear: {e}")
        cleanup_driver(driver)
    
    # Prompt should have appeared. Filling in the data...
    fill_loc_prompt(driver, street, number)

    # close food item card
    try:
        close_button = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.XPATH, '//div[@data-qa="item-details-card"]//span[@role="button"]'))
        )
        close_button.click()
    except Exception as e:
        print(f"!!! Unexpected Error during access or interaction with close button of food item. {e}")
        cleanup_driver(driver)

    print("Entered address was accepted. Proceeding with data parsing.")



def parse_food_item(driver, category):
    response = {
        "category": category, "title": "", "details": "", 
        "allergens": "", "price": "", "img_url": ""
    }

    # parsing food item's title/name
    try:
        h2 = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, 'h2'))
        )
        response["title"] = h2.text
        print(f"Food: {response["title"]}")
    except:
        print("!!! Error: failed to access and parse <h2> title content of food item")
        cleanup_driver(driver)
    
    # parsing food item's details
    try:
        text_div = driver.find_element(By.CSS_SELECTOR, 'div[data-qa="text"]')
        response["details"] = text_div.text
    except:
        print("Food item's description likely not provided")
    
    # parsing food item's allergens
    try:
        info_button = driver.find_element(By.XPATH, '//fieldset//span[@role="button"]')
        info_button.click()   
    except:
        print("fieldset wasnt found")
        info_button = driver.find_element(By.XPATH, '//div[@data-qa="item-details-card"]//span[@role="button"]')
        info_button.click()
        
    # if <h6> exists (header for allergens), so does the allergen info
    h6 = None
    try:
        h6 = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, 'h6'))
        )
    except:
        print("Food item likely has no allergens")
    
    if h6:
        try:
            allergen_list = driver.find_element(By.CSS_SELECTOR, 'ul[data-qa="util"]')
            li_allergen_items = allergen_list.find_elements(By.TAG_NAME, 'li')
            allergen_data = ""
            
            for li in li_allergen_items:
                allergen_data += li.text + " "
            response["allergens"] = allergen_data.rstrip()

        except:
            print("food item likely has no allergens")
            

    try:
        return_back_button = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH,'//div[@data-qa="product-info-header"]//span[@data-qa="product-info-header-action-back"]'))
        )
        print("Found return back button")
        #return_back_button = driver.find_element(By.XPATH, '//div[@data-qa="product-info-header"]//span[@data-qa="product-info-header-action-back"]')
        return_back_button.click()
        print("Clicked return back button")
    except Exception as e:
        print(f"!!! Unexpected Error when finding or interacting with 'return back' <span> button. {e}")
        cleanup_driver(driver)
            
    # parsing food item's price
    try:
        price_span = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//div[@data-qa="item-details-card"]//span[@data-qa="text"]//span'))
        )
        response["price"] = price_span.text
    except:
        print("!!! Error: failed to find <span> element with food item's price")
        cleanup_driver(driver)

    # extracting food item image src
    try:
        img = driver.find_element(By.TAG_NAME, 'img')
        response["img_url"] = img.get_attribute("src")
    except:
        print("!!! Error: failed to find img element of food item and its src")
        cleanup_driver(driver)

    # close food item page
    try:
        close_button = driver.find_element(By.XPATH, '//div[@data-qa="item-details-card"]//span[@role="button"]')
        close_button.click()
    except Exception as e:
        print(f"!!! Error: failed to find or click <span> button to close food item's page. {e}")
        cleanup_driver(driver)
    
    return response
    

def handle_parsing(driver):
    parsed_list = []
    
    try:
        food_sections = driver.find_elements(By.CSS_SELECTOR, 'section[data-qa="item-category"]')
    except:
        print("!!! Error: failed to find <section> elements that contain food items")
        cleanup_driver(driver)

    
    for section in food_sections:
        # Finding food category (section's <h2> content)
        food_category = None
        try:
            h2 = section.find_element(By.TAG_NAME, 'h2') 
            food_category = h2.text
            print(f"\nNew Category: '{food_category}'")
        except:
            print("!!! Error: failed to find or parse <h2> element that contains food category")
            cleanup_driver(driver)

        # Finding and iterating through food items
        try:
            food_items = section.find_elements(By.CSS_SELECTOR, 'div[role="button"]')
            for item in food_items:
                item.click()
                data = parse_food_item(driver, food_category)
                parsed_list.append(data)
        
        except Exception as e:
            print(f"!!! Unexpected Error when finding <section>'s food items or when clicking one of them. {e}")
            cleanup_driver(driver)
    
    return parsed_list



url = "https://www.lieferando.de/speisekarte/gastrooma-mnchen?utm_campaign=foodorder&utm_medium=organic&utm_source=google&shipping=delivery&rwg_token=AJKvS9X6iWbr8a6ECZAx_sfRF8_JtHQWAbX8HYfKbuGk7G-IMB3SyPoZ5aPRsMZHYGXanDfa4iWezXLUTldufH2BSRDxanOecA%3D%3D"
#url = "https://www.lieferando.de/speisekarte/dodo-pizza-1"

def main():
    driver = initialize_driver(url)
    accept_cookies(driver)
    
    street, number = get_restaurant_address(driver)
    handle_loc_prompt(driver, street, number)
    time.sleep(5) # wait after closing location prompt
    
    data = handle_parsing(driver)
    print(f"\nParsed all data!:\n{data}")
    cleanup_driver(driver, quit=False)
    
    

if __name__ == "__main__":
    main()

