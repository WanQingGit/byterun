extract_comp_urltools:
	python3 -m byterun subjects/urltools.py "https://www.hello.world#fragment?q1=1"

extract_json:
	python3 -m byterun subjects/microjson.py "qiaup98bsdf" 2>/dev/null
	
extract_naya:
	python3 -m byterun subjects/nayajson.py "qiaup98bsdf" 2>/dev/null

extract_url:
	python3 -m byterun subjects/urlparser.py "qiaup98bsdf" 2>/dev/null
	
extract_time:
	python3 -m byterun subjects/timeparse.py "qiaup98bsdf" 2>/dev/null