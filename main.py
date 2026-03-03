import json
from Lister import Lister
from items_to_publish import *


def list_my_personal_items(email: str):
    off = [omega_moon, pagani_pd1734, pagani_batman, hublot]
    products = [bowl, ap_silver, ponda, casioak, ferari
             , pagani_skeleton, citizen_tsuyosa_gold,
             rm_black, rm_blue_gold, rm_foxbox, rm_gold, rm_yellow,
             ]
    
    products = [pagani_skeleton,
             ]
    



    

    lister = Lister()
    if lister.login(email):
        for product in products:
            max_retries = 1
            for attempt in range(1, max_retries + 1):
                try:
                    lister.list(product)
                    continue
                except Exception as e:
                    print(f"Attempt {attempt} failed for product: {product.get('title', '')}")
                


def delete_my_items(email: str, headless: bool = False) -> None:
    lister = Lister(headless=headless)
    try:
        if lister.login(email):
            lister.delete_all_items()
            print('Success!')
        else:
            print('Failed: could not log in.')
    finally:
        lister.driver.quit()

def renew_cookies(email):
    """Clear expired cookies and login fresh"""
    lister = Lister()
    lister.clear_expired_cookies(email)
    if lister.login(email):
        print('Cookies renewed successfully!')
    else:
        print('Failed to renew cookies')


if __name__ == "__main__":
    shoham_tests = "shoamtal.tests@gmail.com"

    list_my_personal_items(shoham_tests)
    # delete_my_items(shoham_tests)
