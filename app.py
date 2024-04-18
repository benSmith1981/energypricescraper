from flask import Flask, render_template, request, Response, jsonify, send_from_directory
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode

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
all_data_path = '/tmp/combined_scraped_data.csv' # Path for the combined CSV file

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
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(executable_path=os.getenv('CHROMEDRIVER_PATH'), chrome_options=chrome_options)
    else:
        # Local executable path for development (update the path to where your chromedriver is located)
        path_to_chromedriver = '/Users/bensmith/Downloads/chromedriver-mac-x64/chromedriver'
        driver = webdriver.Chrome(executable_path=path_to_chromedriver, options=chrome_options)

    return driver

def click_radio_button_by_text(driver, text):
    try:
        # Construct an XPath that finds a label containing specific text and clicks it
        # This XPath assumes the text is within a <div> inside the <label>
        label_xpath = f"//label[.//div[contains(text(), '{text}')]]"
        radio_label = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.XPATH, label_xpath))
        )
        radio_label.click()
        print(f"Clicked radio button with text: {text}")
    except Exception as e:
        print(f"Failed to click radio button with text '{text}': {e}")

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
    reached_email_input = False
    attempt_count = 0


    # Locate and click the 'Skip' button
    try:
        # Locate the button by partial text content
        WebDriverWait(driver, 4).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Skip')]"))
        )
        skip_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Skip')]")
        skip_button.click()

        print("Skip button clicked")
    except Exception as e:
        print("Skip not clicked")
        print(e)
        # Navigate through potentially multiple screens with radio buttons and continue buttons
        reached_email_input = False
        attempt_count = 0

        while not reached_email_input and attempt_count < 10:  # Prevent infinite loops
            attempt_count += 1
            try:
                # Check if the email input or skip button is present on the page
                email_input = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.ID, "email-address-input")))
                email_input.send_keys("tester@gmail.com")
                print("Email entered.")
                reached_email_input = True
                break
            except Exception:
                try:
                    # Try clicking the skip button if available
                    skip_button = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Skip')]")))
                    skip_button.click()
                    print("Skip button clicked.")
                    continue  # Continue to check for email input again
                except Exception:
                    print("Skip button not found, checking for radio buttons or continue button.")

                    # click_radio_button_by_text(driver, "Yes")
                    try:
                        # Wait for the label associated with the 'yes' option to be clickable and click it
                        WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "label[for='249']"))
                        )
                        no_option_label = driver.find_element(By.CSS_SELECTOR, "label[for='249']")
                        no_option_label.click()
                        print("Clicked 'yes' radio button for the Economy 7 meter question.")
                    except Exception as e:
                        print("Failed to click 'yees' radio button:", e)

                    # Click the 'Continue' button
                    try:
                        continue_button = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continue')]")))
                        continue_button.click()
                        print("Continue button clicked.")
                    except Exception as e:
                        print("No continue button found or not clickable:", e)
                        driver.quit()
                        return None
                    
                    # Do you use gas? Wait for the label associated with the 'Yes' option to be clickable and click it
                    # click_radio_button_by_text(driver, "Yes")
                    try:
                        # Do you use gas? Wait for the label associated with the 'Yes' option to be clickable and click it
                        WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "label[for='249']"))
                        )
                        yes_option_label = driver.find_element(By.CSS_SELECTOR, "label[for='249']")
                        yes_option_label.click()
                        print("Do you use gas? 'Yes' .")
                    except Exception as e:
                        print("Failed to click 'Yes' option for Do you use gas?:", e)
                    
                    # Click the 'Continue' button
                    try:
                        continue_button = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continue')]")))
                        continue_button.click()
                        print("Continue button clicked.")
                    except Exception as e:
                        print("No continue button found or not clickable:", e)
                        driver.quit()
                        return None
                    
                    # Dual Fuel Tarriff: Wait for the label associated with the 'No' option to be clickable and click it
                    click_radio_button_by_text(driver, "No")

                    # Click the 'Continue' button
                    try:
                        continue_button = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continue')]")))
                        continue_button.click()
                        print("Continue button clicked.")
                    except Exception as e:
                        print("No continue button found or not clickable:", e)
                        driver.quit()
                        return None
                    
                    # Which supplier are you with? Click the 'Continue' Bristih gas button
                    try:
                        continue_button = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continue')]")))
                        continue_button.click()
                        print("Continue Which supplier are you with? button clicked.")
                    except Exception as e:
                        print("Which supplier are you with? No continue button found or not clickable:", e)
                        driver.quit()
                        return None

                        
                    # How do you pay for your energy? Select the first radio button if present
                    try:
                        # First, find the container of the radio buttons
                        container = WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.CLASS_NAME, "css-c9n7i4")))
                        
                        # Then find the first radio button within this container
                        radio_button = container.find_element(By.CSS_SELECTOR, "input[type='radio']")
                        radio_button.click()
                        print("How do you pay for your energy? Radio button selected.")
                    except Exception:
                        print("How do you pay for your energy? No radio buttons found.")

                    # Click the 'Continue' button for How do you pay for your energy?
                    try:
                        continue_button = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continue')]")))
                        continue_button.click()
                        print("Continue button clicked. How do you pay for your energy?")
                    except Exception as e:
                        print("No How do you pay for your energy? continue button found or not clickable:", e)
                        driver.quit()
                        return None
                    
                    try:
                        # What's your plan name? Locate the button by partial text content
                        WebDriverWait(driver, 4).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Skip')]"))
                        )
                        skip_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Skip')]")
                        skip_button.click()
                        print("What's your plan name? Skip button clicked")
                    except Exception as e:
                        print("What's your plan name? Skip not clicked")
                        print(e)

                    # Do you know how much you use or spend on your energy?
                    click_radio_button_by_text(driver, "No")
                    # Click the 'Continue' button Do you know how much you use or spend on your energy?
                    try:
                        continue_button = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continue')]")))
                        continue_button.click()
                        print("Continue button clicked. Do you know how much you use or spend on your energy?")
                    except Exception as e:
                        print("Do you know how much you use or spend on your energy? No continue button found or not clickable:", e)
                        driver.quit()
                        return None
                

                    # Click the 'Continue' button What size is your property?
                    try:
                        continue_button = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continue')]")))
                        continue_button.click()
                        print("What size is your property? Continue button clicked.")
                    except Exception as e:
                        print("No continue button found or not clickable: What size is your property?", e)
                        driver.quit()
                        return None


    try:
        continue_button = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continue')]")))
        continue_button.click()
        print("Final continue button clicked.")
    except Exception as e:
        print("Failed to click final continue button:", e)
        driver.quit()
        return None
    
    # current_url = driver.current_url  # Get the current URL from the browser
    # modified_url = modify_url_parameter(current_url, 'filter-only-show-fulfillable', 'false')
    # driver.get(modified_url)  # Navigate to the modified URL
    
    try:
        filter_button = WebDriverWait(driver, 10).until(
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
        driver.execute_script("arguments[0].click();", div_element)
        print("Radio button clicked through JS.")
    except Exception as e:
        print("Failed to click Radio button:", e)
        driver.quit()
        return None
    
    try:
        aside_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "aside[aria-label='Dialog: results page filters']"))
        )
        show_results_button = aside_element.find_element(By.CSS_SELECTOR, "button[type='submit']")
        
        # Using JavaScript to perform the click action
        driver.execute_script("arguments[0].click();", show_results_button)
        print("Show results button clicked using JavaScript.")
    except Exception as e:
        print("Failed to click Show results button using JavaScript:", e)
        driver.quit()
        return None

    try:
        for _ in range(2):
            # Scroll to the bottom of the page
            driver.find_element_by_tag_name('body').send_keys(Keys.END)
            see_more_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-event-action='show-more-plans']"))
            )
            
            see_more_button.click()
            print("See more results button clicked.")
            # time.sleep(2)  # slight delay to wait for the page to load more results if necessary

    except Exception as e:
        print("Failed to click See more results button:", e)

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

