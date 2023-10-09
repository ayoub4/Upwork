import re

import openai as openai
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

# Initial URL for login
login_url = "https://www.upwork.com/ab/account-security/login?redir=%2Fnx%2Ffind-work%2Fbest-matches"

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--user-data-dir=C:/Users/ayoub/AppData/Local/Google/Chrome/User Data")
chrome_options.add_argument("--profile-directory=Default")
chrome_options.add_argument("--start-maximized")  # Start Chrome in maximized mode
openai.api_key = "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"
# Get the path of the Chrome WebDriver executable using ChromeDriverManager
webdriver_service = Service(ChromeDriverManager().install())

# Initialize Chrome WebDriver
driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)

# Navigate to the login page
driver.get(login_url)

# Wait for the Google login button to be clickable
google_login_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, "login_google_submit"))
)
google_login_button.click()

# Wait for the redirection to happen after login
WebDriverWait(driver, 10).until(EC.url_to_be("https://www.upwork.com/nx/find-work/best-matches"))

# Scroll to the end of the page
last_height = driver.execute_script("return document.body.scrollHeight")
while True:
    body = driver.find_element(By.TAG_NAME, 'body')
    body.send_keys(Keys.END)

    # Wait for a second after scrolling
    time.sleep(1)

    # Calculate new scroll height and compare with the last scroll height
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

# Find all sections with the specified class using explicit wait
sections = WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.CLASS_NAME, "up-card-section.up-card-list-section.up-card-hover"))
)

# Arrays to store sections' information
job_titles = []

# Iterate through each section and extract job titles and budgets
for section in sections:
    job_title_div = section.find_element(By.CLASS_NAME, "job-tile-title")
    job_title_link = job_title_div.find_element(By.TAG_NAME, "a")
    href = job_title_link.get_attribute("href")
    text_content = job_title_link.text.strip()

    # Extract budget (handle NoSuchElementException)
    try:
        budget_span = section.find_element(By.CSS_SELECTOR, "span[data-test='budget']")
        budget_value = budget_span.text.strip().replace("$", "").replace(",", "")
        budget = float(budget_value)

        # Compare budget and add to the list if it's above $100
        if budget >= 100:
            job_titles.append({"href": href, "text": text_content, "budget": budget})
    except Exception as e:
        continue

elements_values = []
covers = []

