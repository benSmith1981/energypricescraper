from flask import Flask, render_template, request, Response, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from bs4 import BeautifulSoup
import pandas as pd
import time
import csv
import os
from io import StringIO
import json

app = Flask(__name__)
CORS(app)

# Define the mapping from postcode to region ID
postcode_region_map = {
    "NR26 8PH": 10, "LE4 5GH": 11, "DA16 3RQ": 12, "WA13 0TS": 13,
    "B13 0TY": 14, "YO26 4YG": 15, "CA2 6TR": 16, "AB11 7UR": 17,
    "KA3 2HU": 18, "TW18 1NQ": 19, "PO33 1AR": 20, "CF15 7LY": 21,
    "BS4 1QY": 22, "HD2 1RE": 23
}
def clear_cache(driver):
    """Navigates to the clear cache page and clears the cache."""
    driver.get('chrome://settings/clearBrowserData')
    wait = WebDriverWait(driver, 10)
    clear_data_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//settings-ui')))
    clear_data_button.send_keys(Keys.ENTER)

def setup_driver():
    """Setup Chrome WebDriver with necessary options, adjusting for Heroku and local environments."""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920x1080")

    # Determine if the code is running on Heroku
    if 'DYNO' in os.environ:
        # On Heroku, use the environment variables and headless mode
        chrome_options.binary_location = os.getenv('GOOGLE_CHROME_BIN')
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(executable_path=os.getenv('CHROMEDRIVER_PATH'), chrome_options=chrome_options)
    else:
        # Local executable path for development (update the path to where your chromedriver is located)
        path_to_chromedriver = '/Users/bensmith/Downloads/chromedriver-mac-x64/chromedriver'
        driver = webdriver.Chrome(executable_path=path_to_chromedriver, options=chrome_options)

    return driver


# def setup_driver():
#     """Setup Chrome WebDriver with necessary options."""
#     chrome_options = Options()
#     # chrome_options.add_argument("--incognito")  # Open the browser in incognito mode.
#     # chrome_options.add_argument("--headless")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     chrome_options.add_argument("--window-size=1920x1080")
#     path_to_chromedriver = '/Users/bensmith/Downloads/chromedriver-mac-x64/chromedriver'
    
#     driver = webdriver.Chrome(executable_path=path_to_chromedriver, options=chrome_options)
#     return driver

def navigate_and_scrapeNEW(url, postcode):
    driver = setup_driver()
    driver.get(url)
    print("Navigated to URL:", url)

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        print("Page loaded successfully.")
    except Exception as e:
        print("Error loading page:", e)
        driver.quit()
        return None

    # Accept cookies
    try:
        cookie_accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Accept')]"))
        )
        cookie_accept_button.click()
        print("Cookie overlay accepted.")
    except Exception as e:
        print("No cookie button found or not clickable:", e)

    # Click the Energy button
    try:
        energy_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Energy')]"))
        )
        energy_button.click()
        print("Energy button clicked.")
    except Exception as e:
        print("Failed to click Energy button:", e)
        driver.quit()
        return None

    # Enter postcode and start comparison
    try:
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.NAME, "postcode")))
        postcode_input = driver.find_element(By.NAME, "postcode")
        postcode_input.send_keys(postcode)
        driver.find_element(By.XPATH, "//button[contains(text(), 'Start now')]").click()
        print("Postcode entered and start button clicked.")
    except Exception as e:
        print("Failed during postcode entry:", e)
        driver.quit()
        return None

    # Navigate through conditional screens
    reached_email_input = False
    attempt_count = 0

    while not reached_email_input and attempt_count < 10:  # Prevent infinite loops
        attempt_count += 1
        try:
            # Check if the email input or skip button is present on the page
            email_input = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "email-address-input")))
            email_input.send_keys("tester@gmail.com")
            print("Email entered.")
            reached_email_input = True
            break
        except:
            print("Navigating interactive pages...")

            # Handle interaction-required pages
            if not handle_interactive_pages(driver):
                print("User intervention required.")
                input("Adjust the browser to the correct state and press Enter to continue...")
                print("Resuming automation...")

    if not reached_email_input:
        print("Failed to navigate through the site automatically.")
        driver.quit()
        return None

    # Final steps to retrieve and save data
    final_continuation(driver, postcode)

