import requests
import sys
import time
import datetime
import json
import os
from dotenv import load_dotenv

load_dotenv()

# requests and misc params
request_max_retries = 5
request_retry_delay = 1
galcal_id = [500004, 500001] #galmilfirst
header_info = f"Galmil Discord Bot Prototype/ WIP/ Contact: {os.getenv('MAIL')}"
main_api_url = "https://esi.evetech.net"
systems_route = "/latest/fw/systems/"
systems_route_params = "?datasource=tranquility"
systems_name_route = "/latest/universe/systems/"
systems_name_params = "/?datasource=tranquility&language=en" #needs / because system id goes in first
results_log_filename = "log.json"
save_log_filaname = "cmp_data.json"

# less error-prone get request, catches exceptions. returns the json
def fetch_request(request_url):
	for attempt in range(request_max_retries):
		try:
			response = requests.get(request_url, headers={"User-Agent": header_info})
			if response.status_code == 200:
				return response
			else:
				print(f"Error: API request failed with status code {response.status_code}")
				
			print(f"Retry attempt {attempt + 1}/{request_max_retries} in {request_retry_delay} seconds...")
			time.sleep(request_retry_delay)

		except requests.RequestException as e:
			print(f"Error: Failed to make API request - {e}")
			print(f"Retry attempt {attempt + 1}/{request_max_retries} in {request_retry_delay} seconds...")
			time.sleep(request_retry_delay)
	return None

# get all galcal systems relevant infos: name, system id, faction id and victory points
def get_systems_infos(galcal_systems) -> list:
	systems_infos = []
	for system in galcal_systems:
		system_id = system['solar_system_id']
		system_info = fetch_request(main_api_url+systems_name_route+str(system_id)+systems_name_params).json()
		systems_infos.append({
			"name" : system_info['name'],
			"id" : system_id,
			"occupier_faction_id" : system["occupier_faction_id"],
			"victory_points" : system['victory_points']})
	return systems_infos

# values are arbitrary and subject to change. <10000 check to avoid false positives due to system flipping
def is_potential_bf(vp_diff_abs) -> bool:
    return vp_diff_abs > 1500 and vp_diff_abs < 10000

# return potential bf status, stating system name, if the bf is offensive or defensive, won or lost, and time
def get_bf_status(system, galcal_id, diff, formatted_date_time) -> str:
	faction_id = system['occupier_faction_id']
	battle_type = "Defensive" if faction_id == galcal_id[0] else "Offensive"
	if faction_id == galcal_id[0]:
		outcome = "won" if diff < 0 else "lost"
	else:
		outcome = "won" if diff > 0 else "lost"
	return f"{system['name']}: Potential {battle_type} battlefield {outcome} detected ({formatted_date_time})"

#thanks chatgpt i hate time shaeningans
def sleep_until_next_esi_call(next_esi_call_time):
	gmt_offset = datetime.timezone(datetime.timedelta(hours=0))  # GMT timezone offset is 0 hours
	target_time_gmt = datetime.datetime.strptime(next_esi_call_time, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=gmt_offset)
	# Convert GMT time to UTC
	target_time_utc = target_time_gmt.astimezone(datetime.timezone.utc)
	# Get the current UTC time
	current_time_utc = datetime.datetime.now(datetime.timezone.utc)
	# Calculate the time difference between the current UTC time and the target time
	time_difference = target_time_utc - current_time_utc
	# Convert the time difference to seconds
	sleep_duration = time_difference.total_seconds() + 60
	print(f"Fetching done, sleeping for {sleep_duration} seconds until {target_time_utc} + 60seconds")
	time.sleep(sleep_duration)
	# time.sleep(10)


def main():
	systems_infos_cmp = []
	# opens the save file if it exists and creates the data from it
	if os.path.exists(save_log_filaname):
		with (open(save_log_filaname, "r")) as file:
			systems_infos_cmp = json.load(file)
			print("Populated compare list via save file")
	# main loop, once every minute
	while 1:
		galcal_systems = []
		# list of all fw systems in json
		fw_request_response = fetch_request(main_api_url+systems_route+systems_route_params)
		# only continue if response is there, if its None, API might be unreachable
		if fw_request_response is not None:
			all_fw_systems = fw_request_response.json()

			# keep only gallente/caldari fw systems
			for system in all_fw_systems:
				if system['occupier_faction_id'] in galcal_id:
					galcal_systems.append(system)

			# create dict of systems with name id faction id and vp
			systems_infos = get_systems_infos(galcal_systems)

			if not systems_infos_cmp:
				print("Populating compare list")
				systems_infos_cmp = systems_infos
			else:
				# timestamp default is none, will be set if there is at least one vp change
				timestamp = None
				# compares the vp of new and old all_fw_systems
				for index, system in enumerate(systems_infos):
					system_vp = system['victory_points']
					system_vp_cmp = systems_infos_cmp[index]['victory_points']
					# vp change detected: print and log in file all the changes
					if system_vp != system_vp_cmp:
						timestamp = fw_request_response.headers['Date']
						diff = system_vp - system_vp_cmp
						if is_potential_bf(abs(diff)):
							bf_status = get_bf_status(system, galcal_id, diff, timestamp)
							print(bf_status)
							with open(results_log_filename, "a") as file:
								file.write(bf_status)
						# output part, first to CLI then file
						system_header = f"{timestamp}: {system['name']} ({system['id']})\n"
						vp_percent_old = system_vp_cmp * 100 / 75000
						vp_percent_new = system_vp * 100 / 75000
						vp_percent_change = vp_percent_new - vp_percent_old
						vp_change = f"\tVictory points change: {str(diff)} ({vp_percent_change:.2f}% change)"
						system_vp_change_infos = system_header + vp_change
						print(system_vp_change_infos)
						with open(results_log_filename, "a") as file:
							file.write(f"{system_vp_change_infos}\n")
						# update the system cmp list
						systems_infos_cmp[index] = system
				# add spaces for next log
				if timestamp is not None:
					with open(results_log_filename, "a") as file:
						file.write("\n\n")
		
			with open(save_log_filaname, "w") as file:
				json.dump(systems_infos_cmp, file)

			sleep_until_next_esi_call(fw_request_response.headers['Expires'])

	
if __name__ == '__main__':
	sys.exit(main())