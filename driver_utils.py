from undetected_chromedriver import Chrome, ChromeOptions
from misc import print_exception_info

def terminate_driver(driver: Chrome, quit=True):
    driver.close() # Close the browser tab
    driver.quit() # Quit the browser entirely  
    print("Chrome driver terminated successfully")
    (exit() if quit else None)
    

def init_driver(url: str) -> Chrome:
    driver = None
    options = ChromeOptions()
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.geolocation": 2  # Block geolocation requests
    })
    
    try:
        driver = Chrome(use_subprocess=False, headless=False, options=options)
        driver.get(url)
        print("Driver successfully initialized. Webpage loaded.")
        return driver
    except Exception as e:
        print_exception_info(func_name="init_driver", e=e)
        (terminate_driver(driver) if driver else None)