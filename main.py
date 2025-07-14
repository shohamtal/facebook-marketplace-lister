import json
from Lister import Lister
from items_to_publish import *


def list_my_personal_items(email: str):
    off = [omega_moon, pagani_pd1734]
    products = [tissot_prx, pagani_batman, ap_silver, ponda, poker, casioak, ferari
             , pagani_skeleton, pp_aquanaut, hublot,
             rm_black, rm_black_and_red, rm_blue_gold, rm_foxbox, rm_gold, rm_yellow,
             ]
    

    lister = Lister()
    if lister.login(email):
        for product in products:
            result = lister.list(product)




def delete_my_items(email):
    lister = Lister()
    if lister.login(email):
        # delete all my published items in https://www.facebook.com/marketplace/you/selling
        lister.delete_all_items()

    print('Success!')


if __name__ == "__main__":
    shoham_tests = "*******"
    shoham = "*******"

    # list_my_personal_items(shoham_tests)

    delete_my_items(shoham_tests)
    # list_items_from_goldentime(shoham)
