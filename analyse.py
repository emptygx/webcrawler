region_keyword_counts = {}
keywords = ['phishing',
'government',
'online shopping',
'job',
'sextortion',
'lottery',
'banking',
'malware',
'advance fee',
'ponzi']

with open('visited.txt', 'r') as file:
    file.readline()
    lines = file.readlines()
    for line in lines:
        info = line.strip().split('|')

        r = info[2].strip()
        for i in range(10):
            if r not in region_keyword_counts:
                region_keyword_counts[r] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            region_keyword_counts[r][i] += int(info[i + 4])

for region, counts in region_keyword_counts.items():
    print(f'Region: {region}')
    for i in range(10):
        keyword = keywords[i]
        count = counts[i]
        print(f'{keyword}: {count}')
    print('\n')
