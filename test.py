import requests
import time
import datetime
import json

request_max_retries = 5
request_retry_delay = 1
main_api_url = "https://esi.evetech.net"
systems_route = "/latest/fw/systems/"
systems_route_params = "?datasource=tranquility"
systems_name_route = "/latest/universe/systems/"

def fetch_request_json(request_url):
	for attempt in range(request_max_retries):
		try:
			response = requests.get(request_url)
			if response.status_code == 200:
				return response.json()
			else:
				print(f"Error: API request failed with status code {response.status_code}")
				
			print(f"Retry attempt {attempt + 1}/{request_max_retries} in {request_retry_delay} seconds...")
			time.sleep(request_retry_delay)

		except requests.RequestException as e:
			print(f"Error: Failed to make API request - {e}")
			print(f"Retry attempt {attempt + 1}/{request_max_retries} in {request_retry_delay} seconds...")
			time.sleep(request_retry_delay)
	return None

req = requests.get(main_api_url+systems_route+systems_route_params)
print(req.headers['Date'])

test = []
with open("cmp_data.json", "r") as file:
    test = json.load(file)
print(test)