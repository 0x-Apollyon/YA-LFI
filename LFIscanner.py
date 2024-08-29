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
                                   

Made by: Apollyon 
Based on: LFIScanner by R3LI4NT                       
""")
parse = argparse.ArgumentParser()
parse.add_argument('-u','--url',help="Target URL",required=False)
parse.add_argument('-ulist','--url_list',help="Target multiple URLs from a file",required=False)
parse.add_argument('-e','--extract',help="Extract content", action='store_true',required=False)
parse.add_argument('-p','--payload',help="Payloads file [Pre installed lists: all_os.txt , linux.txt , windows.txt]",required=True)
parse.add_argument('-t','--threads',help="Threads [5 by default]",default=5,required=False)
parse.add_argument('-pr','--proxy',help="Add a list of proxies to use [HTTP, HTTPS, SOCKS]",required=False)
parse.add_argument('-auth','--authentication',help="Load headers and/or cookies from a file to run a scan while authenticated",required=False,default="auth.json")
parse.add_argument('-save','--save_to_file',help="Save working LFI payloads by writing them to a file",required=False,default="LFI_scanner_saves.txt")
parse = parse.parse_args()

lock = Lock()


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

def check_single_url_with_payload(x,payloads_per_thread,payload_path,target_url,cookies,headers):
	global proxies_but_dict
	global proxy_running
	payloads = load_internal_payloads(payload_path)
	
	payload_count = 0
	pointer_line = 0
	print(f"Thread number {x+1} launched on URL {target_url} Checking payloads ...")
	last_msg_was_error = False
	for p in payloads:
		try:
			if pointer_line > (x*payloads_per_thread) and pointer_line < ((x+1)*payloads_per_thread): 
				p = p.strip()

				if parse.proxy:
					if proxy_running:
						query = requests.get(target_url+p , headers=headers , proxies=random.choice(proxies_but_dict), cookies=cookies)
					else:
						query = requests.get(target_url+p , headers=headers, cookies=cookies)
				else:
					query = requests.get(target_url+p , headers=headers, cookies=cookies)

				payload_count = payload_count + 1
				if payload_count%25 == 0:
					print(f"[!] Thread {x+1} | Running on URL: {target_url} | Status: Checked {payload_count} payloads...")
				if "root" and "bash" and r"/bin" in query.text and query.status_code//100 == 2:
					print("="*10)
					print(f"LFI DETECTED:\n URL + Payload: {target_url+p}\n\n")
					if parse.extract:
						e = BeautifulSoup(query.text,'html5lib')
						print(e.blockquote.text)
					if parse.save_to_file:
						save_file_path = parse.save_to_file
						if os.path.isfile(save_file_path):
							lock.acquire()
							with open(save_file_path , "a") as save_file:
								save_file.write(target_url+p)
								save_file.write("\n")
							lock.release()
						else:
							lock.acquire()
							with open(save_file_path , "w") as save_file:
								save_file.write(target_url+p)
								save_file.write("\n")
							lock.release()
						print(f"LFI DETECTED: Saved to save file \n")
					print("="*10)
			pointer_line = pointer_line + 1
			last_msg_was_error = False
		except RequestException:
			if not last_msg_was_error:
				print(f"[!] Thread {x+1} | Running on URL: {target_url} | Status: Error occured while making request")
				print(f"[!] Thread {x+1} | Running on URL: {target_url} | Status:  Sleeping for 3 seconds then retrying payloads untill error is resolved ...")
				last_msg_was_error = True
				time.sleep(3)
			else:
				time.sleep(3)
		except NameResolutionError:
			if not last_msg_was_error:
				print(f"[!] Thread {x+1} | Running on URL: {target_url} | Status:  Error occured while resolving domain name. Are you sure the specified website exists and you are connected to the internet ?")
				print(f"[!] Thread {x+1} | Running on URL: {target_url} | Status:  Sleeping for 3 seconds then retrying payloads untill error is resolved ...")
				last_msg_was_error = True
				time.sleep(3)
			else:
				time.sleep(3)

def use_payload(x,payloads_per_thread,payload_path,target_url,targets_path,cookies,headers):
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
						check_single_url_with_payload(x,payloads_per_thread,payload_path,target,cookies,headers)
		else:
			print("[X] NO TARGET URL SPECIFIED")
			quit()
	else:
		check_single_url_with_payload(x,payloads_per_thread,payload_path,target_url,cookies,headers)

selected_payload_file = parse.payload.lower()

match selected_payload_file:
    case "all_os" | "all_os.txt" | "allos" | "allos.txt":
        print("[*] USING PAYLOADS FOR ALL OS SERVERS")
        payload_path = "all_os.txt"
        payload_count = payload_counter(payload_path)
    case "linux" | "linux.txt":
        print("[*] USING PAYLOADS FOR LINUX SERVERS")
        payload_path = "linux.txt"
        payload_count = payload_counter(payload_path)
    case "windows" | "windows.txt":
        print("[*] USING PAYLOADS FOR WINDOWS SERVERS")
        payload_path = "windows.txt"
        payload_count = payload_counter(payload_path)
    case _:
        if os.path.isfile(selected_payload_file):
            payload_path = selected_payload_file
        else:
            print("[X] SPECIFIED PAYLOAD FILE NOT FOUND")
            quit()

global proxies_but_dict
global proxy_running

if parse.proxy:
	proxy_running = True
	proxy_path = parse.proxy
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

headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0',
		"Accept-Language": "en-US,en;q=0.6",
		"Accept-Encoding": "gzip, deflate, br, zstd"
    }
cookies = {}
#default headers

if parse.authentication:
	auth_path = parse.authentication
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



if parse.url:
	print(f"[*] RUNNING ON TARGET ---> {parse.url}")
	if r"https://" in parse.url or r"http://" in parse.url:
		current_target = parse.url
	else:
		current_target = r"https://" + parse.url

	payloads_per_thread = payload_count//int(parse.threads)

	for x in range(int(parse.threads)):
		threading.Thread(target=use_payload, args=(x,payloads_per_thread,payload_path,current_target,False,cookies,headers)).start()	
else:
	print(f"[*] RUNNING ON MULTIPLE TARGETS")
	url_list_path = parse.url_list.lower()
	if url_list_path:
		if os.path.isfile(url_list_path):
			payloads_per_thread = payload_count//int(parse.threads)

			for x in range(int(parse.threads)):
				threading.Thread(target=use_payload, args=(x,payloads_per_thread,payload_path,False,url_list_path,cookies,headers)).start()	
		else:
			print("[X] GIVEN TARGET URL FILE NOT FOUND")	
	else:
		print("[X] NO TARGET URL SPECIFIED")
		quit()