def extract_tariff_data(driver):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    script_content = None

    # Find the script containing the required JSON state
    for script in soup.find_all("script"):
        if 'window.__initialState__=' in script.text:
            script_content = script.text
            break

    if not script_content:
        return {
            "Electricity Day Rate": "N/A",
            "Electricity Night Rate": "N/A",
            "Electricity Standing Charge": "N/A",
            "Gas Rate": "N/A",
            "Gas Standing Charge": "N/A",
            "error": "No relevant script found"
        }

    # Extract JSON from script
    try:
        json_str = script_content.split('=', 1)[1]  # Split on the first '=' and take the second part
        json_data = json.loads(json_str)
    except Exception as e:
        return {
            "Electricity Day Rate": "N/A",
            "Electricity Night Rate": "N/A",
            "Electricity Standing Charge": "N/A",
            "Gas Rate": "N/A",
            "Gas Standing Charge": "N/A",
            "error": f"Error parsing JSON: {e}"
        }

    # Define a container for our extracted data
    extracted_data = {
        "Electricity Day Rate": "N/A",
        "Electricity Night Rate": "N/A",
        "Electricity Standing Charge": "N/A",
        "Gas Rate": "N/A",
        "Gas Standing Charge": "N/A"
    }

    # Attempt to extract data based on JSON structure
    try:
        plans = json_data["MultiComparison"]["comparisonPlans"]
        for plan in plans:
            if plan["__typename"] == "MultiComparisonPlan":
                elec = plan["electricity"]
                gas = plan["gas"]
                extracted_data["Electricity Day Rate"] = next((rate["price"] for rate in elec["tariffRate"] if not rate["nightRate"]), "N/A")
                extracted_data["Electricity Night Rate"] = next((rate["price"] for rate in elec["tariffRate"] if rate["nightRate"]), "N/A")
                extracted_data["Electricity Standing Charge"] = elec["standingCharge"]
                extracted_data["Gas Rate"] = next((rate["price"] for rate in gas["tariffRate"] if not rate["nightRate"]), "N/A")
                extracted_data["Gas Standing Charge"] = gas["standingCharge"]
    except KeyError as e:
        return {
            "Electricity Day Rate": "N/A",
            "Electricity Night Rate": "N/A",
            "Electricity Standing Charge": "N/A",
            "Gas Rate": "N/A",
            "Gas Standing Charge": "N/A",
            "error": f"Key error: {e}"
        }

    return extracted_data


