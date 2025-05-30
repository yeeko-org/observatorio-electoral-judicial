import json
from collections import Counter

# Load the JSON data
with open('fixture/ads/all_ads_list.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 1. Count total entries
total_entries = len(data)
print(f"Total entries in the JSON file: {total_entries}")

# 2. Count categories
categories = Counter(item.get('category', 'not_specified') for item in data)
print("\nCategory distribution:")
for category, count in categories.most_common():
    print(f"  {category}: {count} ({count / total_entries * 100:.1f}%)")

# 2.1 Count publisher_platforms (list)
publisher_platforms = Counter()
for item in data:
    platforms = item.get('publisher_platforms', [])
    for platform in platforms:
        publisher_platforms[platform] += 1

# Print the top 10 publisher platforms
print("\nTop 10 publisher platforms:")
for platform, count in publisher_platforms.most_common(10):
    print(f"  {platform}: {count} ({count / total_entries * 100:.1f}%)")


# 3. Count and collect candidates
all_candidates = []
for item in data:
    if 'candidates' in item and item['candidates']:
        for candidate in item['candidates']:
            # Create full name
            first_name = candidate.get('first_name', '')
            last_name1 = candidate.get('last_name1', '')
            last_name2 = candidate.get('last_name2', '')

            full_name = f"{first_name} {last_name1}"
            if last_name2:
                full_name += f" {last_name2}"

            all_candidates.append(full_name.strip())

candidate_count = len(all_candidates)
print(f"\nTotal number of candidate mentions: {candidate_count}")

# Most mentioned candidates
top_candidates = Counter(all_candidates).most_common(10)
print("\nTop 10 most mentioned candidates:")
for candidate, count in top_candidates:
    print(f"  {candidate}: {count}")

# Filter


# 4. Count positions
positions = Counter(item.get('position', 'not_specified') for item in data)
print("\nPosition distribution:")
for position, count in positions.most_common(5000):  # Top 10 positions
    if position:  # Only show non-empty positions
        print(f"  {position}: {count}")

# 4. Count locations
locations = Counter(item.get('location') for item in data)
print("\nLOCATION distribution:")
for location, count in locations.most_common(5000):  # Top 10 locations
    if location:  # Only show non-empty locations
        print(f"  {location}: {count}")


# 5. Count page_names
page_names = Counter(item.get('page_name') for item in data)
print("\nPage names distribution:")
# total
print(f"Total page names: {len(page_names)}")
for page_name, count in page_names.most_common(100):  # Top 10 page names
    if page_name:  # Only show non-empty page names
        print(f"  {page_name}: {count}")

# 6. Count KEYWwORDS
keywords = Counter()
for item in data:
    item_keywords = item.get('keywords', [])
    for keyword in item_keywords:
        keywords[keyword] += 1
# Print the top 10 keywords
print("\nTop 10 keywords:")
for keyword, count in keywords.most_common(10):
    print(f"  {keyword}: {count} ({count / total_entries * 100:.1f}%)")

