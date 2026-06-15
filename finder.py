import requests
import json

url = "https://pkvvcly41h.execute-api.us-east-1.amazonaws.com/snfapi-exim/company_profile/initiate_l0_contact"

payload = {
	"id": "129180",
	"token_id": "RVdvZUp6NHNtUmVleTdGd2hCTHBQem5xMzBiUmMzNG9tcC9hbW1ZWjdnVT0=",
	"master_id": "6045171",
	"level0_people_id": "147109",
	"level0_company_id": "2160057",
	"people_id": "610769e94776ac0001ca1950",
	"level0_company_relation_id": "219885"
}

headers = {
	'User-Agent': "Dart/3.12 (dart:io)",
	'Accept-Encoding': "gzip",
	'Content-Type': "application/json",
	'x-api-key': "X7WeW8Lp4M6orTTQLFS4i27GzhoPlD4099utjdI8",
	'authenticate': "eyJraWQiOiIxL3JENTZwOWlvSGpvZjFOOHVoQ3EvUkpiTUsrcy8zckJ2d1gxdFhMYWxrPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI3NGQ4MjRjOC1iMDUxLTcwNWUtYzY0My1mZDk0OTRiODkwZTAiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiaXNzIjoiaHR0cHM6Ly9jb2duaXRvLWlkcC51cy1lYXN0LTEuYW1hem9uYXdzLmNvbS91cy1lYXN0LTFfZWtXTUhaTFRFIiwiY29nbml0bzp1c2VybmFtZSI6Ijc0ZDgyNGM4LWIwNTEtNzA1ZS1jNjQzLWZkOTQ5NGI4OTBlMCIsIm9yaWdpbl9qdGkiOiIxNzQ4MWMwZi0wNDk0LTQ4NzQtOGUzYy0xMjVjZGQ0ZTI2OWMiLCJhdWQiOiIzNThhcDhsMWk3ZWhpbDA1Y3Axdjlsc3I1YiIsImV2ZW50X2lkIjoiZDJmYzI3MGEtYzBkNy00OTA1LTkzYTYtNmYzNmFlZTI2Y2RkIiwidG9rZW5fdXNlIjoiaWQiLCJhdXRoX3RpbWUiOjE3ODEyNjYwNTUsImV4cCI6MTc4MTM0Njg4MywiaWF0IjoxNzgxMzQzMjgzLCJqdGkiOiJkMDFhYjNiNS0wY2E5LTRhODUtYTQ0Ny1mYjA1NjdjMGY3OGIiLCJlbWFpbCI6IndlYkB0aGVkb2xsYXJidXNpbmVzcy5jb20ifQ.MWBZx_ZPGWXq_fjFYBzHGT85mTD7QCCVWx_8ntxkQc1KpKlJmhM05Pv8O3eWfV-1-rV_iVG_xJ23PLCCEzFiEm9VO95hYi324XVLisdi6oKKdoi7JIyjksTTyuZekVBpSsoqpQ8zvxH-1dz4qzxNqQShdxdXFd3JbMZXNS5kx1EqAke0uk4GphHB17NwnHvdTXwAT8zktnMGxjO3KcIIuIdGv4Qp8TnPGAgCGZjnV434zuG0NtJn_0AOEf5CkXeQG4Sww1SSOlB-Z595XXZBH37l54lAuunnbsDv2FWV5gfmIejjU87YTc8lasvHdpRK6vKY72UYxryWINGmgXOFnw"
}

response = requests.post(url, data=json.dumps(payload), headers=headers)

print(response.text)