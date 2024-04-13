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

app = Flask(__name__)
CORS(app)

def setup_driver():
    """Setup Chrome WebDriver with necessary options."""
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920x1080")
    path_to_chromedriver = '/Users/bensmith/Downloads/chromedriver-mac-x64/chromedriver'
    driver = webdriver.Chrome(executable_path=path_to_chromedriver, options=chrome_options)
    return driver

def navigate_and_scrape(url):
    driver = setup_driver()
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
        postcode_input.send_keys("LE27JS")
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
        driver.find_element(By.XPATH, "//button[contains(text(), 'Continue')]").click()
        print("Bill payer confirmed and continue clicked.")
    except Exception as e:
        print("Failed to confirm bill payer or continue:", e)
        driver.quit()
        return None

    # Locate and click the 'Skip' button
    try:
        skip_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'whitespace-break-spaces') and contains(text(), 'Skip')]"))
            # EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/gas-electricity/') and contains(@class, 'ev-1a1odnc')]"))
        )
        skip_button.click()
        print("Skip button clicked")
    except Exception as e:
        print("Failed to click Skip button:", e)

    try:
        WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.ID, "email-address-input")))
        email_input = driver.find_element(By.ID, "email-address-input")
        email_input.send_keys("tester@gmail.com")
        print("Email entered.")
    except Exception as e:
        print("Failed during email entry:", e)
        driver.quit()
        return None

    try:
        WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Continue')]")))
        continue_button_email = driver.find_element(By.XPATH, "//button[contains(text(), 'Continue')]")
        continue_button_email.click()
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

    data = scrape_data(driver)
    driver.quit()
    if data is not None:
        data.to_csv('/tmp/scraped_data.csv', index=False)  # Save to temporary file
    return data

def scrape_data(driver):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    cards = soup.select('div.styles-module__resultCardWhole___cIuF2')

    data_list = []
    for card in cards:
        company = card.find('span', class_='styles-module__titleStyles___2itRu').text.strip()
        rates = card.select_one('div.type-body-sm.styles-module__chargesGridContainerStyle___F3ffm')
        unit_rates = [rate.text.strip('p') for rate in rates.find_all('div', class_='type-bold-sm')]
        early_exit_fee = card.select_one('div.styles-module__earlyExitFee___-Jc4E').text.split(': ')[1]
        # Extracting the 'Estimated annual cost' using the specified element
        # price_title = card.select_one('div.styles-module__priceCardTitle___KPICe')
        # if "Estimated annual cost" in price_title.text:
        #     annual_cost_value = card.select_one('div.styles-module__priceStyle___x0We9.type-heading-sm').text.strip('£').replace(',', '')
        # else:
        #     annual_cost_value = "N/A"  # If 'Estimated annual cost' is not found, mark it as 'N/A'
        annual_cost_value = card.select('div.styles-module__priceStyle___x0We9.type-heading-sm')[1].text.strip('£').replace(',', '')

        data_list.append({
            'Company': company,
            'Unit Rate Gas (kWh)': unit_rates[0],
            'Standing Charge Gas (Day)': unit_rates[1],
            'Unit Rate Elec (kWh)': unit_rates[2],
            'Standing Charge Elec (Day)': unit_rates[3],
            'Early Exit Fee': early_exit_fee,
            'Estimated Annual Cost': annual_cost_value
        })

    return pd.DataFrame(data_list)

@app.route('/', methods=['GET', 'POST'])
def index():
    default_url = "https://www.uswitch.com/"
    data_table = None
    data_csv = None
    if request.method == 'POST':
        url = request.form['url']
        scraped_data = navigate_and_scrape(url)
        data_csv = scraped_data.to_csv(index=False)

        if scraped_data is not None:
            data_table = scraped_data.to_html(classes='data', header="true", index=False)

    return render_template('index.html', default_url=default_url, data_table=data_table, data_csv=data_csv)

@app.route('/download-csv')
def download_csv():
    csv_data = request.args.get('data_csv')
    buffer = StringIO(csv_data)
    buffer.seek(0)
    return Response(buffer, mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=energy_plans.csv"})

# @app.route('/download-csv', methods=['GET'])
# def download_csv():
#     try:
#         # Specify the path to the temporary file
#         path_to_csv = '/tmp/scraped_data.csv'
#         # Send file prompt as an attachment to download
#         return send_file(path_to_csv, as_attachment=True, attachment_filename='scraped_data.csv')
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
