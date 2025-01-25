from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from driver_utils import terminate_driver
from misc import print_exception_info


class MenuItem:
    def __init__(self, driver, food_category, element):
        self.driver = driver  
        self.food_category = food_category
        self.element = element

    def extract_data(self):
        # helps locate all data, except for allergens
        div_item_details_card = self.get_div_item_details_card()
        
        title = self.extract_title(div_item_details_card) # if not found or error => terminate_driver()
        print(f"Food name: {title}")
        
        price = self.extract_price() # if not found or error => terminate_driver()
        img_url = self.extract_img_url(div_item_details_card)
        description = self.extract_description(div_item_details_card)
        allergens = self.extract_allergens()
       
        data = {
            "category": self.food_category, "title": title, "description": description, 
            "allergens": allergens, "price": price, "img_url": img_url
        }
        return data
    

    def get_div_item_details_card(self):
        func_name = "self.get_div_item_details_card"
        try:
            item_details_wrapper= WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-qa="item-details-card"]'))
            ) 
            return item_details_wrapper
        except Exception as e:
            reason = "couldn't locate <div data-qa='item-details-card'> element"
            print_exception_info(func_name=func_name, reason=reason, e=e)
            terminate_driver(self.driver)


    def extract_title(self, div_item_details_card):
        func_name = "self.extract_title"
        try:
            h2 = div_item_details_card.find_element(By.TAG_NAME, 'h2')
            title = h2.text
            return title
        
        except NoSuchElementException:
            reason = "couldn't locate <h2> with title within <div data-qa='item-details-card'>"
            print_exception_info(func_name=func_name, e_name="NoSuchElementException", reason=reason)
            terminate_driver(self.driver)

        except Exception as e:
            print_exception_info(func_name=func_name, e=e)
            terminate_driver(self.driver)

        
    def extract_price(self):
        func_name = "self.extract_price"
        try:
            span = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//div[@data-qa="item-details-card"]//span[@data-qa="text"]//span'))
            )
            price = span.text
            return price
        
        except NoSuchElementException:
            reason = "couldn't locate <span> with price within path //<div data-qa='item-details-card'>//<span data-qa='text'>"
            print_exception_info(func_name=func_name, e_name="NoSuchElementException", reason=reason)
            terminate_driver(self.driver)

        except Exception as e:
            print_exception_info(func_name=func_name, e=e)
            terminate_driver(self.driver)
        
    
    def extract_img_url(self, div_item_details_card):
        func_name = "extract_img_url"
        try:
            img = div_item_details_card.find_element(By.TAG_NAME, 'img')
            url = img.get_attribute("src")
            return url
        
        except NoSuchElementException:
            reason = "couldn't locate <img> element within <div data-qa='item-details-card'>. Image is likely missing"
            print_exception_info(func_name=func_name, e_name="NoSuchElementException", reason=reason)
           
        except Exception as e:
            print_exception_info(func_name=func_name, e=e)
            terminate_driver(self.driver)
        
    
    def extract_description(self, div_item_details_card):
        func_name = "extract_description"
        try:
            div = div_item_details_card.find_element(By.CSS_SELECTOR, 'div[data-qa="text"]')
            description = div.text
            return description
        
        except NoSuchElementException:
            reason = "couldn't locate <div data-qa='text'> element within <div data-qa='item-details-card'>. Description is likely missing"
            print_exception_info(func_name=func_name, e_name="NoSuchElementException", reason=reason)
           
        except Exception as e:
            print_exception_info(func_name=func_name, e=e)
            terminate_driver(self.driver)


    def extract_allergens(self):
        
        def open_product_info():
            def locate_button(path):
                try: 
                    button = WebDriverWait(self.driver, 5).until(
                        EC.visibility_of_element_located((By.XPATH, path))
                    )
                    button.click()
                    return True
                except:
                    return False
            
            path_1 = '//fieldset//span[@role="button"]'
            path_2 = '//div[@data-qa="item-details-card"]//span[@data-qa="item-details-action-nutrition-element"]'
            
            if not locate_button(path=path_1):
                status = locate_button(path=path_2)

                if not status:
                    func_name = "locate_button() within open_product_info() in self.extract_allergens"
                    reason = "unable to locate Productinfo button, tried all possible paths."
                    print_exception_info(func_name=func_name, reason=reason)
                    terminate_driver(self.driver)


        def allergen_section_exist():
            func_name = "allergen_section_exist() within self.extract_allergens"
            try:
                div = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-qa="product-info-allergen-section"]'))
                )
                return (True, div)
            except:
                reason= "allergen section doesn't exist"
                print_exception_info(func_name=func_name, reason=reason)
                return (False, None)
            

        def parse_allergens(allergens_section_div):
            func_name = "parse_allergens() within self.extract_allergens"
         
            try:
                data = ""
                li_items = allergens_section_div.find_elements(By.XPATH, './/ul//li')                                              
                for li in li_items:
                    data += li.text + " "
                data = data.rstrip()
                return data
            
            except Exception as e:
                print_exception_info(func_name=func_name, e=e)
                terminate_driver(self.driver)


        def close_product_info():
            func_name = "close_product_info() within self.extract_allergens"
            try:
                button = WebDriverWait(self.driver, 5).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, 'span[data-qa="product-info-header-action-back"]'))
                )
                button.click()
            except Exception as e:
                print_exception_info(func_name=func_name, e=e)
                terminate_driver(self.driver)


        # execute all sub-processes 
        data = None 
        open_product_info()
        status, allergens_section_div = allergen_section_exist()
        if status:
            data = parse_allergens(allergens_section_div)
        close_product_info()
        return data 


    # Open item page or go back to main page
    def open(self, element):
        func_name = "self.open_item_page"
        try:
            element.click()
        except Exception as e:
            reason = "Failed to open item page"
            print_exception_info(func_name=func_name, reason=reason, e=e)
            terminate_driver(self.driver)


    def close(self):
        func_name = "self.close_item_page"
        try:
            close_button = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//div[@data-qa="item-details-card"]//span[@role="button"]'))
            )
            close_button.click()
        except Exception as e:
            reason = "Failed to close item page"
            print_exception_info(func_name=func_name, reason=reason, e=e)
            terminate_driver(self.driver)



