from driver_utils import init_driver, terminate_driver
from cookies import handle_cookies
from lieferando_utils import handle_location_prompt
from parsing_utils import parse_food_menu


def main():
    url = "https://www.lieferando.de/speisekarte/gastrooma-mnchen?utm_campaign=foodorder&utm_medium=organic&utm_source=google&shipping=delivery&rwg_token=AJKvS9X6iWbr8a6ECZAx_sfRF8_JtHQWAbX8HYfKbuGk7G-IMB3SyPoZ5aPRsMZHYGXanDfa4iWezXLUTldufH2BSRDxanOecA%3D%3D"
    #url = "https://www.lieferando.de/speisekarte/dodo-pizza-1"
    
    driver = init_driver(url)
    
    handle_cookies(driver)
    handle_location_prompt(driver)
    
    data_list = parse_food_menu(driver)
    print(f"\nParsed all data!:\n{data_list}")
    
    terminate_driver(driver, quit=False)
    
    
if __name__ == "__main__":
    main()

