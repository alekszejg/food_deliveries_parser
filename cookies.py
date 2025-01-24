from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, JavascriptException
from selenium.webdriver.common.by import By
from driver_utils import terminate_driver
from misc import print_exception_info

def get_cookie_banner(driver, timeout=10):
    func_name = "get_cookie_banner"
    cookie_banner = None
    
    try:
        cookie_banner = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, 'pie-cookie-banner'))
        )
        return cookie_banner
    
    except TimeoutException:
        reason = f"cookie banner didn't appear after {str(timeout)} seconds"
        print_exception_info(func_name=func_name, e_name="TimeoutException", reason=reason)
    
    except Exception as e: 
        print_exception_info(func_name=func_name, e=e)
       
    terminate_driver(driver)
    

def accept_cookies(driver, cookie_banner):
    func_name = "accept_cookies"
    cookies_accepted = False
    
    try:   
        shadow_root = driver.execute_script('return arguments[0].shadowRoot', cookie_banner)
        accept_cookies_button = shadow_root.find_element(By.CSS_SELECTOR, 'pie-button[data-test-id="actions-necessary-only"]')
        accept_cookies_button.click()
        cookies_accepted = True
    
    except JavascriptException as e:
        reason = "JavaScript execution failed likely when accessing shadow root."
        print_exception_info(func_name=func_name, e_name="JavascriptException", reason=reason, e=e)
    
    except NoSuchElementException as e:
        reason = "Accept cookies button not found in shadow DOM."
        print_exception_info(func_name=func_name, e_name="NoSuchElementException", reason=reason, e=e)

    except Exception as e:
        print_exception_info(func_name=func_name, e=e)
    
    finally:
        (terminate_driver(driver) if not cookies_accepted else None)


def handle_cookies(driver):
    cookie_banner = get_cookie_banner(driver)
    accept_cookies(driver, cookie_banner)
    
    