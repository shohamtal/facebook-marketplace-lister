import pickle
from typing import Any, Dict, List, Optional, Tuple

from selenium import webdriver
import time
import os
from dotenv import load_dotenv

from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service

from Element import Element
from Helpers import read_json, format_xpath, assert_directory
from datetime import datetime
from colorama import Fore, Style

from locales import Locale

# Load environment variables
load_dotenv('facebook_credentials.env')


class Lister:
    def __init__(self):
        self.driver_file = 'chromedriver'
        self.sleep_time = 1
        chrome_options = webdriver.ChromeOptions()
        prefs = {"profile.default_content_setting_values.notifications" : 2}
        chrome_options.add_experimental_option("prefs",prefs)
        chrome_options.add_experimental_option("detach", True)
        chrome_options.add_argument("--start-maximized")
        service = Service('drivers/%s' % self.driver_file)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(30)
        self.pathes = read_json(f'elements-{Locale.Hebrew.value}.json')

    @property
    def xpath(self, name):
        xpath_format = self.pathes[name]['xpath']
        return format_xpath(xpath_format, self.values) if self.values else format_xpath(xpath_format, self.defaults)

    @property
    def defaults(self):
        return self.pathes[self.name]['defaults']

    def get_element(self, name):
        element_type = self.pathes[name]['type']
        if element_type == 'button':
            element = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
        else:
            element = self.driver.find_element(By.XPATH, xpath)
        return element

    def read_accounts(self):
        return read_json('accounts')['accounts']
    
    def clear_expired_cookies(self, email):
        """Clear expired cookies and force fresh login"""
        self.cookies_dir = f".{email}"
        self.cookies_file_path = os.path.join(self.cookies_dir, "cookies.pkl")
        
        if os.path.isfile(self.cookies_file_path):
            try:
                os.remove(self.cookies_file_path)
                log('Cleared expired cookies, will login fresh', 'main')
                return True
            except Exception as e:
                log(f'Error clearing cookies: {str(e)}', 'failure')
                return False
        return True
        
    def login_with_credentials(self, email):
        # Check if environment credentials are available
        env_email = os.getenv('FACEBOOK_EMAIL')
        env_password = os.getenv('FACEBOOK_PASSWORD')
        
        if env_email and env_password and env_email != 'your_email@example.com':
            log('Using environment credentials for login', 'main')
            return self._login_with_credentials(env_email, env_password, email)
        
        raise Exception('No environment credentials found')
        
    def login(self, email):
        # Try cookie-based login first
        self.cookies_dir = f".{email}"
        self.cookies_file_path = os.path.join(self.cookies_dir, "cookies.pkl")
        
        if os.path.isfile(self.cookies_file_path):
            try:
                cookies = pickle.load(open(self.cookies_file_path, "rb"))
                
                # Check if cookies are expired
                current_time = time.time()
                valid_cookies = []
                for cookie in cookies:
                    # Check if cookie has expiration and if it's still valid
                    if 'expiry' in cookie and cookie['expiry']:
                        if cookie['expiry'] > current_time:
                            valid_cookies.append(cookie)
                        else:
                            log(f'Cookie expired: {cookie.get("name", "unknown")}', 'main')
                    else:
                        # Session cookies (no expiry) are usually valid
                        valid_cookies.append(cookie)
                
                if valid_cookies:
                    # Navigate to facebook domain BEFORE adding cookies
                    self.driver.get('https://www.facebook.com/')
                    time.sleep(2)
                    
                    for cookie in valid_cookies:
                        self.driver.add_cookie(cookie)
                    
                    # Test if login was successful by navigating to a protected page
                    self.driver.get('https://www.facebook.com/marketplace/you/selling')
                    time.sleep(2)
                    
                    # Check if we're still on login page (cookies expired)
                    if 'login' in self.driver.current_url:
                        log('Cookies expired, need to login manually', 'main')
                    else:
                        log('Successfully logged in using saved cookies', 'success')
                        return True
                else:
                    log('All cookies expired, need to login manually', 'main')
                    
            except Exception as e:
                log(f'Error loading cookies: {str(e)}', 'failure')
                return False
            
        return self.login_with_credentials(email)

        # Fallback to accounts.json
        # registered_accounts = self.read_accounts()
        # account_info = next(x for x in registered_accounts if x['email'] == email)
        # log('Logging in as "%s" ..' % account_info['name'], 'main')

        # # entering email
        # email_input = Element(self.driver, 'login_email').element
        # email_input.clear()
        # email_input.send_keys(account_info['email'])
        
        # # entering password
        # password_input = Element(self.driver, 'login_password').element
        # password_input.clear()
        # password_input.send_keys(account_info['password'])
        
        # # Submitting
        # password_button = Element(self.driver, 'login_button').element
        # password_button.click()

        # # 2fa
        # if account_info['is_2fa_enabled']:
        #     print("do it yourself!!!!")
        #     # two_fa_button = Element(self.driver, '2fa_button').element
        #     # two_fa_button.click()
        #     # two_fa_sms_radio = Element(self.driver, '2fa_sms_radio').element
        #     # two_fa_sms_radio.click()
        #     # Element(self.driver, '2fa_continue_to_sms').element.click()

        # # save coockies state:
        # assert_directory(self.cookies_dir)
        # pickle.dump(self.driver.get_cookies(), open(self.cookies_file_path, "wb"))

        # return True

    def _login_with_credentials(self, email, password, account_email):
        """Login using environment credentials"""
        log(f'Logging in with credentials for {email}', 'main')
        self.driver.get('https://www.facebook.com/login')
        
        # Wait for page to load
        time.sleep(3)
        
        try:
            # Find email input
            email_input = self.driver.find_element(By.ID, 'email')
            email_input.clear()
            email_input.send_keys(email)
            
            # Find password input
            password_input = self.driver.find_element(By.ID, 'pass')
            password_input.clear()
            password_input.send_keys(password)
            
            # Click login button
            login_button = self.driver.find_element(By.NAME, 'login')
            login_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check if login was successful
            current_url = self.driver.current_url
            if 'two_step_verification' in current_url:
                print("Two-step verification required. please solve puzzele manually")
                
            if 'login' in current_url or 'checkpoint' in current_url:
                log('Login failed or requires additional verification', 'failure')
                return False
            
            # Navigate to marketplace to verify access
            self.driver.get('https://www.facebook.com/marketplace/you/selling')
            time.sleep(3)
            
            # Check if we can access marketplace
            current_url = self.driver.current_url
            if 'marketplace' in current_url:
                log('Successfully logged in with credentials', 'success')
                
                # Save cookies for future use
                self.cookies_dir = f".{account_email}"
                assert_directory(self.cookies_dir)
                self.cookies_file_path = os.path.join(self.cookies_dir, "cookies.pkl")
                pickle.dump(self.driver.get_cookies(), open(self.cookies_file_path, "wb"))
                log('Cookies saved for future use', 'main')
                
                return True
            else:
                log('Login successful but cannot access marketplace', 'failure')
                return False
                
        except Exception as e:
            log(f'Error during credential login: {str(e)}', 'failure')
            return False
    
    def list(self, item):
        log(f'listing item {item["title"]}', 'main')
        listing_item = Item(self.driver, item)

        if not listing_item.in_stock:
            log('item not in stock. skipping...', 'main')
            return

        self.driver.get('https://www.facebook.com/marketplace/create/item')
        
        listing_item.upload_images()
        time.sleep(self.sleep_time)
        
        listing_item.enter_title()
        time.sleep(self.sleep_time)
        
        listing_item.enter_price()
        time.sleep(self.sleep_time)
        
        listing_item.choose_category()
        time.sleep(self.sleep_time)
        
        listing_item.choose_condition()
        time.sleep(self.sleep_time)
        
        if 'description' in item.keys() and item['description'] :
            listing_item.enter_description()
            time.sleep(self.sleep_time)
        
        if 'sku' in item.keys() and item['sku'] :
            listing_item.enter_sku()
            time.sleep(self.sleep_time)
        
        listing_item.choose_location()
        time.sleep(self.sleep_time)
        
        if 'hide_from_friends' in item.keys() and item['hide_from_friends'] :        
            listing_item.hide_from_friends()
            time.sleep(self.sleep_time)
        
        listing_item.click_next()
        time.sleep(self.sleep_time)
        
        listing_item.click_publish()
        time.sleep(self.sleep_time)

    def delete_all_items_not_working(self):
        # self.driver.get('https://www.facebook.com/marketplace/you/selling')
        # element = self.get_element("my_items")

        # self.driver.get("https://www.facebook.com/marketplace")
        #
        # # Wait for the page to load and locate the "Your Items" section
        wait = WebDriverWait(self.driver, 10)
        # your_items_section = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[aria-label='Your Items']")))
        # your_items_section.click()

        # Wait for the "Your Items" page to load
        self.driver.get('https://www.facebook.com/marketplace/you/selling')
        time.sleep(self.sleep_time)
        # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[aria-label='Your Listings']")))

        # Get all the listing elements
        listing_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[aria-label='Listing']")

        # Delete each listing
        for listing in listing_elements:
            # Click the "..." button to open the menu
            more_button = listing.find_element(By.CSS_SELECTOR, "button[aria-label='More options']")
            more_button.click()

            # Click the "Delete" option
            delete_button = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='menuitem'][aria-label='Delete']")))
            delete_button.click()

            # Confirm the deletion
            confirm_button = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button[aria-label='Delete']")))
            confirm_button.click()

            # Wait for the listing to disappear
            wait.until(EC.staleness_of(listing))

            print("Listing deleted.")

    def delete_all_items(self):
        """
        Delete all items from Facebook Marketplace selling page.
        Navigates to the selling page and systematically deletes all listings.
        """
        log('Starting to delete all marketplace items...', 'main')
        
        # Navigate to the selling page
        self.driver.get('https://www.facebook.com/marketplace/you/selling')
        time.sleep(3)  # Wait for page to load
        
        wait = WebDriverWait(self.driver, 15)
        deleted_count = 0
        
        while True:
            try:
                # Wait for listings to load and find all listing containers
                # Try multiple selectors as Facebook's structure can vary
                listing_selectors = [
                    "div[aria-label='Listing']",
                    "div[data-testid='marketplace-listing-item']",
                    "div[role='article']",
                    "div[data-testid='marketplace-listing']"
                ]
                
                listing_elements = []
                for selector in listing_selectors:
                    listing_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if listing_elements:
                        log(f'Found {len(listing_elements)} listings with selector: {selector}', 'main')
                        break
                
                if not listing_elements:
                    log('No more listings found to delete', 'success')
                    break
                
                # Process each listing
                for listing in listing_elements:
                    try:
                        # Scroll to the listing to ensure it's visible
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", listing)
                        time.sleep(1)
                        
                        # Find and click the more options button (three dots)
                        more_options_selectors = [
                            "button[aria-label='More options']",
                            "button[aria-label='More']",
                            "button[data-testid='more-options']",
                            "button[aria-haspopup='true']",
                            "div[role='button'][aria-label*='More']"
                        ]
                        
                        more_button = None
                        for selector in more_options_selectors:
                            try:
                                more_button = listing.find_element(By.CSS_SELECTOR, selector)
                                break
                            except:
                                continue
                        
                        if not more_button:
                            log('Could not find more options button for listing', 'failure')
                            continue
                        
                        # Click more options button
                        more_button.click()
                        time.sleep(1)
                        
                        # Find and click delete option
                        delete_selectors = [
                            "div[role='menuitem'][aria-label='Delete']",
                            "div[role='menuitem'][aria-label*='Delete']",
                            "span[text()='Delete']",
                            "div[data-testid='delete-option']"
                        ]
                        
                        delete_button = None
                        for selector in delete_selectors:
                            try:
                                delete_button = wait.until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                )
                                break
                            except:
                                continue
                        
                        if not delete_button:
                            log('Could not find delete option', 'failure')
                            continue
                        
                        # Click delete
                        delete_button.click()
                        time.sleep(1)
                        
                        # Find and click confirm delete button
                        confirm_selectors = [
                            "button[aria-label='Delete']",
                            "button[data-testid='confirm-delete']",
                            "span[text()='Delete']/..",
                            "button[type='submit']"
                        ]
                        
                        confirm_button = None
                        for selector in confirm_selectors:
                            try:
                                confirm_button = wait.until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                )
                                break
                            except:
                                continue
                        
                        if not confirm_button:
                            log('Could not find confirm delete button', 'failure')
                            continue
                        
                        # Click confirm
                        confirm_button.click()
                        time.sleep(2)
                        
                        # Wait for the listing to disappear
                        try:
                            wait.until(EC.staleness_of(listing))
                        except:
                            # If staleness check fails, wait a bit more
                            time.sleep(3)
                        
                        deleted_count += 1
                        log(f'Successfully deleted listing #{deleted_count}', 'success')
                        
                    except Exception as e:
                        log(f'Error deleting listing: {str(e)}', 'failure')
                        continue
                
                # After processing all visible listings, refresh the page to check for more
                self.driver.refresh()
                time.sleep(3)
                
            except Exception as e:
                log(f'Error in delete loop: {str(e)}', 'failure')
                break
        
        log(f'Deletion complete. Total items deleted: {deleted_count}', 'success')
        return deleted_count