def handle_interactive_pages(driver):
    try:
        # Try clicking the skip button if available
        skip_button = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Skip')]")))
        skip_button.click()
        print("Skip button clicked.")
        return True
    except Exception:
        print("Skip button not found, checking for radio buttons or continue button.")

    try:
        # Select the first radio button if present
        radio_button = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='radio']")))
        radio_button.click()
        print("Radio button selected.")

        # Click the 'Continue' button
        continue_button = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continue')]")))
        continue_button.click()
        print("Continue button clicked.")
        return True
    except Exception as e:
        print(f"Interactive navigation failed: {e}")
        return False

def final_continuation(driver, postcode):
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Continue')]")))
        continue_button_email = driver.find_element(By.XPATH, "//button[contains(text(), 'Continue')]")
        continue_button_email.click()
        print("Final continue button clicked.")
    except Exception as e:
        print("Failed to click final continue button:", e)
        driver.quit()
        return None
    
    # Additional steps to scrape and process data
    data = scrape_data(driver, postcode)
    if data is not None:
        data.to_csv('/tmp/scraped_data.csv', index=False)  # Save to temporary file
    driver.quit()
    return data


def navigate_and_scrape(url, postcode):
    driver = setup_driver()
    # clear_cache(driver)  # Clear cache before navigating to the URL
    driver.get(url)
    print("Navigated to URL:", url)

    try:
        WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        print("Page loaded successfully.")
    except Exception as e:
        print("Error loading page:", e)
        driver.quit()
        return None

    try:
        cookie_accept_button = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.ucb-btn-accept.ucb-btn-accept--desktop[data-type='accept-all']"))
        )
        cookie_accept_button.click()
        print("Cookie overlay accepted.")
    except Exception as e:
        print("No cookie button found or not clickable:", e)

    try:
        energy_button = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/gas-electricity/') and contains(@class, 'ev-1a1odnc')]"))
        )
        energy_button.click()
        print("Energy button clicked.")
    except Exception as e:
        print("Failed to click Energy button:", e)
        driver.quit()
        return None

    try:
        WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.NAME, "postcode")))
        postcode_input = driver.find_element(By.NAME, "postcode")
        postcode_input.send_keys(postcode)
        driver.find_element(By.XPATH, "//button[contains(text(), 'Compare energy')]").click()
        print("Postcode entered and compare button clicked.")
    except Exception as e:
        print("Failed during postcode entry:", e)
        driver.quit()
        return None

    try:
        WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.NAME, "address.id")))
        address_dropdown = driver.find_element(By.NAME, "address.id")
        address_dropdown.click()
        address_dropdown.find_elements(By.TAG_NAME, 'option')[1].click()
        print("Address selected.")
    except Exception as e:
        print("Failed to select address:", e)
        driver.quit()
        return None

    try:
        WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.XPATH, "//label[@for='isBillPayerConfirmed']")))
        confirm_button = driver.find_element(By.XPATH, "//label[@for='isBillPayerConfirmed']")
        confirm_button.click()
        continue_button = WebDriverWait(driver, 1).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continue')]"))
        )
        continue_button.click()
        # driver.find_element(By.XPATH, "//button[contains(text(), 'Continue')]").click()
        print("Bill payer confirmed and continue clicked.")
    except Exception as e:
        print("Failed to confirm bill payer or continue:", e)
        driver.quit()
        return None

    # Navigate through conditional screens
    # reached_email_input = False
    # attempt_count = 0

    # while not reached_email_input and attempt_count < 10:  # Prevent infinite loops
    #     attempt_count += 1
    #     try:
    #         # Check if the email input or skip button is present on the page
    #         email_input = WebDriverWait(driver, 2).until(
    #             EC.presence_of_element_located((By.ID, "email-address-input")))
    #         email_input.send_keys("tester@gmail.com")
    #         print("Email entered.")
    #         reached_email_input = True
    #         break
    #     except:
    #         print("Navigating interactive pages...")

    #         # Handle interaction-required pages
    #         print("User intervention required. Adjust the browser to the correct state and press Enter to continue...")
    #         input("Press Enter in the console to continue once the page is correctly set...")
    #         print("Resuming automation...")

    # if not reached_email_input:
    #     print("Failed to navigate through the site automatically.")
    #     driver.quit()
    #     return None

    # # Navigate through conditional screens
    # reached_email_input = False
    # attempt_count = 0

    # while not reached_email_input and attempt_count < 10:  # Prevent infinite loops
    #     attempt_count += 1
    #     try:
    #         # Check if the email input or skip button is present on the page
    #         email_input = WebDriverWait(driver, 2).until(
    #             EC.presence_of_element_located((By.ID, "email-address-input")))
    #         email_input.send_keys("tester@gmail.com")
    #         print("Email entered.")
    #         reached_email_input = True
    #         break
    #     except:
    #         print("Navigating interactive pages...")

    #         # Handle interaction-required pages
    #         if not handle_interactive_pages(driver):
    #             print("User intervention required.")
    #             input("Adjust the browser to the correct state and press Enter to continue...")
    #             print("Resuming automation...")

    # if not reached_email_input:
    #     print("Failed to navigate through the site automatically.")
    #     driver.quit()
    #     return None


    # Locate and click the 'Skip' button
    try:
        skip_button = WebDriverWait(driver, 4).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'whitespace-break-spaces') and contains(text(), 'Skip')]"))
            # EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/gas-electricity/') and contains(@class, 'ev-1a1odnc')]"))
        )
        skip_button.click()
        print("Skip button clicked")
    except Exception as e:
        print(e)
        # Navigate through potentially multiple screens with radio buttons and continue buttons
        # reached_email_input = False
        # attempt_count = 0

        # while not reached_email_input and attempt_count < 10:  # Prevent infinite loops
        #     attempt_count += 1
        #     try:
        #         # Check if the email input or skip button is present on the page
        #         email_input = WebDriverWait(driver, 2).until(
        #             EC.presence_of_element_located((By.ID, "email-address-input")))
        #         email_input.send_keys("tester@gmail.com")
        #         print("Email entered.")
        #         reached_email_input = True
        #         break
        #     except Exception:
        #         try:
        #             # Try clicking the skip button if available
        #             skip_button = WebDriverWait(driver, 2).until(
        #                 EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Skip')]")))
        #             skip_button.click()
        #             print("Skip button clicked.")
        #             continue  # Continue to check for email input again
        #         except Exception:
        #             print("Skip button not found, checking for radio buttons or continue button.")
        #             # Select the first radio button if present
        #             try:
        #                 radio_button = WebDriverWait(driver, 2).until(
        #                     EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='radio']")))
        #                 radio_button.click()
        #                 print("Radio button selected.")
        #             except Exception:
        #                 print("No radio buttons found.")

        #             # Click the 'Continue' button
        #             try:
        #                 continue_button = WebDriverWait(driver, 2).until(
        #                     EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continue')]")))
        #                 continue_button.click()
        #                 print("Continue button clicked.")
        #             except Exception as e:
        #                 print("No continue button found or not clickable:", e)
        #                 driver.quit()
        #                 return None

    try:
        # Check if the email input or skip button is present on the page
        email_input = WebDriverWait(driver, 4).until(
            EC.presence_of_element_located((By.ID, "email-address-input")))
        email_input.send_keys("tester@gmail.com")
        print("Email entered.")
    except Exception as e:
        print("email not entered? {e}")

    try:
        continue_button = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continue')]")))
        continue_button.click()
        # WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Continue')]")))
        # continue_button_email = driver.find_element(By.XPATH, "//button[contains(text(), 'Continue')]")
        # continue_button_email.click()
        print("Final continue button clicked.")
    except Exception as e:
        print("Failed to click final continue button:", e)
        driver.quit()
        return None
    
    try:
        filter_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-event-label='filters-open']"))
        )
        filter_button.click()
        print("Filter button clicked.")
    except Exception as e:
        print("Failed to click Filter button:", e)
        driver.quit()
        return None

    try:
        div_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//aside[@aria-label='Dialog: results page filters']//div[contains(text(), 'Include plans that require switching directly through the supplier')]"))
        )
        div_element.click()
    except Exception as e:
        print("Failed to click Radio button:", e)
        driver.quit()
        return None

    try:
        aside_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "aside[aria-label='Dialog: results page filters']"))
        )
        show_results_button = aside_element.find_element(By.CSS_SELECTOR, "button[type='submit']")
        show_results_button.click()
        print("Show results button clicked.")
    except Exception as e:
        print("Failed to click Show results button:", e)
        driver.quit()
        return None

    try:
        for _ in range(4):
            see_more_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-event-action='show-more-plans']"))
            )
            # Scroll to the bottom of the page
            driver.find_element_by_tag_name('body').send_keys(Keys.END)
            see_more_button.click()
            print("See more results button clicked.")
    except Exception as e:
        print("Failed to click See more results button:", e)

    time.sleep(3)  # Wait for the results page to load completely

    data = scrape_data(driver,postcode)
    driver.quit()
    if data is not None:
        data.to_csv('/tmp/scraped_data.csv', index=False)  # Save to temporary file
    return data

