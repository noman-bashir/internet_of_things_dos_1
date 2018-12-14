import csv

data = [0 for i in range(498240)]
with open ('hCor1.csv', 'rb') as solarFile:
	solarData = csv.reader(solarFile)
	for i, row in enumerate(solarData):
		data[i] = row[0]