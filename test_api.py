import urllib.request
import json

for filter_type in ['overdue', '30', '60', 'all']:
    url = f'http://127.0.0.1:5000/api/tools/inspection-reminders?filter={filter_type}'
    req = urllib.request.Request(url)
    r = urllib.request.urlopen(req)
    data = json.loads(r.read())
    
    print(f"\n=== Filter: {filter_type} ===")
    print(f"Total: {data['data']['total']}")
    scrapped = [t for t in data['data']['items'] if t.get('status') == '报废']
    if scrapped:
        print(f"⚠️ Found {len(scrapped)} scrapped items:")
        for t in scrapped[:3]:
            print(f"  {t['code']} - {t['name']}")
    else:
        print("✅ No scrapped items")
req = urllib.request.Request(url)
r = urllib.request.urlopen(req)
data = json.loads(r.read())

print(f"Total overdue: {data['data']['total']}")
print("\nFirst 5 items:")
for t in data['data']['items'][:5]:
    print(f"  {t['code']} - {t['name']} - 状态:{t['status']}")

# Check if any scrapped items exist
scrapped = [t for t in data['data']['items'] if t['status'] == '报废']
if scrapped:
    print(f"\n⚠️ Found {len(scrapped)} scrapped items (should be 0 after fix):")
    for t in scrapped[:3]:
        print(f"  {t['code']} - {t['name']}")
else:
    print("\n✅ No scrapped items in reminders - fix working!")