for job in job_titles:
    print(f"Job Title: {job['text']}, Href: {job['href']}, Budget: ${job['budget']:.2f}")

    # Open link in a new tab
    driver.execute_script("window.open('', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(job['href'])

    # Wait for the page to load (adjust waiting time as needed)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
    element_value = driver.find_element(By.CSS_SELECTOR, "*[data-test='description']").text.strip()
    elements_values.append(element_value)

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system",
                   "content": f"You are Ayoub Mzari a professional Wordpress Developer with more than 3 years of experience as a Wordpress developer for a Digital services company creating and managing wordpress websites as well as its SEO, you also havce and a bachelor in the field, you are just opening up to freelancing and you're looking for projects to work on and you'll be happy to show the client your projects once contacted and you cant do that now for privacy purposes"},
                  {"role": "user",
                   "content": f"Write a motivating captive and professional cover letter to the client without addressing any personal information, the letter is to be short and informative, explain what you'll add to the project as as points (creating the website in the shortest time possible, managing it, hostign it if needed, 3 months free updates and upgrades on the need of the client) to apply for this project:" + element_value}
                  ])
    generated_text = response.choices[0].message.content.strip()
    covers.append(generated_text)

    try:
        apply_button = driver.find_element(By.CSS_SELECTOR, "[aria-label='Apply Now']")
        apply_button.click()
    except Exception as e:
        print("Apply Now button not found.")

    # Replace old URL with new URL
    job['href'] = driver.current_url

    # Find the second element with the name "milestoneMode" and click on it
    milestone_mode_elements = driver.find_elements(By.CLASS_NAME, "up-checkbox-replacement-helper")
    if len(milestone_mode_elements) >= 2:
        milestone_mode_elements[1].click()

        # Set the value of an element with id 'charged-amount-id' to the budget variable
        try:
            charged_amount_element = driver.find_element(By.ID, 'charged-amount-id')
            charged_amount_element.clear()  # Clear any existing text in the element
            # Convert the budget to an integer before sending it to the input field
            budget_int = int(job['budget'])
            #charged_amount_element.send_keys(budget_int)
            print(budget_int)  # Print the integer value
        except Exception as e:
            print("Error setting charged amount value:", e)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "[id^='dropdown-label']")))
        dropdown_element = driver.find_element(By.CSS_SELECTOR, "[id^='dropdown-label']")
        dropdown_element.click()

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Less than 1 month')]")))
        less_than_one_month_element = driver.find_element(By.XPATH, "//*[contains(text(), 'Less than 1 month')]")
        less_than_one_month_element.click()

        # Find the element with attribute aria-labelledby="cover_letter_label" and set its value to generated_text
        try:
            textarea_element = driver.find_element(By.CSS_SELECTOR, "[aria-labelledby='cover_letter_label']")
            textarea_element.clear()  # Clear any existing text in the textarea
            textarea_element.send_keys(generated_text)  # Set the value of the textarea to generated_text
        except Exception as e:
            print("Error setting textarea value:", e)

        """try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-ev-label='boost_set_bid_amount']")))
            boost_set_bid_element = driver.find_element(By.CSS_SELECTOR, "[data-ev-label='boost_set_bid_amount']")
            boost_set_bid_element.click()

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "up-table.up-table-bordered")))
            table_element = driver.find_element(By.CLASS_NAME, "up-table.up-table-bordered")
            rows = table_element.find_elements(By.TAG_NAME, "tr")
            third_row = rows[2] if len(rows) > 2 else None  # Check if third row exists
            if third_row:
                second_td = third_row.find_elements(By.TAG_NAME, "td")[1] if len(
                    third_row.find_elements(By.TAG_NAME, "td")) > 1 else None  # Check if second td in third row exists
                if second_td:
                    div_inside_td = second_td.find_element(By.TAG_NAME, "div")
                    div_text = div_inside_td.text.strip()
                    numbers_only = re.sub(r'\D', '', div_text)
                    div_text_2 = numbers_only[:2]
                else:
                    div_text_2 = "1"  # Set default value if second td doesn't exist
            else:
                div_text_2 = "1"  # Set default value if third row doesn't exist
            # This removes all non-digit characters from the string
            connects = (int(div_text_2) +1)  #

            boost_bid_amount_input = driver.find_element(By.ID, "boost-bid-amount")
            boost_bid_amount_input.clear()  # Clear any existing text in the input field
            boost_bid_amount_input.send_keys(connects)  # Set the value of the input field to the 'connects' variable

            boost_add_or_edit_bid_button = driver.find_element(By.CSS_SELECTOR,
                                                               "[data-ev-label='boost_add_or_edit_bid']")
            boost_add_or_edit_bid_button.click()
        except TimeoutException:
            print("Bid system not available")"""

        try:
            final_button = driver.find_element(By.CLASS_NAME, "up-btn.up-btn-primary.m-0")
            final_button.click()
            # Wait for the presence of the modal dialog
            modal_dialog = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "up-modal-dialog"))
            )

            # Find the checkbox element inside the modal and click on it
            checkbox_element = modal_dialog.find_element(By.NAME, "checkbox")
            checkbox_element.click()

            # Find the button inside the modal and click on it
            modal_button = modal_dialog.find_element(By.CLASS_NAME, "btn-primary")
            modal_button.click()

        except Exception as e:
            print("Error handling modal dialog:", e)

        time.sleep(5)  # Wait for 30 seconds (you can adjust this time as needed)

    # Switch back to the original tab (first tab)
    driver.switch_to.window(driver.window_handles[0])
# Print updated URLs
print("\nUpdated URLs:")
"""for job in job_titles:
    print(f"Job Title: {job['text']}, Updated Href: {job['href']}, Budget: ${job['budget']:.2f}")"""
# Close the WebDriver
'''for element_value in elements_values :
    print("""project :"""
          + element_value + """
          -------------------------------------------------------------------------------\n""")'''
for cover in covers :
    print(cover)
driver.quit()


