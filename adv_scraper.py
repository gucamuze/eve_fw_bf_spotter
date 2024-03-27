from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from icecream import ic

def scrapper_get_adv():
    frontlines_url = "https://www.eveonline.com/frontlines/gallente"
    scrapper_options = Options()
    scrapper_options.add_argument("--headless")
    driver = webdriver.Chrome(options=scrapper_options)
    # driver = webdriver.Chrome()
    driver.get(frontlines_url)
    # Maximum number of scroll attempts
    max_scroll_attempts = 10
    scroll_attempt = 0
    loaded = None
    results: list[dict] = []

    # Scroll down to make the element appear
    while scroll_attempt < max_scroll_attempts:
        try:
            # Check if the element with class containing "frontlines-main-container" is present
            loaded = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[class*="frontlines-map-container"]'))
            )
            # If element is found, break out of the loop
            break
        except:
            # If element is not found, scroll down and increment scroll_attempt
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            scroll_attempt += 1
    if loaded is not None:
        solarsystem_elements = driver.find_elements(By.XPATH, "//*[starts-with(@id, 'solarsystem')]")
        for system in solarsystem_elements:
            system_id = system.get_attribute("id").removeprefix("solarsystem-")
            system_adv = system.find_element(By.XPATH, ".//*[starts-with(@class, 'mantine-Text-root')]").text.removesuffix("%")
            system_results = {"system_id" : system_id,
                              "system_adv" : system_adv}
            results.append(system_results)        
    
    driver.quit
    return results

if __name__ == "__main__":
    results = scrapper_get_adv()
    ic (results)
