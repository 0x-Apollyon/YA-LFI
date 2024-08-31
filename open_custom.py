import chardet

def open_custom(file_path, mode='r', encoding=None, **kwargs):
	if 'b' in mode:
		return open(file_path, mode, **kwargs)
	if encoding is None:
		with open(file_path, 'rb') as f:
			raw_data = f.read(4096)
			result = chardet.detect(raw_data)
			encoding = result['encoding']
		if encoding == 'ascii': # avoid encoding problems
			encoding = 'utf-8'
	return open(file_path, mode, encoding=encoding, **kwargs)

# by azuk4r