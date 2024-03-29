from pyzotero import zotero
library_id = '9995734'
library_type = 'user'
api_key = 'kmAjQIHZRMT1eCTmYbDltAZP'
zot = zotero.Zotero(library_id, library_type, api_key)
items = zot.top(limit=5)
# we've retrieved the latest five top-level items in our library
# we can print each item's item type and ID
for item in items:
    print('Item: %s | Key: %s' % (item['data']['itemType'], item['data']['key']))
info = zot.items()
print(info)