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
from typing import Any, Dict, List, Optional, Tuple

# Load environment variables
load_dotenv('facebook_credentials.env')


class Lister:
    def __init__(self, headless: bool = False):
        self.driver_file = 'chromedriver'
        self.sleep_time = 1
        chrome_options = webdriver.ChromeOptions()
        prefs = {"profile.default_content_setting_values.notifications": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_experimental_option("detach", not headless)
        chrome_options.add_argument("--start-maximized")
        if headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
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
                invalid_cookies = []
                for cookie in cookies:
                    # Check if cookie has expiration and if it's still valid
                    if 'expiry' in cookie and cookie['expiry']:
                        if cookie['expiry'] > current_time:
                            valid_cookies.append(cookie)
                        else:
                            invalid_cookies.append(cookie)
                            log(f'Cookie expired: {cookie.get("name", "unknown")}', 'main')
                    else:
                        # Session cookies (no expiry) are usually valid
                        valid_cookies.append(cookie)
                
                if valid_cookies and not invalid_cookies:
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
            email_input = self.driver.find_element(By.NAME, 'email')
            email_input.clear()
            email_input.send_keys(email)

            # Find password input
            password_input = self.driver.find_element(By.NAME, 'pass')
            password_input.clear()
            password_input.send_keys(password)
            
            # Submit login form
            password_input.send_keys(Keys.RETURN)
            
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
            raise e
    
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

    def _is_chrome_error_page(self) -> bool:
        """True if the current page is a Chrome error page (e.g. ERR_TOO_MANY_REDIRECTS)."""
        try:
            src = self.driver.page_source
            return (
                "ERR_TOO_MANY_REDIRECTS" in src
                or "This page isn't working" in src
                or ("error-code" in src and "ERR_" in src)
            )
        except Exception:
            return False

    def _wait_selling_page_ready(self) -> None:
        """Wait for selling page to finish loading (fixed wait + optional element wait)."""
        if self._is_chrome_error_page():
            return
        # Wait for URL to be marketplace selling
        WebDriverWait(self.driver, 15).until(
            lambda d: "marketplace" in d.current_url and "selling" in d.current_url
        )
        # Fixed wait for React/SPA to render listing cards
        time.sleep(5)
        # Optionally wait for "more options" if present soon
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "[role='button'][aria-label^='אפשרויות נוספות עבור']")
                )
            )
        except Exception:
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//*[@role='button' and contains(@aria-label, 'אפשרויות נוספות')]")
                    )
                )
            except Exception:
                pass  # proceed anyway after fixed wait
        time.sleep(1)

    def _scroll_selling_page_to_load_listings(self) -> None:
        """Scroll the selling page to trigger lazy-loaded listing cards."""
        for _ in range(4):
            self.driver.execute_script(
                "window.scrollBy(0, window.innerHeight);"
            )
            time.sleep(1.5)
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

    def _find_listing_buttons(
        self, selectors: List[Tuple[Any, str]]
    ) -> Tuple[list, int, str]:
        """Find 'more options' buttons. Returns (elements, index_used, selector_used)."""
        for i, (by, sel) in enumerate(selectors):
            elms = self.driver.find_elements(by, sel)
            if elms:
                return (elms, i, sel)
        return ([], -1, "")

    def _find_clickable(
        self,
        selectors: List[Tuple[Any, str]],
        per_selector_timeout: float = 3,
    ) -> Tuple[Optional[WebElement], int, str]:
        """Try selectors in order with a short timeout each; return (element, index_used, selector_used)."""
        for i, (by, sel) in enumerate(selectors):
            try:
                el = WebDriverWait(self.driver, per_selector_timeout).until(
                    EC.element_to_be_clickable((by, sel))
                )
                return (el, i, sel)
            except Exception:
                continue
        return (None, -1, "")

    def _safe_click(self, element: WebElement) -> None:
        """Click an element; fall back to JS click if an overlay intercepts it."""
        try:
            element.click()
        except Exception as e:
            if "element click intercepted" in str(e) or "ElementClickInterceptedException" in type(e).__name__:
                log('Click intercepted by overlay, using JS click.', 'main')
                self.driver.execute_script("arguments[0].click();", element)
            else:
                raise

    def _js_click_menu_item(self, text: str) -> bool:
        """Use JavaScript to find and click a role='menuitem' by its visible text."""
        return bool(self.driver.execute_script("""
            var items = document.querySelectorAll('[role="menuitem"]');
            for (var i = 0; i < items.length; i++) {
                if ((items[i].innerText || '').includes(arguments[0])) {
                    items[i].click();
                    return true;
                }
            }
            return false;
        """, text))

    def _js_click_dialog_button(self, button_text: str, dialog_label: str = '') -> bool:
        """
        Use JavaScript to find and click a button inside a dialog by visible text
        or aria-label.  Runs in browser context so overlays are irrelevant.
        If dialog_label is given, only buttons inside a dialog whose aria-label
        contains that string are considered.
        """
        return bool(self.driver.execute_script("""
            var target = arguments[0];
            var dlgLabel = arguments[1];
            var dialogs = document.querySelectorAll('[role="dialog"]');
            /* If dialog_label given, narrow to that dialog */
            for (var d = 0; d < dialogs.length; d++) {
                var da = dialogs[d].getAttribute('aria-label') || '';
                if (dlgLabel && !da.includes(dlgLabel)) continue;
                var btns = dialogs[d].querySelectorAll('[role="button"], button');
                /* First pass: prefer a button with matching aria-label AND visible text */
                for (var b = 0; b < btns.length; b++) {
                    var btn = btns[b];
                    var label = btn.getAttribute('aria-label') || '';
                    var txt   = (btn.innerText || '').trim();
                    if (label === target && txt === target) {
                        btn.click();
                        return true;
                    }
                }
                /* Second pass: match aria-label alone (text may be empty) */
                for (var b = 0; b < btns.length; b++) {
                    var btn = btns[b];
                    var label = btn.getAttribute('aria-label') || '';
                    if (label === target) {
                        btn.click();
                        return true;
                    }
                }
            }
            return false;
        """, button_text, dialog_label))

    def _dump_selling_page_debug_html(self) -> None:
        """Write current page HTML to a file when no listings are found (for debugging selectors)."""
        if self._is_chrome_error_page():
            log('Skipping debug dump: page is a browser error (e.g. redirect loop), not Facebook.', 'main')
            return
        path = "selling_page_debug.html"
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            log(f'Debug: saved page HTML to {path}', 'main')
        except Exception as e:
            log(f'Could not save debug HTML: {e}', 'failure')

    def delete_all_items(self) -> int:
        """
        Delete all items from Facebook Marketplace selling page.
        Hebrew UI flow: "אפשרויות נוספות עבור" -> "מחיקת המודעה" -> "מחיקה" (confirm).

        Primary approach: JavaScript clicks (run inside the browser, bypass overlays).
        Fallback: Selenium selectors with _safe_click.
        """
        log('Starting to delete all marketplace items...', 'main')
        selling_url = 'https://www.facebook.com/marketplace/you/selling'

        # --- Navigate to selling page with redirect-loop handling ---
        self.driver.get(selling_url)
        time.sleep(5)
        if self._is_chrome_error_page():
            log('Redirect loop detected. Trying via facebook.com first...', 'main')
            self.driver.get('https://www.facebook.com/')
            time.sleep(4)
            self.driver.get(selling_url)
            time.sleep(5)
        if self._is_chrome_error_page():
            log(
                'Facebook redirected too many times. Clear cookies and log in again: '
                'run renew_cookies(email).',
                'failure',
            )
            return 0

        self._wait_selling_page_ready()
        self._scroll_selling_page_to_load_listings()
        time.sleep(2)

        deleted_count = 0
        consecutive_failures = 0
        max_consecutive_failures = 5

        # --- Selenium fallback selectors (used only if JS click fails) ---

        more_options_selectors = [  # type: List[Tuple[Any, str]]
            (By.CSS_SELECTOR, "[role='button'][aria-label^='אפשרויות נוספות עבור']"),
            (By.XPATH, "//*[@role='button' and starts-with(@aria-label, 'אפשרויות נוספות עבור')]"),
            (By.CSS_SELECTOR, "[role='button'][aria-label*='אפשרויות נוספות']"),
            (By.CSS_SELECTOR, "button[aria-label='More options']"),
            (By.CSS_SELECTOR, "button[aria-label='More']"),
        ]

        delete_menu_fallback = [  # type: List[Tuple[Any, str]]
            (By.XPATH, "//div[@role='menuitem'][.//span[contains(text(),'מחיקת המודעה')]]"),
            (By.XPATH, "//span[text()='מחיקת המודעה']/ancestor::div[@role='menuitem']"),
            (By.XPATH, "//div[@role='menuitem']//span[contains(text(),'מחיקת המודעה')]"),
            (By.XPATH, "//div[@role='menuitem']//span[contains(text(),'Delete')]"),
            (By.XPATH, "//div[@role='menuitem']//span[contains(text(),'מחק')]"),
        ]

        confirm_fallback = [  # type: List[Tuple[Any, str]]
            (By.XPATH, "//div[@role='dialog']//div[@role='button'][@aria-label='מחיקה']"),
            (By.XPATH, "//div[@role='dialog' and contains(@aria-label,'מחיקת מודעה')]//*[@role='button'][@aria-label='מחיקה']"),
            (By.XPATH, "//div[@role='dialog' and contains(@aria-label,'מחיקת מודעה')]//div[@role='button'][text()='מחיקה']"),
        ]

        fallbacks_used = []  # type: List[Tuple[str, str]]

        while True:
            # --- Find listing "more options" buttons ---
            more_buttons, more_idx, more_sel = self._find_listing_buttons(
                more_options_selectors
            )
            if not more_buttons:
                if deleted_count == 0:
                    self._dump_selling_page_debug_html()
                    log('No listings found to delete.', 'failure')
                else:
                    log('No more listings found to delete.', 'success')
                break

            if more_idx > 0:
                fallbacks_used.append(("more_options", more_sel))
            log(
                f'Found {len(more_buttons)} listing(s) | more_options: selector #{more_idx + 1} used',
                'main',
            )

            more_btn = more_buttons[0]
            try:
                # --- Click "more options" ---
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", more_btn
                )
                time.sleep(0.5)
                self._safe_click(more_btn)
                time.sleep(1)

                # --- Click "delete listing" in the menu ---
                del_method = "JS"
                if not self._js_click_menu_item('מחיקת המודעה'):
                    log('  JS menu click missed, trying Selenium fallback...', 'main')
                    delete_btn, del_idx, del_sel = self._find_clickable(
                        delete_menu_fallback, per_selector_timeout=3
                    )
                    if not delete_btn:
                        log('Could not find delete menu option; dismissing menu.', 'failure')
                        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                        time.sleep(1)
                        consecutive_failures += 1
                        if consecutive_failures >= max_consecutive_failures:
                            log(f'Stopping after {max_consecutive_failures} consecutive failures.', 'failure')
                            self._dump_selling_page_debug_html()
                            break
                        continue
                    del_method = f"Selenium #{del_idx + 1}"
                    fallbacks_used.append(("delete_menu", del_sel))
                    self._safe_click(delete_btn)
                log(f'  delete_menu: {del_method} used', 'main')

                # Wait for the dialog to appear
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "[role='dialog']")
                        )
                    )
                except Exception:
                    pass
                time.sleep(0.5)

                # --- Click confirm in the dialog ---
                conf_method = "JS"
                if not self._js_click_dialog_button('מחיקה', 'מחיקת מודעה'):
                    log('  JS confirm click missed, trying Selenium fallback...', 'main')
                    confirm_btn, conf_idx, conf_sel = self._find_clickable(
                        confirm_fallback, per_selector_timeout=3
                    )
                    if not confirm_btn:
                        log('Could not find confirm button; pressing Escape.', 'failure')
                        self._dump_selling_page_debug_html()
                        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                        time.sleep(1)
                        consecutive_failures += 1
                        if consecutive_failures >= max_consecutive_failures:
                            log(f'Stopping after {max_consecutive_failures} consecutive failures.', 'failure')
                            break
                        continue
                    conf_method = f"Selenium #{conf_idx + 1}"
                    fallbacks_used.append(("confirm", conf_sel))
                    self._safe_click(confirm_btn)
                log(f'  confirm: {conf_method} used', 'main')

                # Wait for the confirmation dialog to close
                try:
                    WebDriverWait(self.driver, 10).until_not(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "[role='dialog']")
                        )
                    )
                except Exception:
                    time.sleep(2)
                time.sleep(1)

                # Verify the listing count actually decreased
                new_buttons, _, _ = self._find_listing_buttons(more_options_selectors)
                if len(new_buttons) >= len(more_buttons):
                    log('Listing count did not decrease — deletion may have failed.', 'failure')
                    consecutive_failures += 1
                    if consecutive_failures >= max_consecutive_failures:
                        log(f'Stopping after {max_consecutive_failures} consecutive failures.', 'failure')
                        self._dump_selling_page_debug_html()
                        break
                    continue

                deleted_count += 1
                consecutive_failures = 0
                log(f'Successfully deleted listing #{deleted_count}', 'success')

                # Re-scroll every 5 deletions to load lazy-loaded listings
                if deleted_count % 5 == 0:
                    self._scroll_selling_page_to_load_listings()
                    time.sleep(1)

            except Exception as e:
                log(f'Error deleting listing: {str(e)}', 'failure')
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    log(f'Stopping after {max_consecutive_failures} consecutive failures.', 'failure')
                    break
                time.sleep(2)
                self.driver.get(selling_url)
                time.sleep(3)
                self._wait_selling_page_ready()
                self._scroll_selling_page_to_load_listings()

        if deleted_count > 0:
            log(f'Deletion complete. Total items deleted: {deleted_count}', 'success')
        else:
            log('Deletion complete. No items were deleted.', 'failure')

        if fallbacks_used:
            seen = {}  # type: Dict[str, str]
            for step, sel in fallbacks_used:
                seen[step] = sel
            log(
                'FALLBACK USED: Selenium selectors were used (JS click failed). '
                'Check if the JS helpers need updating:',
                'failure',
            )
            for step, sel in seen.items():
                log(f'  {step}: {sel!r}', 'failure')
            lines = []
            for step, sel in seen.items():
                lines.append(f'  - {step}: {sel!r}')
            prompt_text = (
                '\n===== COPY-PASTE THIS PROMPT =====\n'
                'The following selectors are working but are not first in line — '
                'please move them to the head of their respective list in Lister.py:\n'
                + '\n'.join(lines)
                + '\n=================================='
            )
            print(prompt_text)

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
