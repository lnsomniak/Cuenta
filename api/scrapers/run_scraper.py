from target import search_products
# a simple tcni or whatever the acronym is scraper. where I found out that fresh meat has no nutrition data so i'll probably be manually importing a lot of it from USDA. gg. 
results = search_products("chicken breast")
for r in results[:5]:
    tcin = r.get('tcin')
    title = r.get('item', {}).get('product_description', {}).get('title', '')
    print(f"{tcin}: {title[:50]}")