import json
import re

def extract_fulfillable_data(driver):
    # Load the page source into BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Initialize container for the extracted fulfillable data
    fulfillable_data = {}

    # Loop through each script tag
    for script in soup.find_all("script"):
        # Check if script tag has contents
        if script.contents:
            content = script.contents[0]  # Access the first item of contents
            # Look for dataLayer pushes that contain 'isFulfillable'
            if 'dataLayer.push' in content and 'isFulfillable' in content:
                print("Found target script with 'isFulfillable'.")
                try:
                    # Extract the JSON object from the script
                    json_str = re.search(r'dataLayer.push\((\{.*?\})\);', content, re.DOTALL).group(1)
                    data = json.loads(json_str)
                    
                    # Navigate through the nested structure (assuming structure is known and consistent)
                    comparisons = data['energy']['results']['comparisons']
                    for comp in comparisons:
                        plan_name = comp['plan']['name']
                        is_fulfillable = comp['isFulfillable']
                        fulfillable_data[plan_name] = is_fulfillable
                        print(f"Plan: {plan_name}, Is Fulfillable: {is_fulfillable}")

                except json.JSONDecodeError as e:
                    print(f"Failed to decode JSON: {e}")
                except AttributeError as e:
                    print(f"Regex did not match: {e}")
                except KeyError as e:
                    print(f"Key error: {e}")
        else:
            print("Script tag is empty.")

    return fulfillable_data


