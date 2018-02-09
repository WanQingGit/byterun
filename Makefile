extract_comp_urltools:
	python3 -m byterun subjects/urltools.py "https://www.hello.world#fragment?q1=1"

extract_json:
	python3 -m byterun subjects/microjson.py "{\"a\":[1,2,3]}" 2>/dev/null
	
extract_naya:
	python3 -m byterun subjects/nayajson.py "qiaup98bsdf" 2>/dev/null

extract_url:
	python3 -m byterun subjects/urlparser.py "http://asd/q?w=e#test" 2>/dev/null
	
extract_cgi:
	python3 -m byterun subjects/cgi.py "A+%12B" 2>/dev/null