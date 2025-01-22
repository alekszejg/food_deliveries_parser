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



def trigger_location_popup(driver):
    try:
        section_food_1 = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//section[@data-qa="item-category"]'))
        )
        print("Found 1st food section")
        div_food_1 = section_food_1.find_element(By.XPATH, './/div[@role="button"]')
        print("Found 1st food item in section")
        div_food_1.click()
        print("Click 1st food item in section")
        time.sleep(2)

    except Exception as e:
        print("Unexpected error when triggering lcoation popup to appear")



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
            trigger_location_popup(driver)
            provide_location(driver, addr["street"], addr["number"])
        else:
            print("Error trying to obtain restaurant address. Closing driver...")
        

        '''page_sections = driver.find_elements(By.XPATH, '//section[@data-qa="item-category"]')
        section_headings = []
        index = 0
        time.sleep(5)
        for section in page_sections:
            if index == 0:
                # section name
                h2_section_name = section.find_element(By.XPATH, './/div//h2[@data-qa="heading"]')
                section_headings.append(h2_section_name.text)
                # interactive divs
                div_interactive_items = section.find_elements(By.XPATH, './/div[@role="button"]')
                for div in div_interactive_items:
                    try:
                        div.click()
                        print("div was clicked")
                        time.sleep(1)  # Optional: sleep to allow for any loading after click
                        close_button = div.find_element(By.XPATH, './/span[@role="button"]')
                        close_button.click()  # Click the close button
                        print("Closed content successfully.")

                    except Exception as e:
                        print(f"Failed to click button: {e}")
            index += 1
        print(section_headings)'''
        driver.close()
    
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

