from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

import asyncio
from icecream import ic

def init_scrapper() -> webdriver.Chrome:
    frontlines_url: str = "https://www.eveonline.com/frontlines/gallente"
    scrapper_options = Options()
    scrapper_options.add_argument("--headless")
    scrapper_options.add_argument("--no-sandbox")
    scrapper_options.add_argument("--disable-dev-shm-usage")
    chrome_prefs = {}
    scrapper_options.experimental_options["prefs"] = chrome_prefs
    chrome_prefs["profile.default_content_settings"] = {"images": 2}
    driver = webdriver.Chrome(options=scrapper_options)
    driver.get(frontlines_url)
    return driver
    

def scroll_to_load_page(driver: webdriver.Chrome):
    max_scroll_attempts = 10
    scroll_attempt = 0
    loaded = None

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
    return loaded

async def scrapper_get_specific_system_adv(system_id: int) -> int:
    driver = init_scrapper()
    system_adv = 0

    # Scroll down to make the element appear
    loaded = scroll_to_load_page(driver)
    if loaded is not None:
        solarsystem_elements = driver.find_element(By.XPATH, f"//*[starts-with(@id, 'solarsystem-{system_id}')]")
        adv_node = solarsystem_elements.find_element(By.XPATH, ".//*[starts-with(@class, 'mantine-Text-root')]")
        system_adv = int(adv_node.text.removesuffix("%"))
        if adv_node.get_attribute("class").find("2kmlov") != -1:
            system_adv *= -1

    driver.quit
    return system_adv

async def scrapper_get_all_systems_adv() -> list[dict]:
    driver = init_scrapper()
    results: list[dict] = []

    # Scroll down to make the element appear
    loaded = scroll_to_load_page(driver)
    if loaded is not None:
        solarsystem_elements = driver.find_elements(By.XPATH, "//*[starts-with(@id, 'solarsystem')]")
        for system in solarsystem_elements:
            system_id = system.get_attribute("id").removeprefix("solarsystem-")
            adv_node = system.find_element(By.XPATH, ".//*[starts-with(@class, 'mantine-Text-root')]")
            system_adv = int(adv_node.text.removesuffix("%"))
            if adv_node.get_attribute("class").find("2kmlov") != -1:
                system_adv *= -1
            system_results = {"id" : int(system_id),
                              "adv" : int(system_adv)}
            results.append(system_results)        
    
    driver.quit
    return results

async def main():
    results = await scrapper_get_all_systems_adv()
    ic (results)

if __name__ == "__main__":
    asyncio.run(main())