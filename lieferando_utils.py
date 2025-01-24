import json 
import re
from selenium.webdriver.common.by import By
from driver_utils import terminate_driver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from misc import print_exception_info


def get_restaurant_addr(driver):
    func_name = "get_restaurant_addr"
    
    try: 
        script = driver.find_element(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
        json_data = script.get_attribute("innerHTML")
        data = json.loads(json_data)
        address = data.get("address", {}).get("streetAddress", {})
        
        if not address:
            print("\n!!! Error: address wasn't provided by restaurant !!!\n")
            terminate_driver(driver)
        
        # Avoids extra information after symbols ,.(
        regex_match1 = re.match(r'^[^,(.]+', address.strip())
        if not regex_match1:
            print("!!! Unexpected Error in regex during address cleanup")
            terminate_driver(driver)
            
        clean_address = regex_match1.group(0).strip()
        street_number = None

        # check for street number
        regex_match2 = re.search(r'\b\d+[a-zA-Z]?\b', clean_address)
        if regex_match2:
            street_number = regex_match2.group()

        print(f"Obtained restaurant's address. Street: {clean_address}, number: {street_number}")
        return (clean_address, street_number)
            
    except Exception as e:
        print_exception_info(func_name=func_name, e=e)
        terminate_driver(driver)
    
    
def click_loc_suggestion(driver):
    func_name = "click_loc_suggestion"
    
    try:
        suggestion = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'li[role="option"]'))
        )
        suggestion.click()
    
    except NoSuchElementException:
        reason = "couldn't locate <li> element with address suggestion"
        print_exception_info(func_name=func_name, e_name="NoSuchElementException", reason=reason)
        terminate_driver(driver)
    
    except Exception as e:
        reason = "click failed to <li> element with address suggestion"
        print_exception_info(func_name=func_name, reason=reason, e=e)
        terminate_driver(driver)


# If prompted again to enter street number
def wait_for_street_number_prompt(driver, street_num):
    func_name = "wait_for_street_number_prompt"
    input = None
    
    try:
        input = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[placeholder="Enter building number or name"]'))
        )
        input.send_keys(street_num if street_num else "1") # 1 as fallback

    except NoSuchElementException:
        pass # <input> not found, probably no prompt was sent
    
    except Exception as e:
        reason = "likely failed to enter data with street number into <input>"
        print_exception_info(func_name=func_name, reason=reason, e=e)
        terminate_driver(driver)

    # need to press a button to confirm address 
    try:
        confirm_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-qa="location-panel-street-number"]'))
        )
        confirm_button.click()
    
    except NoSuchElementException:
        reason = "failed to locate 'Confirm Address' <button> element"
        print_exception_info(func_name=func_name, e_name="NoSuchElementException", reason=reason, e=e)
        terminate_driver(driver)

    except Exception as e:
        reason = "likely failed to click 'Confirm Address' button below <input>"
        print_exception_info(func_name=func_name, reason=reason, e=e)
        terminate_driver(driver)

   
def fill_loc_prompt(driver, street, number):
    func_name = "fill_loc_prompt"
    
    try:
        my_location = f"{street} {number or ''}".strip()
        street_input = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[aria-label="Ort suchen"]'))
        )
        street_input.send_keys(my_location)

    except NoSuchElementException:
        reason = "couldn't find main address <input> element"
        print_exception_info(func_name=func_name, e_name="NoSuchElementException", reason=reason)
        terminate_driver(driver)

    except Exception as e:
        reason = "Failed to send location data to main address <input> element" 
        print_exception_info(func_name=func_name, e_name="NoSuchElementException", reason=reason, e=e)
        terminate_driver(driver)

    # now address suggestion should appear
    click_loc_suggestion(driver)
    
    

# Clicking on 1st menu item triggers Lieferando's location prompt 
def trigger_loc_prompt(driver):
    func_name = "trigger_loc_prompt"
    
    try:
        clickable_food_item = driver.find_element(By.XPATH, '//section[@data-qa="item-category"]//div[@role="button"]')
        clickable_food_item.click()
    
    except NoSuchElementException:
        reason = "Couldn't find requested menu item in DOM"
        print_exception_info(func_name=func_name, e_name="NoSuchElementException", reason=reason)
        terminate_driver(driver)

    except Exception as e:
        print_exception_info(func_name=func_name, e=e)
        terminate_driver(driver) 


def handle_location_prompt(driver):
    func_name = "handle_location_prompt"
    
    street, number = get_restaurant_addr(driver)
    
    trigger_loc_prompt(driver)
    fill_loc_prompt(driver, street, number)
    wait_for_street_number_prompt(driver, street)

    # close food item card that was opened to trigger location prompt
    try:
        close_button = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.XPATH, '//div[@data-qa="item-details-card"]//span[@role="button"]'))
        )
        close_button.click()
    
    except NoSuchElementException as e:
        reason = "failed to find <span role='button'> to close food item card"
        print_exception_info(func_name=func_name, e_name="NoSuchElementException", reason=reason, e=e)
        terminate_driver(driver)

    except Exception as e:
        reason = "likely the click failed on <span role='button'> to close food item card"
        print_exception_info(func_name=func_name, reason=reason, e=e)
        terminate_driver(driver)

    print("Entered address was accepted. Proceeding with data parsing.")