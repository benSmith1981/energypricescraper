from flask import Flask, render_template, request, Response
from io import StringIO
import pandas as pd
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

def scrape_data_with_selenium(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    webdriver_service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)

    try:
        driver.get(url)
        time.sleep(5)  # Adjust timing as necessary

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        cards = soup.select('div.styles-module__resultCardWhole___cIuF2')
        
        data_list = []
        for card in cards:
            company = card.find('span', class_='styles-module__titleStyles___2itRu')
            rates = card.select_one('div.type-body-sm.styles-module__chargesGridContainerStyle___F3ffm')
            early_exit_fee_element = card.select_one('div.styles-module__earlyExitFee___-Jc4E')
            annual_cost_element = card.select_one('div.styles-module__priceStyle___x0We9')

            company = company.text.strip() if company else "Unknown Company"
            early_exit_fee = early_exit_fee_element.text.split(': ')[1] if early_exit_fee_element else "N/A"
            annual_cost = annual_cost_element.text.strip('£').replace(',', '') if annual_cost_element else "0"

            if rates:
                unit_rate_gas = rates.find_all('div', class_='type-bold-sm')[0].text.strip('p') if len(rates.find_all('div', class_='type-bold-sm')) > 0 else "0"
                standing_charge_gas = rates.find_all('div', class_='type-bold-sm')[1].text.strip('p') if len(rates.find_all('div', class_='type-bold-sm')) > 1 else "0"
                unit_rate_elec = rates.find_all('div', class_='type-bold-sm')[2].text.strip('p') if len(rates.find_all('div', class_='type-bold-sm')) > 2 else "0"
                standing_charge_elec = rates.find_all('div', class_='type-bold-sm')[3].text.strip('p') if len(rates.find_all('div', class_='type-bold-sm')) > 3 else "0"
            else:
                unit_rate_gas = standing_charge_gas = unit_rate_elec = standing_charge_elec = "N/A"

            data_list.append({
                'Company': company,
                'Unit Rate (kWh)': f"{unit_rate_gas}/{unit_rate_elec}",
                'Standing Charge (Day)': f"{standing_charge_gas}/{standing_charge_elec}",
                'Early Exit Fee': early_exit_fee,
                'Estimated Annual Cost': annual_cost
            })

        return pd.DataFrame(data_list)

    finally:
        driver.quit()


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        url = request.form['url']
        data = scrape_data_with_selenium(url)
        data_csv = data.to_csv(index=False)
        return render_template('home.html', data_table=data.to_html(index=False), data_csv=data_csv)
    else:
        default_url = "https://www.uswitch.com/gas-electricity/journey/results?filter-fuel=DUAL_FUEL&filter-only-show-fulfillable=false&filter-payment-method=MONTHLY_DIRECT_DEBIT&filter-rate-type=FIXED_OR_VARIABLE&page=4"
        return render_template('home.html', default_url=default_url)

@app.route('/download-csv')
def download_csv():
    csv_data = request.args.get('data_csv')
    buffer = StringIO(csv_data)
    buffer.seek(0)
    return Response(buffer, mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=energy_plans.csv"})

if __name__ == '__main__':
    app.run(debug=True)


# def scrape_data(url):
#     try:
#         response = session.get(url)
#         response.raise_for_status()
#         # response = requests.get(url)
#         # response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
#     except RequestException as e:
#         logging.error(f"Request failed: {e}")
#         return pd.DataFrame()  # Return an empty DataFrame if the request failed

#     try:
#         soup = BeautifulSoup(response.text, 'html.parser')
#         cards = soup.select('div.styles-module__resultCardWhole___cIuF2')

#         # Lists to store data
#         data_list = []

#         for card in cards:
#             try:
#                 # Extract data from each card
#                 company = card.find('span', class_='styles-module__titleStyles___2itRu').get_text()
#                 rates = card.select_one('div.type-body-sm.styles-module__chargesGridContainerStyle___F3ffm')
#                 unit_rate_gas = rates.find_all('div', class_='type-bold-sm')[0].get_text().strip('p')
#                 standing_charge_gas = rates.find_all('div', class_='type-bold-sm')[1].get_text().strip('p')
#                 unit_rate_elec = rates.find_all('div', class_='type-bold-sm')[2].get_text().strip('p')
#                 standing_charge_elec = rates.find_all('div', class_='type-bold-sm')[3].get_text().strip('p')
#                 early_exit_fee = card.select_one('div.styles-module__earlyExitFee___-Jc4E').get_text().split(': ')[1]
#                 annual_cost = card.select_one('div.styles-module__priceStyle___x0We9').get_text().strip('£').replace(',', '')

#                 data_list.append({
#                     'Company': company,
#                     'Unit Rate (kWh)': f"{unit_rate_gas}/{unit_rate_elec}",
#                     'Standing Charge (Day)': f"{standing_charge_gas}/{standing_charge_elec}",
#                     'Early Exit Fee': early_exit_fee,
#                     'Estimated Annual Cost': annual_cost
#                 })
#             except (AttributeError, IndexError) as e:
#                 logging.warning(f"Could not parse some information from the card: {e}")

#         return pd.DataFrame(data_list)

#     except Exception as e:
#         logging.error(f"Failed to parse the webpage: {e}")
#         return pd.DataFrame()


# Test the function with the provided URL (This line is for demonstration and should be removed in the Flask app)
# data_frame = scrape_data("Your URL here")
# print(data_frame.head())

# if __name__ == '__main__':
#     app.run(debug=True)
