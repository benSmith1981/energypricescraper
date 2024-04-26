from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Specify the path to your ChromeDriver
chrome_driver_path = r"C:\Users\darren.huxtable\OneDrive - Fischer Futureheat Ltd\Documents\Python Scripts\chromedriver-win64 (1)\chromedriver-win64\chromedriver.exe"
service = Service(chrome_driver_path)

chrome_options = Options()
chrome_options.headless = False

# Initialize the WebDriver and open the website

# Disable caching
#chrome_options.add_argument("--disable-application-cache")
#chrome_options.add_argument("--disable-cache")
#chrome_options.add_argument("--disable-offline-load-stale-cache")
#chrome_options.add_argument("--disk-cache-size=0")

# Clear cookies
#chrome_options.add_argument("--disable-plugins-discovery")
#chrome_options.add_argument("--disable-local-storage")
#chrome_options.add_argument("--disable-session-storage")
#chrome_options.add_argument("--disable-web-security")
#chrome_options.add_argument("--user-data-dir=/tmp")

# Pass the service object into the service argument
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.get("https://uswitch.com")

# Instantiate a WebDriverWait object
wait = WebDriverWait(driver, 10)  # wait for a maximum of 20 seconds

# Use visibility_of_element_located to ensure the element is visible
consent_button = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".ucb-btn-accept.ucb-btn-accept--desktop")))

# Since visibility doesn't ensure clickability, let's check if it's clickable
consent_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".ucb-btn-accept.ucb-btn-accept--desktop")))

# Click the button
consent_button.click()

# repeat the process to click the Energy Button
Energy_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "body > div:nth-child(10) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(3) > a:nth-child(1) > span:nth-child(2)")))

#Click the button
Energy_button.click()

#Once the postcode selector comes up, select the box and input first postcode
postcode_box = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[placeholder='e.g. SW1A 1AA']")))
postcode_box.send_keys("DA16 3RQ")

submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.type-bold-base")))
submit_button.click()

# Navigate to the dropdown element using its CSS selector
dropdown_selector = "body > div:nth-child(2) > div:nth-child(9) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(3) > div:nth-child(1) > form:nth-child(1) > fieldset:nth-child(1) > div:nth-child(2) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > select:nth-child(1)"
dropdown = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, dropdown_selector)))

# Create a Select object to interact with the dropdown
select = Select(dropdown)

# Select the fourth entry by index
select.select_by_index(2)  # Index is zero-based; 3 represents the fourth item

# Check the checkbox if not already checked
#checkbox = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "label[for='isBillPayerConfirmed']")))
#if not driver.find_element(By.CSS_SELECTOR, "input[id='isBillPayerConfirmed']").is_selected():
#    checkbox.click()

# Locate the submit button using XPath and click it
submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='css-1uay7uz']//button[@type='submit'][normalize-space()='Continue']")))
submit_button.click()
#Do you have an economy 7 meter?

try:
    # Text to search for within the label
    text = "No"
    # XPath to find the label containing the specified text
    label_xpath = f"//label[contains(., '{text}')]"

    # Wait until the element is clickable and then click it
    radio_label = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, label_xpath)))
    radio_label.click()
    print(f"Clicked radio button with label containing: '{text}'")
except Exception as e:
    print(f"Error clicking the radio button: {str(e)}")

# Locate the submit button using XPath and click it
submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='css-1uay7uz']//button[@type='submit'][normalize-space()='Continue']")))
submit_button.click()

#Do you have gas?

try:
    # Text to search for within the label
    text = "Yes"
    # XPath to find the label containing the specified text
    label_xpath = f"//label[contains(., '{text}')]"

    # Wait until the element is clickable and then click it
    radio_label = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, label_xpath)))
    radio_label.click()
    print(f"Clicked radio button with label containing: '{text}'")
except Exception as e:
    print(f"Error clicking the radio button: {str(e)}")

# Locate the submit button using XPath and click it
submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='css-1uay7uz']//button[@type='submit'][normalize-space()='Continue']")))
submit_button.click()

#Are you on a Dual Fuel Tariff?

try:
    # Text to search for within the label
    text = "Yes"
    # XPath to find the label containing the specified text
    label_xpath = f"//label[contains(., '{text}')]"

    # Wait until the element is clickable and then click it
    radio_label = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, label_xpath)))
    radio_label.click()
    print(f"Clicked radio button with label containing: '{text}'")
except Exception as e:
    print(f"Error clicking the radio button: {str(e)}")

# Locate the submit button using XPath and click it
submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='css-1uay7uz']//button[@type='submit'][normalize-space()='Continue']")))
submit_button.click()



# Which supplier are you with - Just click continue
submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='css-1uay7uz']//button[@type='submit'][normalize-space()='Continue']")))
submit_button.click()

# How do you pay for your energy
submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='css-1uay7uz']//button[@type='submit'][normalize-space()='Continue']")))
submit_button.click()

# Just carry on...
submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='css-1uay7uz']//button[@type='submit'][normalize-space()='Continue']")))
submit_button.click()

#How much do you spend?

try:
    # Text to search for within the label
    text = "No"
    # XPath to find the label containing the specified text
    label_xpath = f"//label[contains(., '{text}')]"

    # Wait until the element is clickable and then click it
    radio_label = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, label_xpath)))
    radio_label.click()
    print(f"Clicked radio button with label containing: '{text}'")
except Exception as e:
    print(f"Error clicking the radio button: {str(e)}")


# Just carry on...
submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='css-1uay7uz']//button[@type='submit'][normalize-space()='Continue']")))
submit_button.click()

# Just carry on...
submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='css-1uay7uz']//button[@type='submit'][normalize-space()='Continue']")))
submit_button.click()


# Locate the email address input box
email_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@id='email-address-input']")))

# Clear any existing text in the input box
email_input.clear()

# Send the email address to the input box
email_input.send_keys("email@gmail.com")

# Locate the submit button using XPath and click it
submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='css-1uay7uz']//button[@type='submit'][normalize-space()='Continue']")))
submit_button.click()

# Locate the filter button using XPath and click it
filter_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Filter']")))
filter_button.click()

dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "select[name='filters.rateType']")))
    
# Create a Select object to interact with the dropdown
select = Select(dropdown)

# Select the first item in the dropdown
select.select_by_index(2)  # Indexes are zero-based

dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "select[name='filters.fuel']")))
    
# Create a Select object to interact with the dropdown
select = Select(dropdown)

# Select the first item in the dropdown (plan type)
select.select_by_index(1)  # Indexes are zero-based

try:
    # Text to search for within the label
    text = "Include plans that require switching directly through the supplier"
    # XPath to find the label containing the specified text
    label_xpath = f"//label[contains(., '{text}')]"

    # Wait until the element is clickable and then click it
    radio_label = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, label_xpath)))
    radio_label.click()
    print(f"Clicked radio button with label containing: '{text}'")
except Exception as e:
    print(f"Error clicking the radio button: {str(e)}")
    
# Locate the submit button using XPath and click it
submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Show results']")))
submit_button.click()

# Locate the more button using XPath and click it 2
more_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html[1]/body[1]/div[2]/div[3]/div[2]/div[1]/div[4]/div[1]/button[1]/span[1]")))
more_button.click()

# Locate the more button using XPath and click it 3
more_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html[1]/body[1]/div[2]/div[3]/div[2]/div[1]/div[4]/div[1]/button[1]/span[1]")))
more_button.click()

# Locate the more button using XPath and click it 4
more_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html[1]/body[1]/div[2]/div[3]/div[2]/div[1]/div[4]/div[1]/button[1]/span[1]")))
more_button.click()