from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from driver_utils import terminate_driver
from misc import print_exception_info


class FoodItem:
    def __init__(self, driver, food_category):
        self.driver = driver  
        self.food_category = food_category
    

    def extract_data(self):
        img_url = self.extract_image_url()
        title = self.extract_title()
        price = self.extract_price()
        description = self.extract_description()
        allergens = self.check_allergens()
       
        data = {
            "category": self.food_category, "title": title, "description": description, 
            "allergens": allergens, "price": price, "img_url": img_url
        }

        # helps locate all data, except for allergens
        details_wrapper = self.get_details_wrapper()
        
        return data
    
    def get_details_wrapper(self):
        try:
            item_details_wrapper= WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-qa="item-details-card"]'))
            ) 
        except Exception as e:
            reason = "couldn't locate <div data-qa='item-details-card'> element"
            print_exception_info(func_name=func_name, reason=reason, e=e)
            terminate_driver(self.driver)

    def extract_image_url(self):
        try:
            img = div_item_details_card.find_element(By.TAG_NAME, 'img')
            response["img_url"] = img.get_attribute("src")
        except Exception as e:
            print(f"!!! Error: failed to find img element of food item and its src. {e}")
            terminate_driver(driver)
        print(f"Image: {response['img_url']}")
    

    def extract_title(self):
        try:
            h2 = div_item_details_card.find_element(By.TAG_NAME, 'h2')
            response["title"] = h2.text
        except:
            print("!!! Error: failed to access and parse <h2> title content of food item")
            terminate_driver(driver)

        print(f"Title: {response['title']}")


    def extract_price(self):
        try:
            price_span = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//div[@data-qa="item-details-card"]//span[@data-qa="text"]//span'))
            )
            response["price"] = price_span.text
        except:
            print("!!! Error: failed to find <span> element with food item's price")
            cleanup_driver(driver)
        
        print(f"Price: {response['price']}")
    

    def extract_description(self):
        try:
            text_div = div_item_details_card.find_element(By.CSS_SELECTOR, 'div[data-qa="text"]')
            response["details"] = text_div.text
        except:
            print("Food item's description likely not provided")

        print(f"Details: {response['details']}")

    def check_allergens(self):
        
        def open_product_info(self):
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

        def extract_allergens(self):
            # 1st check if allergens section is there, if not then no allergens
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
                    terminate_driver(driver)

            except:
                print("Food item likely has no allergens.\n")
            
            def close_product_info(self):
                try:
                    return_back_button = WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, 'span[data-qa="product-info-header-action-back"]'))
                    )
                    return_back_button.click()
                except Exception as e:
                    print(f"!!! Unexpected Error when finding or interacting with 'return back' <span> button. {e}")
                    terminate_driver(driver)
        
        # goes back to main menu page
        def self_close(self):
            try:
                close_button = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@data-qa="item-details-card"]//span[@role="button"]'))
                )
                close_button.click()
            except Exception as e:
                print(f"!!! Error: failed to find or click <span> button to close food item's page. {e}")
                terminate_driver(driver)



def parse_food_sections(driver, food_sections):
    func_name = "parse_food_sections"
    parsed_menu_items = []
    
    for section in food_sections:
        # Finding food section/category name
        try:
            h2 = section.find_element(By.TAG_NAME, 'h2') 
            food_category = h2.text
            print(f"\nFood Category: '{food_category}'")
        except Exception as e:
            reason = "failed to find or parse <h2> element containing next food category name"
            print_exception_info(func_name=func_name, reason=reason, e=e)
            terminate_driver(driver)

    
        # Finding and parsing all food items in section
        food_items = None
        try:
            food_items = section.find_elements(By.CSS_SELECTOR, 'div[role="button"]')
            for item in food_items:
                item.click()
                data_dict = parse_menu__section_item(driver, food_category)
                parsed_menu_items.append(data_dict)
        
        except Exception as e:
            print(f"!!! Unexpected Error when finding <section>'s food items or when clicking one of them. {e}")
            terminate_driver(driver)



def parse_food_menu(driver):
    func_name = "parse_food_menu"
    
    try:
        food_sections = driver.find_elements(By.CSS_SELECTOR, 'section[data-qa="item-category"]')
        data_list = parse_food_sections(driver, food_sections)
        return data_list
    
    except Exception as e:
        reason = "failed to find all <section data-qa='item-category'> elements"
        print_exception_info(func_name=func_name, reason=reason, e=e)
        terminate_driver(driver)

