from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import time, sys, requests
from io import BytesIO
from PIL import Image
from csv import writer


# initialize test folder
test_folder = 'C:\\dev\\selenium_test\\'

# logger initialize
ts = time.localtime()
logfile = 'Results' + time.strftime('%Y%m%d_%H%M%S', ts) + '.csv'
csv_logger = open(test_folder + logfile, 'w', newline='')
csv_writer = writer(csv_logger)
# write header for the logger
csv_writer.writerow(['TIMESTAMP', 'RESULT', 'STEP DETAILS'])
csv_logger.close()

# function to write logs of the test
def write_log(result, step_detail):
	csv_logger = open(test_folder + logfile, 'a', newline='')
	csv_writer = writer(csv_logger)
	csv_writer.writerow([time.strftime('%Y%m%d_%H%M%S', ts), result, step_detail])
	csv_logger.close()

# function to initialize a driver Chrome
# returns the webdriver object
def init_driver():
	# adding options to remove annoying pop up when chrome is opened via selenium
	options = webdriver.ChromeOptions()
	options.add_argument('--ignore-certificate-errors')
	options.add_argument("--test-type")
	options.add_argument('--disable-extensions')
	options.add_argument('--start-maximized')
	options.add_argument('disable-infobars')
	options.add_argument('--headless')
	options.add_experimental_option('useAutomationExtension', False)
	driver = webdriver.Chrome(options=options)
	driver.implicitly_wait(20)
	return driver

# function to close the driver
def close_driver(driver):
	driver.close()
	return

# start
if __name__ == '__main__':

	# start a driver for a web browser:
	driver = init_driver()

	# 1. Open the page https://en.wikipedia.org/wiki/Selenium
	driver.get('https://en.wikipedia.org/wiki/Selenium')
	# verify page load
	try:
		driver.find_element_by_css_selector('#firstHeading')
	except NoSuchElementException:
		write_log('FAIL', 'Wikipedia page load fail. Exiting ...')
		close_driver(driver)
		sys.exit()
	else:
		write_log('PASS', 'Wikipedia page load success.')


	# 2. Verify that the external links in "External links" section work
	# get locator of external section
	list_links = driver.find_elements_by_xpath('//span[@id="External_links"]//parent::h2//following-sibling::ul//'
																						'a[@class="external text"]')
	write_log(len(list_links))
	# loop each link for a response
	for link in list_links:
		# send a request
		r = requests.get(link.get_attribute('href'))
		if r.status_code != 404:
			# link working
			write_log('PASS', 'Link ' + link.text + ' working')
		else:
			# link not working
			write_log('PASS', 'Link ' + link.text + ' not working')


	# 3. Click on the "Oxygen" link on the Periodic table at the bottom of the page
	# loop for rows
	rows = driver.find_elements_by_xpath('//table[@aria-describedby="periodic-table-legend"]//tbody/tr')
	element_to_search = "Oxygen"
	for i in range(2, len(rows)):
		cols = driver.find_elements_by_xpath('//table[@aria-describedby="periodic-table-legend"]//tbody/tr[{}]/td'.format(i))
		for j in range(1, len(cols)):
			# get element object
			element_obj = driver.find_element_by_xpath('//table[@aria-describedby="periodic-table-legend"]//tbody/tr[{}]/td[{}]'.format(i, j))
			# look for oxygen
			if element_to_search in element_obj.get_attribute('title'):
				element_obj.click()
				break
		else:
			continue
		break
	# verify error
	if driver.find_element_by_css_selector('#firstHeading').text == element_to_search:
		write_log('PASS', 'Element ' + element_to_search + ' located and clicked.')
	else:
		write_log('FAIL', 'Element ' + element_to_search + ' page not loaded.')


	# 4. Verify that it is a "featured article"
	try:
		driver.find_element_by_css_selector('img[alt^="This is a featured article"]')
	except NoSuchElementException:
		write_log('FAIL', 'Not a featured article')
	else:
		write_log('PASS', 'This is a featured article')


	# 5. Take a screen shot of the right hand sidebar that lists its properties
	image_element = driver.find_element_by_css_selector('table[class="infobox"]>tbody')
	# get dimensions of the element to capture
	location = image_element.location
	size = image_element.size
	# get original size ppf the window
	original_size = driver.get_window_size()
	# use JS to get width
	required_width = driver.execute_script('return document.body.parentNode.scrollWidth')
	# use JS to get height
	required_height = driver.execute_script('return document.body.parentNode.scrollHeight')
	# set new dimensions
	driver.set_window_size(required_width, required_height)
	# take the screenshot
	png = driver.get_screenshot_as_png()
	# reset driver sizing
	driver.set_window_size(original_size['width'], original_size['height'])
	# open the buffered image using PIL
	im = Image.open(BytesIO(png))
	# set the coordinates
	left = location['x']
	top = location['y']
	right = location['x'] + size['width']
	bottom = location['y'] + size['height']
	# crop image
	im = im.crop((left, top, right, bottom))
	# save image
	im.save(test_folder + 'screenshot_properties.png')
	write_log('DONE', 'Saved image in test folder')


	# 6. Count the number of pdf links in "Citations" (I assumed this is references as there is no citations on the page)
	# get the references section
	element_references = driver.find_element_by_xpath('//span[@id="References"]//parent::h2//following-sibling::div[@class="reflist columns references-column-width"]')
	# count the number of PDFs in that section and log
	write_log('DONE', 'The number of PDFs in the references section are: ' + str(len(element_references.find_elements_by_xpath('//span[@ class ="cs1-format"]'))))


	# 7. In the search bar on top right enter "pluto" and verify that the 2nd suggestion is "Plutonium"
	# get the search box and enter string
	string_search = "pluto"
	driver.find_element_by_css_selector('#searchInput').send_keys(string_search)
	# wait for AJAX load of search results
	try:
		element = WebDriverWait(driver, 10).until(
			ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[class="suggestions-results"]'))
		)
		write_log('PASS', 'Search for string "' + string_search + '" success.')
		# validate that the 2nd suggestion is Plutonium
		second_suggestion = driver.find_element_by_xpath('//div[@class="suggestions-results"]/a[2]')
		search_suggestion = "Plutonium"
		if second_suggestion.text == search_suggestion:
			write_log('PASS', 'Second element in search suggestion is "' + search_suggestion + '"')
		else:
			write_log('FAIL', 'Second element in search suggestion is not "' + search_suggestion + '" but is: ' + second_suggestion.text)
	except NoSuchElementException:
		write_log('FAIL', 'Search for string "' + string_search + '" failed.')

	# close the driver:
	close_driver(driver)
