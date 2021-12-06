all: download process

download:
	@python3 -mvenv .venv
	@.venv/bin/pip install --upgrade pip
	@.venv/bin/pip install -r requirements.txt
	@curl --progress-bar -L http://download.geonames.org/export/dump/allCountries.zip > dump/allCountries.zip
	@cd dump; unzip -o allCountries.zip
	@curl --progress-bar -L http://download.geonames.org/export/dump/alternateNamesV2.zip > dump/alternateNamesV2.zip
	@cd dump; unzip -o alternateNamesV2.zip
	@rm dump/{allCountries,alternateNamesV2}.zip

process:
	@.venv/bin/python prepare.py

.PHONY: all download process
