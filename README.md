<pre>
▄██   ▄      ▄████████           ▄█          ▄████████  ▄█  
███   ██▄   ███    ███          ███         ███    ███ ███  
███▄▄▄███   ███    ███          ███         ███    █▀  ███▌ 
▀▀▀▀▀▀███   ███    ███  ██████  ███        ▄███▄▄▄     ███▌ 
▄██   ███ ▀███████████  ██████  ███       ▀▀███▀▀▀     ███▌ 
███   ███   ███    ███          ███         ███        ███  
███   ███   ███    ███          ███▌    ▄   ███        ███  
 ▀█████▀    ███    █▀           █████▄▄██   ███        █▀   </pre>
                                
### Yet another - local file inclusion scanner
##### By: Apollyon
##### Based on: LFIScanner by R3LI4NT  

## Commands

| COMMAND | DESCRIPTION |
| ------------- | ------------- |
| -h / --help | Request help |
| -u / --url | Target Website |
| -ulist / --url_list | Target multiple websites from file |
| -wiz / --wizard | Wizard for new users |
| -p / --payload | Payload file |
| -e / --extract | Extract content |
| -t / --threads | Multi threaded scanning |
| -pr / --proxy | Using proxies (HTTP, HTTPS, SOCKS) |
| -tr / --tor | Use Tor for connections with separate instances per thread |
| -rotate / --tor-rotation | Rotate Tor IP after N requests (requires --tor and int) |
| -auth / --authentication | Authentication using headers and/or cookies |
| -save / --save_to_file | Saves valid payloads to file on disk |

## Installation
Normal
```
git clone https://github.com/0x-Apollyon/YA-LFI.git
cd YA-LFI
pip install -r requirements.txt
```
Using virtual environment (Arch based linux distros)
```
git clone https://github.com/0x-Apollyon/YA-LFI.git
cd YA-LFI
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

You can run it using commands given below or use the wizard

View help
```
python LFIscanner.py -h
```
Default usage
```
python LFIscanner.py -u https://example.com?param= -p all_os.txt
```
Using with wizard
```
python LFIscanner.py -wiz
```
Linux wordlist
```
python LFIscanner.py -u https://example.com?param= -p linux.txt 
```
Windows wordlist
```
python LFIscanner.py -u https://example.com?param= -p windows.txt
```
WARNING: DO NOT RUN WITHOUT A PARAMETER IN THE URL

![image](https://github.com/user-attachments/assets/4e07bcd8-21a2-43e4-8551-8006460f8ce7) <br>
![image](https://github.com/user-attachments/assets/be6ae5a0-376b-4a95-899b-3f4d47c933fd)



## Other amazing third party wordlists

[Linux wordlist](https://github.com/carlospolop/Auto_Wordlists/blob/main/wordlists/file_inclusion_linux.txt) <br>
[Windows wordlist](https://github.com/carlospolop/Auto_Wordlists/blob/main/wordlists/file_inclusion_windows.txt)

## Most common parameters

```
?cat={payload}
?dir={payload}
?action={payload}
?board={payload}
?date={payload}
?detail={payload}
?file={payload}
?download={payload}
?path={payload}
?folder={payload}
?prefix={payload}
?include={payload}
?page={payload}
?inc={payload}
?locate={payload}
?show={payload}
?doc={payload}
?site={payload}
?type={payload}
?view={payload}
?content={payload}
?document={payload}
?layout={payload}
?mod={payload}
?conf={payload}
```
[Source](https://book.hacktricks.xyz/pentesting-web/file-inclusion)
