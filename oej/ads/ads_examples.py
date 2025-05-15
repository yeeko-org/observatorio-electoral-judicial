

def load_meta_apps():
    from oej.ads.meta_api import LoadMetaAds

    load_meta = LoadMetaAds()
    load_meta.all_ads = {}
    load_meta.start_get_ads()
    load_meta.save_ads()
    load_meta.save_list_ads()

    load_meta = LoadMetaAds(limit=20)
    load_meta.start_get_ads(["eleccion"], ["judicial"])
    load_meta.save_ads()

def load_cats():
    from oej.ads.meta_api import LoadMetaAds

    load_meta = LoadMetaAds()

    load_meta.load_locations_cats()
    load_meta.set_locations()
    load_meta.load_positions_cats()
    load_meta.set_positions()
    load_meta.save_ads()
    load_meta.save_list_ads()

def classify_ads():
    from oej.ads.meta_api import LoadMetaAds

    load_meta = LoadMetaAds(limit=500)
    load_meta.classify_ads(limit=500)
    load_meta.save_ads()

    load_meta.classify_duplicate_ads()
    load_meta.save_ads()



def read_from_txt():
    import os

    common_path = "fixture\social_listening"

    file_path = os.path.join(common_path, "all_keywords.txt")
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    keywords_count = {}

    for line in lines:
        keywords = line.split(";")
        for keyword in keywords:
            if keyword.startswith("@"):
                continue
            keyword = keyword.strip()
            keyword = keyword.lower()
            keywords_count.setdefault(keyword, 0)
            keywords_count[keyword] += 1

    sorted_keywords = sorted(
        keywords_count.items(), key=lambda x: x[1], reverse=True)

    for keyword, count in sorted_keywords[:30]:
        print(f"{keyword}: {count}")

