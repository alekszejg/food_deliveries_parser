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

    # Not sure if I 100% need element below, but it makes element search much more precise
    div_item_details_card = None
    try:
        div_item_details_card = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-qa="item-details-card"]'))
        ) 
    except:
        print("!!! Unexpected Error when locating <div data-qa='item-details-card'>")
        cleanup_driver(driver)
    
    # extracting food item image src
    try:
        img = div_item_details_card.find_element(By.TAG_NAME, 'img')
        response["img_url"] = img.get_attribute("src")
    except Exception as e:
        print(f"!!! Error: failed to find img element of food item and its src. {e}")
        cleanup_driver(driver)
    
    print(f"Image: {response['img_url']}")

    # parsing food item's title/name
    try:
        h2 = div_item_details_card.find_element(By.TAG_NAME, 'h2')
        response["title"] = h2.text
    except:
        print("!!! Error: failed to access and parse <h2> title content of food item")
        cleanup_driver(driver)

    print(f"Title: {response['title']}")
    

    # parsing food item's details
    try:
        text_div = div_item_details_card.find_element(By.CSS_SELECTOR, 'div[data-qa="text"]')
        response["details"] = text_div.text
    except:
        print("Food item's description likely not provided")

    print(f"Details: {response['details']}")

    # parsing food item's allergens
    try:
        product_info_button = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.XPATH,'//fieldset//span[@role="button"]'))
        )
        product_info_button.click()   
    except:
        print("Element <fieldset> not found, likely only 1 portion option avaible")
        product_info_button = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.XPATH, '//div[@data-qa="item-details-card"]//span[@data-qa="item-details-action-nutrition-element"]'))
        )
        product_info_button.click()
   
    # check if allergen section exists and only afterwards parse allergens
    try:
        allergen_section = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-qa="product-info-allergen-section"]'))
        )
        
        try:
            allergen_items = allergen_section.find_elements(By.XPATH, './/ul//li')                                              
            allergen_data = ""
            for li in allergen_items:
                allergen_data += li.text + " "
            response["allergens"] = allergen_data.rstrip()
            print(f"Allergens: {response['allergens']}")

        except:
            print("Unexpected Error occured when finding <li> allergen items")
            cleanup_driver(driver)

    except:
        print("Food item likely has no allergens.\n")
    

    # Returning back from Productinformation page        
    try:
        return_back_button = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'span[data-qa="product-info-header-action-back"]'))
        )
        return_back_button.click()
    except Exception as e:
        print(f"!!! Unexpected Error when finding or interacting with 'return back' <span> button. {e}")
        cleanup_driver(driver)
            

    # close food item page
    try:
        close_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//div[@data-qa="item-details-card"]//span[@role="button"]'))
        )
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

