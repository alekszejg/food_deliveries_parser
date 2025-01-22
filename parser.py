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
    

def provide_location(driver, street: str, number=None):
    try:
        input_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@aria-label="Ort suchen"]'))
        )
    except Exception as e:
        print(f"Failed to close location modal: {e}")


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
        print(addr)
        #close_location_modal(driver)

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
        driver.quit()

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

