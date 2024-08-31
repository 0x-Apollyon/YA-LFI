import os
import time
import subprocess
import socket
import shutil
from stem import Signal
from stem.control import Controller

def start_tor_service():
	try:
		subprocess.call(['sudo', 'service', 'tor', 'start'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		print("[*] TOR SERVICE STARTED")
	except Exception as e:
		print(f"[X] Failed to start Tor service: {str(e)}")

def clean_up(tor_base_port=9050, tor_control_base_port=9151, total_instances=5, tor_data_dir="/tmp/tor_profiles"):
	try:
		subprocess.call(['killall', 'tor'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		time.sleep(1)
		for port in range(tor_base_port, tor_base_port + total_instances * 10, 10):
			if is_port_open(port):
				os.system(f"fuser -k {port}/tcp")
			if is_port_open(port + 101):
				os.system(f"fuser -k {port + 101}/tcp")
		if os.path.exists(tor_data_dir):
			shutil.rmtree(tor_data_dir)
		time.sleep(3)
	except Exception as e:
		print(f"[X] Failed during cleanup: {str(e)}")

def is_port_open(port):
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
		result = sock.connect_ex(('127.0.0.1', port))
		return result == 0

def create_tor_instance(thread_num, tor_base_port=9050, tor_control_base_port=9151, tor_data_dir="/tmp/tor_profiles"):
	while True:
		instance_dir = f"{tor_data_dir}/tor_profile_{thread_num}"
		os.makedirs(instance_dir, exist_ok=True)
		torrc_content = f"""
		SocksPort {tor_base_port + thread_num * 10}
		ControlPort {tor_control_base_port + thread_num * 10}
		DataDirectory {instance_dir}
		"""
		torrc_path = f"{instance_dir}/torrc"
		with open(torrc_path, 'w') as torrc_file:
			torrc_file.write(torrc_content)
		try:
			subprocess.Popen(['/usr/bin/tor', '-f', torrc_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			time.sleep(5)
			with Controller.from_port(port=tor_control_base_port + thread_num * 10) as controller:
				controller.authenticate()
				break
		except Exception as e:
			print(f"[X] Thread {thread_num} | Failed to start Tor instance: {str(e)}")
			thread_num += 1
			continue

def rotate_tor_ip(thread_num, tor_control_base_port=9151):
	try:
		with Controller.from_port(port=tor_control_base_port + thread_num * 10) as controller:
			controller.authenticate()
			controller.signal(Signal.NEWNYM)
		ip_address = get_ip(thread_num)
		print(f"[?] Thread {thread_num} | IP assigned: {ip_address}")
	except Exception as e:
		print(f"[X] Thread {thread_num} | Failed to rotate Tor IP: {str(e)}")
		raise Exception(f"[X] Thread {thread_num}: Failed to rotate Tor IP: {e}")

def get_ip(thread_num, tor_base_port=9050):
	proxies = {
		'http': f'socks5://127.0.0.1:{tor_base_port + thread_num * 10}',
		'https': f'socks5://127.0.0.1:{tor_base_port + thread_num * 10}'
	}
	try:
		ip_address = requests.get('https://checkip.amazonaws.com/', proxies=proxies).text.strip()
		return ip_address
	except Exception as e:
		print(f"[X] Failed to retrieve Tor IP: {str(e)}")
		return "Unknown"

def configure_proxies_for_thread(thread_num, tor_base_port=9050):
	return {
		'http': f'socks5://127.0.0.1:{tor_base_port + thread_num * 10}',
		'https': f'socks5://127.0.0.1:{tor_base_port + thread_num * 10}'
	}

# by azuk4r