def scrape_data(driver, postcode):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    cards = soup.select('div.styles-module__resultCardWhole___cIuF2')
    region = postcode_region_map.get(postcode, 'Unknown')
    fulfillable_data = extract_fulfillable_data(driver)
    tariff_data = extract_tariff_data(driver)
    if "error" in tariff_data:
        print(tariff_data["error"])  # Log error to console or handle it as needed
        return pd.DataFrame()  # Return an empty DataFrame or handle error appropriately

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
            'Is Fulfillable': is_fulfillable,
            'Electricity Day Rate (p/kWh)': tariff_data["Electricity Day Rate"],
            'Electricity Night Rate (p/kWh)': tariff_data["Electricity Night Rate"],
            'Electricity Standing Charge (p/day)': tariff_data["Electricity Standing Charge"],
            'Gas Rate (p/kWh)': tariff_data["Gas Rate"],
            'Gas Standing Charge (p/day)': tariff_data["Gas Standing Charge"]
        })

    return pd.DataFrame(data_list)

def clear_existing_data(filepath):
    """ Clear the existing CSV file content before a new scrape. """
    if os.path.exists(filepath):
        os.remove(filepath)

def save_scraped_data(dataframe, filepath):
    """Save scraped data to a CSV file, appending if file exists."""
    if os.path.exists(filepath):
        dataframe.to_csv(filepath, mode='a', header=False, index=False)
    else:
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

@app.route('/data', methods=['GET'])
def data():
    filepath = all_data_path
    if os.path.exists(filepath):
        return jsonify(pd.read_csv(filepath).to_dict(orient='records'))
    return jsonify([])  # Return an empty list if no data is available

@app.route('/')
def index():
    clear_existing_data(all_data_path)
    postcodes = [
        "NR26 8PH", "LE4 5GH", "DA16 3RQ", "WA13 0TS",
        "B13 0TY", "YO26 4YG", "CA2 6TR", "AB11 7UR",
        "KA3 2HU", "TW18 1NQ", "PO33 1AR", "CF15 7LY",
        "BS4 1QY", "HD2 1RE"
    ]
    # clear_existing_data(all_data_path)
    return render_template('index.html', postcodes=postcodes)


@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json()
    postcode = data['postcode']
    url = "https://www.uswitch.com/"
    
    # Perform scraping
    scraped_data = navigate_and_scrape(url, postcode)
    if scraped_data is not None:
        # Define filepath for combined data
        filepath = all_data_path
        
        # Check if the combined CSV exists, if not, initialize it
        if not os.path.exists(filepath):
            scraped_data.to_csv(filepath, index=False)
        else:
            # If exists, append without including the header
            scraped_data.to_csv(filepath, mode='a', header=False, index=False)
        
        return jsonify({'message': 'Scraping successful', 'filepath': 'combined_scraped_data.csv'})
    
    return jsonify({'message': 'Scraping failed', 'filepath': None}), 500


@app.route('/download_csv/<filename>')
def download_csv(filename):
    directory = '/tmp'
    try:
        return send_from_directory(directory, filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404


if __name__ == '__main__':
    app.run(debug=True)
