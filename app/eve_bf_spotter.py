import time
import datetime
import json
import os
import httpx
from dotenv import load_dotenv
from adv_scraper import scrapper_get_all_systems_adv

load_dotenv()

# requests and misc params
request_max_retries = 5
request_retry_delay = 1
galcal_id = [500004, 500001] #galmilfirst
header_info = f"Galmil Discord Bot Beta / Contact: {os.getenv('MAIL')}"
main_api_url = "https://esi.evetech.net"
systems_route = "/latest/fw/systems/"
systems_route_params = "?datasource=tranquility"
systems_name_route = "/latest/universe/systems/"
systems_name_params = "/?datasource=tranquility&language=en" #needs / because system id goes in first
results_log_filename = "log.json"
save_log_filaname = "cmp_data.json"

# less error-prone get request, catches exceptions. returns the json
async def fetch_request(request_url: str) -> httpx.Response | None:
    for attempt in range(request_max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(request_url, headers={"User-Agent": header_info})
                if response.status_code == 200:
                    return response
                else:
                    print(f"Error: API request failed with status code {response.status_code}")
     
        except httpx.HTTPError as e:
            print(f"Error: Failed to make API request - {e}")
            print(f"Retry attempt {attempt + 1}/{request_max_retries} in {request_retry_delay} seconds...")
            time.sleep(request_retry_delay)
    return None

def get_system_adv(system_id: int, systems_adv: list[dict]) -> int:
    for system in systems_adv:
        if system["id"] == system_id:
            return system["adv"]

def get_system_adv(system_id: int, systems_adv: list[dict]) -> int:
    for system in systems_adv:
        if system["id"] == system_id:
            return system["adv"]

# get all galcal systems relevant infos: name, system id, faction id and victory points
async def get_systems_infos(galcal_systems: list, systems_adv: list[dict]) -> list[dict]:
	systems_infos = []
	for system in galcal_systems:
		system_id: int = int(system['solar_system_id'])
		system_info = await fetch_request(main_api_url+systems_name_route+str(system_id)+systems_name_params)
		system_info = system_info.json()
		system_adv = get_system_adv(system_id, systems_adv)
		systems_infos.append({
			"name" : system_info['name'],
			"id" : system_id,
			"occupier_faction_id" : system["occupier_faction_id"],
			"victory_points" : system['victory_points'],
   			"adv" : system_adv})
	return systems_infos

# values are arbitrary and subject to change. <10000 check to avoid false positives due to system flipping
def is_potential_bf(vp_diff_abs: int) -> bool:
    return vp_diff_abs > 1500 and vp_diff_abs < 10000

# return potential bf status, stating system name, if the bf is offensive or defensive, won or lost, and time
def get_bf_status(system: dict, galcal_id: int, diff: int) -> dict[str, str, str, float]:
	faction_id = system['occupier_faction_id']
	battle_type = "Defensive" if faction_id == galcal_id[0] else "Offensive"
	if faction_id == galcal_id[0]:
		outcome = "won" if diff < 0 else "lost"
	else:
		outcome = "won" if diff > 0 else "lost"
	return {"system_name" : system['name'],
			"bf_type" : battle_type,
   			"outcome" : outcome,
      		"system_vp_percent" : 0.0,
        	"system_adv" : system['adv']}
 
# Takes a RFC compliant string as given by the ESI, and returns true if time given in string is past due
# TODO: This is complicated garbage that needs refactoring
def task_must_run(next_task_run_time: str) -> bool:
	if not next_task_run_time:
		return True
	gmt_offset = datetime.timezone(datetime.timedelta(hours=0))  # GMT timezone offset is 0 hours
	target_time_gmt = datetime.datetime.strptime(next_task_run_time, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=gmt_offset)
	# Convert GMT time to UTC
	target_time_utc = target_time_gmt.astimezone(datetime.timezone.utc)
	# Get the current UTC time
	current_time_utc = datetime.datetime.now(datetime.timezone.utc)
	# Calculate the time difference between the current UTC time and the target time
	time_difference = (target_time_utc - current_time_utc).total_seconds()
 
	return time_difference < 0

def get_cmp_index(systems_infos_cmp: list, id: int) -> int:
    for index, system in enumerate(systems_infos_cmp):
        if system['id'] == id:
            return index

# returns a list with [0]->next call schedule, [2]->vp changes (temporary), [1]->potential bf completions, or None if API is unreachable
async def bf_spotter_get_bf_completion() -> list[str, dict, None] | None :
	systems_infos_cmp = []
	TMP_all_systems_vp_changes = ""
	results = []
	# opens the save file if it exists and creates the data from it
	if os.path.exists(save_log_filaname):
		with (open(save_log_filaname, "r")) as file:
			systems_infos_cmp = json.load(file)
			print("Populated compare list via save file")

	galcal_systems = []
	# list of all fw systems in json
	fw_request_response = await fetch_request(main_api_url+systems_route+systems_route_params)
	# only continue if response is there, if its None, API might be unreachable
	if fw_request_response is not None:
		all_fw_systems = fw_request_response.json()
  
		# keep only gallente/caldari fw systems
		for system in all_fw_systems:
			if system['occupier_faction_id'] in galcal_id:
				galcal_systems.append(system)
    
		systems_adv = await scrapper_get_all_systems_adv()
		# create dict of systems with name id faction id and vp
		systems_infos = await get_systems_infos(galcal_systems, systems_adv)

		if not systems_infos_cmp:
			print("Populating compare list")
			systems_infos_cmp = systems_infos
		else:
			# timestamp default is none, will be set if there is at least one vp change
			timestamp = None
			# compares the vp of new and old all_fw_systems
			for system in systems_infos:
				cmp_index = get_cmp_index(systems_infos_cmp, system['id'])
				system_vp = system['victory_points']
				system_vp_cmp = systems_infos_cmp[cmp_index]['victory_points']
				system_adv = system['adv']
				system_adv_cmp = systems_infos_cmp[cmp_index]['adv']
				# vp change detected: print and log in file all the changes
				#TODO: change heuristics
				if system_vp != system_vp_cmp:
					diff = system_vp - system_vp_cmp
					timestamp = fw_request_response.headers['Date']
					# output part, first to CLI then file
					system_header = f"{timestamp}: {system['name']} ({str(system['id'])})\n"
					vp_percent_old = system_vp_cmp * 100 / 75000
					vp_percent_new = system_vp * 100 / 75000
					vp_percent_change = vp_percent_new - vp_percent_old
					vp_change = f"\tVictory points change: {str(diff)} ({vp_percent_change:.2f}% change)\n"
					adv_change = f"\tAdvantage change: {str(system_adv - system_adv_cmp)}%\n"
					system_changes = system_header + vp_change + adv_change
					print(system_changes)
					TMP_all_systems_vp_changes += system_changes
					# battlefield spotting
					if is_potential_bf(abs(diff)):
						bf_status = get_bf_status(system, galcal_id, diff)
						bf_status['system_vp_percent'] = vp_percent_new
						results.append(bf_status)
						print(bf_status)
						with open("bf_log.json", "a") as file:
							file.write(f"{bf_status}\n{system_changes}\n")
					with open(results_log_filename, "a") as file:
						file.write(f"{system_changes}")
					# update the system cmp list
					systems_infos_cmp[cmp_index] = system
			# add spaces for next log
			if timestamp is not None:
				with open(results_log_filename, "a") as file:
					file.write("\n\n")
	
		with open(save_log_filaname, "w") as file:
			json.dump(systems_infos_cmp, file)
		print("bf_spotter done")
		return [fw_request_response.headers['Expires'], results, TMP_all_systems_vp_changes]

	return None
