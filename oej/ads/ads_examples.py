

def load_meta_apps():
    from oej.ads.meta_api import LoadMetaAds
    from oej.ads.export_ads import ExportAds

    export_ads = ExportAds()
    export_ads.standarize_names(delete_spaces=False)
    direct_keywords = export_ads.names_search
    # keywords_with_spaces = [
    #     keyword for keyword in direct_keywords if " " in keyword]
    keywords_with_accents = []
    for keyword in direct_keywords:
        if any(char in keyword for char in "ÁÉÍÓÚáéíóúü"):
            keywords_with_accents.append(keyword)

    load_meta = LoadMetaAds()
    # load_meta.all_ads = {}
    # load_meta.start_get_ads()
    # load_meta.save_ads()
    # load_meta.save_list_ads()

    # load_meta.special_clean_48(keywords_with_spaces, delete_empty=False)
    # load_meta.save_ads()
    # load_meta.save_list_ads()

    # load_meta.get_direct_keywords(direct_keywords)
    load_meta.get_direct_keywords(keywords_with_accents)
    load_meta.delete_empty_keywords(delete_empty=False, lookup_candidates=True)
    load_meta.save_ads()
    load_meta.save_list_ads()

# load_meta = LoadMetaAds(limit=20)
# load_meta.start_get_ads(["eleccion"], ["judicial"])

def load_cats():
    from oej.ads.meta_api import LoadMetaAds

    load_meta = LoadMetaAds()

    load_meta.load_locations_cats()
    load_meta.set_locations()
    load_meta.set_states()
    load_meta.post_clean_states()
    load_meta.load_positions_cats()
    load_meta.set_positions()
    load_meta.set_direct_positions()
    load_meta.post_clean_positions()
    load_meta.save_ads()
    load_meta.save_list_ads()


def classify_all_ads():
    from oej.ads.meta_api import LoadMetaAds

    load_meta = LoadMetaAds(limit=2000)
    load_meta.classify_ads(limit=2000)
    load_meta.save_ads()
    load_meta.save_list_ads()

    load_meta.classify_duplicate_ads()
    load_meta.save_ads()
    load_meta.save_list_ads()


def export():
    from oej.ads.export_ads import ExportAds
    export_ads = ExportAds()
    export_ads.run()


def special_48():
    from oej.ads.meta_api import LoadMetaAds
    load_meta = LoadMetaAds(limit=1000)
    load_meta.special_clean_48()
    load_meta.save_ads()
    load_meta.save_list_ads()


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