def parse_food_sections(driver, food_sections):
    func_name = "parse_food_sections"
    parsed_menu_items = []
    
    for section in food_sections:
        food_section_name = None
        try:
            h2 = section.find_element(By.TAG_NAME, 'h2') 
            food_section_name = h2.text
            print(f"\nFood Section: '{food_section_name}'")
        except Exception as e:
            reason = "failed to find or parse <h2> element containing next food category name"
            print_exception_info(func_name=func_name, reason=reason, e=e)
            terminate_driver(driver)

    
        # Finding and parsing all food items in section
        menu_items = None
        try:
            menu_items = section.find_elements(By.CSS_SELECTOR, 'div[role="button"]')
            for item in menu_items:
                menu_item = MenuItem(driver, food_section_name, item)
                menu_item.open(item)
                data = menu_item.extract_data()
                parsed_menu_items.append(data)
                menu_item.close()
        
        except Exception as e:
            print(f"!!! Unexpected Error when finding <section>'s food items or when clicking one of them. {e}")
            terminate_driver(driver)


def parse_food_menu(driver):
    func_name = "parse_food_menu"
    
    try:
        food_sections = driver.find_elements(By.CSS_SELECTOR, 'section[data-qa="item-category"]')
        data = parse_food_sections(driver, food_sections)
        return data
    
    except Exception as e:
        reason = "failed to find all <section data-qa='item-category'> elements"
        print_exception_info(func_name=func_name, reason=reason, e=e)
        terminate_driver(driver)

