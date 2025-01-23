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


def cleanup_driver(driver, exit=False):
    try:
        driver.close()  # Close the browser tab
        driver.quit()   # Quit the browser entirely  
        print("Driver successfully cleaned up.")
    except Exception as e:
        print(f"Error during driver cleanup: {e}")
    finally:
        if exit:
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
        print("! Error during driver initialization. {e}")
        if driver:
            cleanup_driver(driver, exit=True)
        


def accept_cookies(driver):
    try:
        cookie_banner = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.TAG_NAME, 'pie-cookie-banner'))
        )
        shadow_root = driver.execute_script('return arguments[0].shadowRoot', cookie_banner)
        accept_cookies_btn = shadow_root.find_element(By.CSS_SELECTOR, 'pie-button[data-test-id="actions-necessary-only"]')
        accept_cookies_btn.click()
        print("Accepted necessary cookies.")
    except Exception as e:
        print(f"! Error during cookies accept. {e}")
        cleanup_driver(driver, exit=True)


def get_restaurant_address(driver):
    try: 
        script = driver.find_element(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
        json_data = script.get_attribute("innerHTML")
        data = json.loads(json_data)
        address = data.get("address", {}).get("streetAddress", {})
        
        if not address:
            print("! Error: address wasn't provided by restaurant")
            cleanup_driver(driver, exit=True)
        
        # Avoids extra information after symbols ,.(
        regex_match1 = re.match(r'^[^,(.]+', address.strip())
        if not regex_match1:
            print("! Unexpected Error in regex during address cleanup")
            cleanup_driver(driver, exit=True)
            
        clean_address = regex_match1.group(0).strip()
        street_number = None

        # check for street number
        regex_match2 = re.search(r'\b\d+[a-zA-Z]?\b', clean_address)
        if regex_match2:
            street_number = regex_match2.group()

        print(f"Obtained restaurant's address. Street: {clean_address}, number: {street_number}")
        return (clean_address, street_number)
            
    except Exception as e:
        print(f"! Unexpected Error during restaurant's address extraction. {e}")
        cleanup_driver(driver, exit=True)
    
    
def fill_loc_prompt(driver, street, number):
    try:
        street_input = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[aria-label="Ort suchen"]'))
        )
        my_loc = f"{street} {number or ''}".strip()
        street_input.send_keys(my_loc)
    except Exception as e:
        print(f"! Unexpected Error when accessing location <input> element. {e}")
        cleanup_driver(driver, exit=True)
    
    try:
        address_suggestion = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'li[role="option"]'))
        )
        address_suggestion.click()
    except Exception as e:
        print(f"Unexpected Error when accessing or interacting with address suggestion. {e}")
        cleanup_driver(driver, exit=True)

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
            print(f"Unexpected Error when accessing or interacting with 'Confirm Address' button. {e}")
            cleanup_driver(driver, exit=True)
    
    

def handle_loc_prompt(driver, street, number):
    # Triggers Lieferando's location prompt to appear by clicking 1st menu item
    try:
        food_section_1 = driver.find_element(By.CSS_SELECTOR, 'section[data-qa="item-category"]')
        clickable_food_div = food_section_1.find_element(By.XPATH, './/div[@role="button"]')
        clickable_food_div.click()
    except Exception as e:
        print(f"! Unexpected Error when triggering location popup to appear: {e}")
        cleanup_driver(driver, exit=True)
    
    # Prompt should have appeared. Filling in the data...
    fill_loc_prompt(driver, street, number)

    # close food item card
    try:
        close_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@data-qa="item-details-card"]//span[@role="button"]'))
        )
        close_button.click()
    except Exception as e:
        print(f"Unexpected Error during access or interaction with close button of food item. {e}")
        cleanup_driver(driver, exit=True)

    print("Entered address was accepted. Proceeding with data parsing.")