class Item :
    def __init__(self, driver, item):
        self.driver = driver
        self.item = item

    @property
    def in_stock(self):
        return self.item.get("in_stock", True)
        
    def populate_images_from_path(self):
        dir = self.item['images_path']
        images = sorted([
            os.path.join(dir, f) for f in os.listdir(dir)
            if os.path.isfile(os.path.join(dir, f))
               and (
                   f.lower().endswith(f".png")
                   or f.lower().endswith(f".jpg")
                   or f.lower().endswith(f".jpeg")
                   or f.lower().endswith(f".webp")
               )
        ])
        self.item['images'] = [{"file": x} for x in images]


    def upload_images(self):
        log('Uploading Images', 'main')
        image_upload = Element(self.driver, 'post_image').element
        self.driver.execute_script("document.querySelector('%s').classList = []" % Element(self.driver, 'post_image_css').xpath)
        log('Showing image input ..', 'main')
        if self.item.get("images_path"):
            self.populate_images_from_path()
        joined_images_path = ' \n '.join([image["file"] for image in self.item['images']][:10])
        log('sending images ..', 'main')
        image_upload.send_keys(joined_images_path)
        log('Uploaded Images Successfully .', 'success')
        return True

            
    def enter_title(self):
        try:
            log('Entering The Title', 'main')
            title_input = Element(self.driver, 'post_title').element
            title_input.clear()
            title_input.send_keys(self.item['title'])
            log('Entered Title Successfully .', 'success')
            return True
        except :
            log('FAILED TO ENTER THE TITLE', 'failure')
            return False
            
    def enter_price(self):
        try:
            log('Entering The Price', 'main')
            price_input = Element(self.driver, 'post_price').element
            price_input.clear()
            price_input.send_keys(self.item['price'])
            log('Entered Price Successfully .', 'success')
            return True
        except :
            log('FAILED TO ENTER THE PRICE', 'failure')
            return False
    
    def choose_category(self):
        try:
            log('Choosing The Category', 'main')
            category_dropdown = Element(self.driver, 'post_category').element
            category_dropdown.click()
            
            values = self.item['category'] if 'category' in self.item.keys() and self.item['category'] else None
            category_dropdown_option = Element(self.driver, 'post_category_option', values).element
            log('clicking The Category Dropdown ..', 'sub')
            category_dropdown_option.click()
            
            log('Category Chosen Successfully .', 'success')
            return True
        except :
            log('FAILED TO CHOOSE THE CATEGORY', 'failure')
            return False
    
    def choose_condition(self):
        try:
            log('Choosing The Condition', 'main')
            condition_dropdown = Element(self.driver, 'post_condition').element
            condition_dropdown.click()
            log('clicking The Condition Dropdown ..', 'sub')
        
            values = self.item['condition'] if 'condition'in self.item.keys() and self.item['condition'] else None
            condition_dropdown_option = Element(self.driver, 'post_condition_option', values).element
            condition_dropdown_option.click()
            log('Condition Chosen Successfully .', 'success')
            return True
        except :
            log('FAILED TO CHOOSE THE CATEGORY', 'failure')
            return False
    
    def enter_description(self):
        try:
            log('Entering The Description', 'main')
            description_input = Element(self.driver, 'post_description').element
            description_input.clear()
            description_input.send_keys(self.item['description'])
            log('Entered Description Successfully .', 'success')
            return True
        except Exception as e:
            log('FAILED TO ENTER THE Description', 'failure')
            raise Exception('FAILED TO ENTER THE Description')
        
    def enter_sku(self):
        try:
            log('Entering The SKU', 'main')
            sku_input = Element(self.driver, 'post_sku').element
            sku_input.clear()
            sku_input.send_keys(self.item['sku'])
            log('Entered SKU Successfully .', 'success')
            return True
        except :
            log('FAILED TO ENTER THE SKU', 'failure')
            return False
    
    def choose_location(self):
        try:
            values = self.item['location'] if self.item.get('location') else Element(self.driver, 'post_location_option').defaults
            log('Choosing The Location', 'main')
            location_input = Element(self.driver, 'post_location').element
            location_input.click()
            log('Searching Locations ..', 'sub')
            location_input.send_keys(Keys.DELETE)
            location_input.send_keys(values)
            
            log('Choosing Location ..', 'sub')
            # values = self.item['location'] if 'location'in self.item.keys() and self.item['location'] else None
            location_input_option = Element(self.driver, 'post_location_option', values).element
            location_input_option.click()
            
            log('Location Chosen Successfully .', 'success')
            return True
        except Exception as e :
            log('FAILED TO CHOOSE THE Location', 'failure')
            return False
    
    def hide_from_friends(self):
        try:
            log('Checking Hide From Friends', 'main')
            self.click_button('post_hide_from_friends')
            log('Checked Hide From Friends Successfully .', 'success')
            return True
        except Exception as e:
            log('FAILED TO Check Hide From Friends', 'failure')
            return False

    def click_next(self):
        try:
            log('Clicking Next', 'main')
            self.click_button('post_next_button')
            log('Clicked Next Successfully', 'success')
            return True
        except :
            log('FAILED TO click Next', 'failure')
            return False

    def click_publish(self):
        try:
            log('Clicking Publish', 'main')
            self.click_button('post_publish_button')
            log('Clicked Publish Successfully', 'success')
            return True
        except :
            log('FAILED TO click Publish', 'failure')
            return False

    def click_button(self, button):
        element:WebElement = Element(self.driver, button).element
        element.click()


def log(msg, type=None):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    msg = "[%s] : %s" % (current_time, msg)
    if type is not None:
        if type == 'failure':
            msg = Fore.RED + "\t- " + msg + Style.RESET_ALL
        elif type == 'success':
            msg = Fore.GREEN + "\t+ " + msg + Style.RESET_ALL
        elif type == 'sub':
            msg = Fore.WHITE + "\t> " + msg + Style.RESET_ALL
        elif type == 'main':
            msg = Fore.WHITE + ">> " + msg + Style.RESET_ALL
        else:
            msg = msg + Style.RESET_ALL
    else:
        msg = msg + Style.RESET_ALL
    print (msg)