def scrape_data(driver, postcode):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    cards = soup.select('div.styles-module__resultCardWhole___cIuF2')
    region = postcode_region_map.get(postcode, 'Unknown')
    fulfillable_data = extract_fulfillable_data(driver)

    data_list = []
    for index, card in enumerate(cards, start=1):
        company = card.find('span', class_='styles-module__titleStyles___2itRu').text.strip()
        rates = card.select_one('div.type-body-sm.styles-module__chargesGridContainerStyle___F3ffm')
        unit_rates = [rate.text.strip('p') for rate in rates.find_all('div', class_='type-bold-sm')]
        early_exit_fee = card.select_one('div.styles-module__earlyExitFee___-Jc4E').text.split(': ')[1]
        annual_cost = card.select('div.styles-module__priceStyle___x0We9.type-heading-sm')[1].text.strip('£').replace(',', '')

        # Extract plan name from data-nerd-props attribute JSON
        plan_props = json.loads(rates['data-nerd-props'])
        plan_name = plan_props.get('element_text', 'Unknown')

        # Match plan name with fulfillable data
        is_fulfillable = 'Unknown'
        for name, fulfillable in fulfillable_data.items():
            if plan_name in name or name in plan_name:
                is_fulfillable = fulfillable
                break

        data_list.append({
            'Region': region,
            'Ranking': index,
            'Company': company,
            'Unit Rate Gas (kWh)': unit_rates[0],
            'Standing Charge Gas (Day)': unit_rates[1],
            'Unit Rate Elec (kWh)': unit_rates[2],
            'Standing Charge Elec (Day)': unit_rates[3],
            'Early Exit Fee': early_exit_fee,
            'Estimated Annual Cost': annual_cost,
            'Is Fulfillable': is_fulfillable
        })

    return pd.DataFrame(data_list)


# def clear_existing_data(filepath):
#     """ Clear the existing CSV file content before a new scrape. """
#     if os.path.exists(filepath):
#         os.remove(filepath)

# import pandas as pd
# import os