# function that extracts data from single food item 
def extract_food_item_data(driver, category):
    response = {"category": category, "title": "", "details": "", 
        "allergens": "", "price": "", "img_url": ""
    }

    try:
        # extracting food item name
        h2_food_name = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, '//div[@data-qa="item-details-card"]//h2[@data-qa="heading"]'))
        )
        response["title"] = h2_food_name.text

        
        # extracting general food details 
        try:
            div_food_details = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, '//div[@data-qa="item-details-card"]//div[@data-qa="text"]'))
            )
            response["details"] = div_food_details.text
        except:
            print("Description wasn't provided")
        print("encountered no error after product details")

        try:
            # find out if food item has multiple order options (potion sizes)
            span_product_info_button = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.XPATH, '//fieldset//span[@role="button"][text()="Produktinfo"]'))
            )
            print("FIELDSET FOUND")
            span_product_info_button.click()
            print("PRODUCT INFO BUTTON CLICKED")
        except:
            # fieldset doesn't exist. Only one order option
            print("FIELDSET NOT FOUND")
            span_product_info_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@data-qa="item-details-card"]//span[@role="button"][text()="Produktinfo"]'))
            )
            span_product_info_button.click()
            print("PRODUCT INFO BUTTON CLICKED")
        
        # check if allergen info exists by checking if its header exists
        try:
            h6_allergens = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, '//h6[text()="Allergens"]'))
            )

            ul_allergens = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, '//ul[@data-qa="util"]'))
            )
            li_allergen_items = ul_allergens.find_elements(By.XPATH, './li')
            
            allergen_info = ""
            for li in li_allergen_items:
                allergen_info += li.text + " "
            
            response["product_info"] = allergen_info.rstrip()
        except:
            # basically <h6> doesn't exist. Not outputing it into console to avoid mess
            pass
        finally:
            span_go_back_button = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, '//div[@data-qa="product-info-header"]//span[@role="button"]'))
            )
            span_go_back_button.click()
            
        # extracting food item price
        span_price = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, '//div[@data-qa="item-details-card"]//span[@data-qa="text"]//span'))
        )
        response["price"] = span_price.text

        # extracting food item image src
        img = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, '//div[@data-qa="item-details-card"]//img'))
        )
        response["img_url"] = img.get_attribute("src")
        
        # close food item (acts as real user)
        close_food_item_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@data-qa="item-details-card"]//span[@role="button"]'))
        )
        close_food_item_button.click()
        return response
    
    except Exception as e:
        print(f"Unexpected error when parsing <li>. {e}")



# main function for handling data extraction
def handle_data_extraction(driver):
    extracted_data = []
    food_sections = driver.find_elements(By.XPATH, '//section[@data-qa="item-category"]')
    
    for section in food_sections:
        h2_food_section= section.find_element(By.XPATH, './/div//h2[@data-qa="heading"]')
        
        if h2_food_section:
            food_category = h2_food_section.text
            print(f"Food section: '{food_category}'\n")
            
            # <li> items aren't clickable but their deep indirect children divs are
            clickable_food_items = section.find_elements(By.XPATH, './/div[@role="button"]')
    
            # going through every food item
            for item in clickable_food_items:
                item.click()
                print("Item was clicked")
                data = extract_food_item_data(driver, food_category)
                extracted_data.append(data)
                print(f"{data["title"]} was parsed")
        else:
            print("Failed to find food section name")
    print(extracted_data)


url = "https://www.lieferando.de/speisekarte/gastrooma-mnchen?utm_campaign=foodorder&utm_medium=organic&utm_source=google&shipping=delivery&rwg_token=AJKvS9X6iWbr8a6ECZAx_sfRF8_JtHQWAbX8HYfKbuGk7G-IMB3SyPoZ5aPRsMZHYGXanDfa4iWezXLUTldufH2BSRDxanOecA%3D%3D"
#url = "https://www.lieferando.de/speisekarte/dodo-pizza-1"

def main():
    driver = initialize_driver(url)
    accept_cookies(driver)
    
    street, number = get_restaurant_address(driver)
    handle_loc_prompt(driver, street, number)
    
    handle_data_extraction(driver)
    
    cleanup_driver(driver)
    
    

if __name__ == "__main__":
    main()

