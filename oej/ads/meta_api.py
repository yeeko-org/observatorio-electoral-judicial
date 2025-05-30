import requests
from django.conf import settings
from tqdm import tqdm
import json


class LoadMetaAds:
    fields = [
        "id",
        "ad_creation_time",
        "ad_creative_bodies",
        "ad_creative_link_captions",
        "ad_creative_link_descriptions",
        "ad_creative_link_titles",
        "ad_delivery_start_time",
        "ad_delivery_stop_time",
        "ad_snapshot_url",
        "bylines",
        "currency",
        "estimated_audience_size",
        "impressions",
        "page_id",
        "page_name",
        "publisher_platforms",
        "spend"
    ]
    extra_fields = [
        "delivery_by_region",
        "demographic_distribution",
    ]

    def __init__(
            self, date_start='2025-03-01', date_end=None, limit=5000,
            include_extra_fields=False, fields=None
    ):
        self.token = settings.FB_ACCESS_TOKEN
        self.v_api_fb = settings.V_API_FB
        self.all_ads = {}
        self.unique_ads = set()
        self.site_url = None
        self.base_graph_url = f"https://graph.facebook.com/{self.v_api_fb}/"
        # self.date_start = date_start
        # self.date_end = date_end
        self.base_path = "fixture/ads/all_ads.json"
        self.limit = limit
        self.last_response = None
        self.locations_dict = {}
        self.full_positions_dict = {}
        positions_dict = {
            "0": "No especificado",
            "1": "Ministras y Ministros de la SCJN",
            "2": "Magistraturas del Tribunal de Disciplina Judicial (TDJ)",
            "3": "Magistraturas de la Sala Superior del TEPJF",
            "4": "Magistraturas de las Salas Regionales del TEPJF",
            "5": "Magistraturas de Circuito",
            "6": "Juezas y jueces de Distrito",
            "10": "Otros del Poder judicial",
            "20": "Otros del Poder judicial",
            "99": "Otras posiciones (no judiciales)",
        }
        self.positions_dict = {}
        for position_id, position_name in positions_dict.items():
            self.positions_dict[position_id] = position_name
            position_int = int(position_id)
            self.positions_dict[str(position_int)] = position_name
        fields = fields or self.fields
        if include_extra_fields:
            fields += self.extra_fields
        self.fields_str = ",".join(fields)
        self.load_saved_ads()
        self.common_url = (
            f"{self.base_graph_url}ads_archive?ad_reached_countries=MX"
            f"&ad_type=POLITICAL_AND_ISSUE_ADS&access_token={self.token}"
            f"&limit={self.limit}&pretty=0&fields={self.fields_str}"
            f"&ad_delivery_date_min={date_start}&unmask_removed_content=true"
        )
        if date_end:
            self.common_url += f"&ad_delivery_date_max={date_end}"

    def start_get_ads(self, keywords1=None, keywords2=None):
        if not keywords1:
            keywords1 = [
                "candidato", "candidata", "candidatos", "candidatura",
                "candidatas",
                "eleccion", "elecciones", "encuesta", "sondeo", "electoral"]
        if not keywords2:
            keywords2 = [
                "judicial", "juez", "jueces", "jueza",
                "magistrado", "magistrada", "magistrados",
                "magistratura", "magistraturas",
                "ministro", "ministra", "ministros", "ministras",
                "tribunal", "scjn", "suprema"]
        self.build_keywords(keywords1, keywords2)

    def build_keywords(self, keywords1, keywords2):
        keywords = []
        for keyword1 in keywords1:
            for keyword2 in keywords2:
                keywords.append((keyword1, keyword2))
        for keyword1, keyword2 in keywords:
            self.get_ads(keyword1, keyword2)

    def get_direct_keywords(self, keywords):
        for keyword in keywords:
            keyword = keyword.strip()
            keyword = keyword.lower()
            keyword = keyword.replace(" ", "%20")
            self.get_ads(keyword, exact_phrase=True)

    def get_ads(self, keyword1, keyword2=None, exact_phrase=False):
        # post_message_url = ('https://graph.facebook.com/%s/me/messenger_profile?'
        #                     'access_token=%s' % (settings.V_API_FB, token))
        search_terms = f"&search_terms={keyword1}"
        if keyword2:
            search_terms += f"%20{keyword2}"
        search_terms = search_terms.replace(" ", "%20")
        request_url = f"{self.common_url}{search_terms}"
        if exact_phrase:
            request_url += "&search_type=KEYWORD_EXACT_PHRASE"
        print(f"request_url: {request_url}")
        self.get_response(request_url, search_terms)

    def get_response(self, request_url, search_terms):
        response = requests.get(request_url)
        self.last_response = response
        data = response.json()
        # print("data", data)
        simple_search_terms = search_terms.replace("&search_terms=", "")
        for ad in data.get("data", []):
            ad_id = ad.get("id")
            if ad_id not in self.all_ads:
                ad.setdefault("keywords", [])
                ad.setdefault("category", "new")
                ad["keywords"].append(simple_search_terms)
                self.all_ads[ad_id] = ad
            else:
                keywords = self.all_ads[ad_id].get("keywords", [])
                if simple_search_terms not in keywords:
                    self.all_ads[ad_id]["keywords"].append(simple_search_terms)
                self.all_ads[ad_id].update(ad)
        if "paging" in data and self.limit >= 5000:
            next_url = data["paging"].get("next")
            if next_url:
                self.get_response(next_url, search_terms)

    def classify_ads(
            self, ai_company='deepseek', engine='deepseek-chat', limit=999999):
        from oej.sonar.sonar_research import SonarResearch
        deepseek = SonarResearch(
            ai_company=ai_company, engine=engine, to_json=True)
        ads_blocks = []
        current_count = 0
        current_block = ""
        for ad_id, ad_data in self.all_ads.items():
            text = "\n".join(ad_data.get("ad_creative_bodies", []))
            category = ad_data.get("category")
            is_new = category == "new"
            if text in self.unique_ads:
                self.all_ads[ad_id]["category"] = "duplicate"
                continue
            self.unique_ads.add(text)
            if category and not is_new:
                continue
            if not text:
                self.all_ads[ad_id]["category"] = "unknown"
                continue
            current_count += 1
            current_block += f"ID: {ad_id}\n\n"
            current_block += f"{text}\n"
            if current_count % 10 == 0:
                ads_blocks.append(current_block)
                current_block = ""
            if current_count >= limit:
                break

        desc = f"Classifying ads ({len(ads_blocks)})"
        for ads_block in tqdm(ads_blocks, desc=desc):
            deepseek.build_prompt("oej/ads/classify_ads.txt")
            result = deepseek.send_prompt(user_prompt=ads_block)
            if not result:
                print("No result")
                continue
            for ad_id, new_ad_data in result.items():
                ad_data = self.all_ads.get(ad_id)
                full_data = ad_data.copy()
                full_data.update(new_ad_data)
                self.all_ads[ad_id] = full_data

    def classify_duplicate_ads(self):
        unique_texts = []
        for ad_id, ad_data in self.all_ads.items():
            if ad_data.get("category") == "duplicate":
                continue
            text = "\n".join(ad_data.get("ad_creative_bodies", []))
            unique_texts.append({
                "id": ad_id,
                "text": text,
                "data": ad_data
            })

        update_fields = [
            "category", "vote_promotion", "candidates", "position", "location"]
        for ad_id, ad_data in self.all_ads.items():
            if ad_data.get("category") == "duplicate":
                text = "\n".join(ad_data.get("ad_creative_bodies", []))
                first_unique = next((
                    item for item in unique_texts
                    if item["text"] == text), None)
                if first_unique:
                    first_unique_data = first_unique["data"]
                    for field in update_fields:
                        if field in first_unique_data:
                            ad_data[field] = first_unique_data.get(field)
                    self.all_ads[ad_id] = ad_data

    def load_site_url(self):
        import requests
        page_url = ("https://www.facebook.com/ads/archive/render_ad/?id=1042382157852000"
                     "&access_token=XXX")
        response = requests.get(page_url)

        # props
        # placeholderElement

    def load_locations_cats(self):
        from geo.models import State
        states_dict = {state.inegi_code: state.short_name
                       for state in State.objects.all()}
        with open("fixture/ads/text_locations.txt", "r", encoding="utf-8") as file:
            locations = file.read().splitlines()
        for location in locations:
            text, state_id, details = location.split("|")
            state = states_dict.get(state_id)
            self.locations_dict[text] = {
                "state": state,
                "details": details
            }

    def set_locations(self):
        for ad_id, ad_data in self.all_ads.items():
            location = ad_data.get("location")
            if not location:
                continue
            loc_data = self.locations_dict.get(location)
            if not loc_data:
                print(f"Location not found: {location}")
                continue
            self.all_ads[ad_id]["state"] = loc_data["state"]
            self.all_ads[ad_id]["location_details"] = loc_data["details"]

    def set_states(self):
        from geo.models import State
        states_dict = {state.inegi_code: state.short_name
                       for state in State.objects.all()}
        for ad_id, ad_data in self.all_ads.items():
            state = ad_data.get("state")
            if not state:
                continue
            if state in states_dict:
                self.all_ads[ad_id]["state"] = states_dict[state]
            else:
                print(f"State not found: {state}")

    def post_clean_states(self):
        from geo.models import State
        states_dict = {state.id: state.short_name
                       for state in State.objects.all()}
        for ad_id, ad_data in self.all_ads.items():
            state = ad_data.get("state")
            if not state:
                continue
            try:
                state_int = int(state)
                state = states_dict.get(state_int)
                if state:
                    self.all_ads[ad_id]["state"] = state
            except ValueError:
                continue

    def load_positions_cats(self):
        from oej.models import Position

        with open("fixture/ads/text_positions.txt", "r", encoding="utf-8") as file:
            positions = file.read().splitlines()
        #Magistrada en Materia Penal del Tribunal Superior de Justicia del Estado|2|Penal
        # Magistrada del Tribunal de Justicia Administrativa|2
        # Magistrado Local|2
        for position_data in positions:
            text, position_id, specialty = position_data.split("|")
            position_id = str(position_id)
            position = self.positions_dict.get(position_id)
            if not position:
                print(f"Position not found: {position_id}")
                print(f"position_data: {position_data}")
                continue
            self.full_positions_dict[text] = {
                "position": position,
                "specialty": specialty
            }

    def set_positions(self):
        for ad_id, ad_data in self.all_ads.items():
            position = ad_data.get("position")
            if not position:
                continue
            pos_data = self.full_positions_dict.get(position)
            if not pos_data:
                print(f"Position not found: {position}")
                continue
            self.all_ads[ad_id]["real_position"] = pos_data["position"]
            self.all_ads[ad_id]["specialty"] = pos_data["specialty"]

    def set_direct_positions(self):

        for ad_id, ad_data in self.all_ads.items():
            position = ad_data.get("real_position")
            if not position:
                continue
            position = str(position)
            pos_data = self.positions_dict.get(position)
            if not pos_data:
                print(f"Position not found: {position}")
                continue
            self.all_ads[ad_id]["real_position"] = pos_data

    def post_clean_positions(self):
        for ad_id, ad_data in self.all_ads.items():
            real_position = ad_data.get("real_position")
            if isinstance(real_position, int):
                position = self.positions_dict.get(str(real_position))
                if position:
                    self.all_ads[ad_id]["real_position"] = position

    def load_saved_ads(self):
        try:
            with open(self.base_path, "r", encoding="utf-8") as file:
                self.all_ads = json.load(file)
        except FileNotFoundError:
            self.all_ads = {}

    def save_ads(self):
        with open(self.base_path, "w", encoding="utf-8") as file:
            json.dump(self.all_ads, file, ensure_ascii=False, indent=4)

    def save_list_ads(self):
        data = self.all_ads.values()
        data = list(data)
        list_path = self.base_path.replace(".json", "_list.json")
        with open(list_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def special_clean_48(self, bad_finds=None, delete_empty=True):
        if not bad_finds:
            bad_finds = ["el%20candidato 48", "candidato 48"]
        ads_to_remove = []
        for ad_id, ad_data in self.all_ads.items():
            keywords = ad_data.get("keywords", [])
            modified = False
            for bad_find in bad_finds:
                real_bad_find = bad_find.strip().lower()
                real_bad_find = real_bad_find.replace(" ", "%20")
                if real_bad_find in keywords:
                    keywords.remove(real_bad_find)
                    modified = True
            if not keywords:
                ads_to_remove.append(ad_id)
            elif modified:
                self.all_ads[ad_id]["keywords"] = keywords

        self.delete_empty_keywords(ads_to_remove, delete_empty)

    def delete_empty_keywords(
            self, ads_to_remove=None, delete_empty=True, lookup_candidates=False):
        if not ads_to_remove:
            ads_to_remove = []
            for ad_id, ad_data in self.all_ads.items():
                keywords = ad_data.get("keywords", [])
                if not keywords:
                    candidates = ad_data.get("candidates", [])
                    if lookup_candidates:
                        if not candidates:
                            ads_to_remove.append(ad_id)
                    else:
                        ads_to_remove.append(ad_id)

        if delete_empty:
            for ad_id in ads_to_remove:
                if ad_id in self.all_ads:
                    print(f"Removing ad {ad_id} with no keywords")
                    del self.all_ads[ad_id]
        else:
            print(f"Ads with no keywords: {len(ads_to_remove)}")
            for ad_id in ads_to_remove:
                print(f"Ad {ad_id} has no keywords")