# def save_scraped_data(dataframe, filepath):
#     """Save or append scraped data to a CSV file."""
#     if os.path.exists(filepath):
#         existing_data = pd.read_csv(filepath)
#         combined_data = pd.concat([existing_data, dataframe], ignore_index=True)
#         combined_data.to_csv(filepath, index=False)
#     else:
#         dataframe.to_csv(filepath, index=False)

# def load_data(filepath):
#     """Load data from CSV file if exists."""
#     if os.path.exists(filepath):
#         return pd.read_csv(filepath)
#     return pd.DataFrame()  # Return an empty DataFrame if file doesn't exist

# def scrape_and_save_data(postcodes, url, filepath):
#     """Scrape data for a list of postcodes and save to a CSV file."""
#     existing_data = load_data(filepath)
#     for postcode in postcodes:
#         scraped_data = navigate_and_scrape(url, postcode)
#         if scraped_data is not None:
#             existing_data = pd.concat([existing_data, scraped_data], ignore_index=True)
#     save_scraped_data(existing_data, filepath)
#     return existing_data


# @app.route('/', methods=['GET', 'POST'])
# def index():
#     filepath = '/tmp/scraped_data.csv'
#     data_table = None

#     if request.method == 'POST':
        # postcodes = [
        #     "NR26 8PH", "LE4 5GH" 
        #     ,"DA16 3RQ", "WA13 0TS",
        #     "B13 0TY", "YO26 4YG", "CA2 6TR", "AB11 7UR",
        #     "KA3 2HU", "TW18 1NQ", "PO33 1AR", "CF15 7LY",
        #     "BS4 1QY", "HD2 1RE"
        # ]
#         url = "https://www.uswitch.com/"
#         existing_data = scrape_and_save_data(postcodes, url, filepath)
#         data_table = existing_data.to_html(classes='data', header="true", index=False)

#     return render_template('index.html', data_table=data_table)

# @app.route('/download-csv')
# def download_csv():
#     """Serve the saved CSV file for download."""
#     filepath = '/tmp/scraped_data.csv'
#     if os.path.exists(filepath):
#         with open(filepath, 'r') as file:
#             csv_data = file.read()
#         return Response(csv_data, mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=energy_plans.csv"})
#     return "No data available for download."

def clear_existing_data(filepath):
    """ Clear the existing CSV file content before a new scrape. """
    if os.path.exists(filepath):
        os.remove(filepath)

def save_scraped_data(dataframe, filepath):
    """Save scraped data to a CSV file, overwriting any existing data."""
    dataframe.to_csv(filepath, index=False)

def scrape_and_save_data(postcodes, url, filepath):
    """Scrape data for a list of postcodes and save to a CSV file."""
    combined_data = pd.DataFrame()  # Initialize an empty DataFrame
    for postcode in postcodes:
        scraped_data = navigate_and_scrape(url, postcode)
        if scraped_data is not None:
            combined_data = pd.concat([combined_data, scraped_data], ignore_index=True)
    save_scraped_data(combined_data, filepath)
    return combined_data

@app.route('/', methods=['GET', 'POST'])
def index():
    filepath = '/tmp/scraped_data.csv'
    data_table = ""

    if request.method == 'POST':
        if request.form.get('action') == 'Clear Data':
            clear_existing_data(filepath)
            data_table = ""
        elif request.form.get('action') == 'Scrape Data':
            postcodes = [
                "NR26 8PH"
                # , "LE4 5GH" 
                # ,"DA16 3RQ", "WA13 0TS",
                # "B13 0TY", "YO26 4YG", "CA2 6TR", "AB11 7UR",
                # "KA3 2HU", "TW18 1NQ", "PO33 1AR", "CF15 7LY",
                # "BS4 1QY", 
                # "HD2 1RE"
            ]
            url = "https://www.uswitch.com/"
            clear_existing_data(filepath)  # Optional: Clear data before new scrape
            scraped_data = scrape_and_save_data(postcodes, url, filepath)
            data_table = scraped_data.to_html(classes='data', header="true", index=False)

    return render_template('index.html', data_table=data_table)

@app.route('/download-csv')
def download_csv():
    """Serve the saved CSV file for download."""
    filepath = '/tmp/scraped_data.csv'
    if os.path.exists(filepath):
        return Response(open(filepath, 'r'), mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=energy_plans.csv"})
    return "No data available for download."

if __name__ == '__main__':
    app.run(debug=True)
