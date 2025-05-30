import pandas as pd
import json
import roman
import os
from oej.ads.names import nicknames, ready_cats
from oej.models import Candidate


class ExportAds:

    def __init__(
            self,
    ):
        print("Processing ads data...")
        self.all_data = None
        self.names_search = set()
        self.delete_spaces = True
        self.total_prints = 0
        self.file1_records = []
        self.file2_records = []
        self.integer_fields = [
            'spend_lower_bound', 'spend_upper_bound',
            'estimated_audience_size_lower_bound',
            'estimated_audience_size_upper_bound',
            'impressions_lower_bound', 'impressions_upper_bound',
            'spend_upper_bound', 'quantity', 'spend_lower', 'spend_upper'
        ]
        self.nested_fields = [
            'estimated_audience_size', 'impressions', 'spend']
        self.date_fields = [
            'ad_delivery_start_time', 'ad_delivery_stop_time',
            'ad_creation_time']
        self.boolean_fields = [
            'is_survey', 'vote_promotion']
        self.divide_fields = [
            'ad_creative_bodies', 'ad_creative_link_captions',
            'ad_creative_link_descriptions', 'ad_creative_link_titles']
        self.special_fields = [
            'ad_creative_bodies', 'ad_creative_link_captions',
            'ad_creative_link_descriptions', 'ad_creative_link_titles',
            'keywords', 'estimated_audience_size', 'impressions', 'spend',
            'publisher_platforms', 'candidates', 'vote_promotion'
        ]
        self.platforms = [
            'facebook', 'instagram', 'messenger', 'threads', 'audience_network']
        self.concat_fields = [
            ('real_position', 'positions'),
            ('state', 'states'),
            ('location_details', 'locations'),
            ('category', 'categories'),
            ('specialty', 'specialities'),
        ]
        self.names_dict = {}
        self.national_candidates = {}
        self.other_candidates = {}
        self.skip_candidates = set()
        self.ready_cats = {}
        self.build_real_candidates_dict()
        self.build_ready_candidates_dict()

    def run(
            self,
            json_file_path='fixture/ads/all_ads_list.json',
            output_dir='fixture/ads',
    ):

        self.standarize_names()
        self.build_candidates_dict()
        df1, df2 = self.process_ads_data(json_file_path)
        df3 = self.build_candidates_dataframe()

        # Export to Excel
        self.export_to_excel(df1, df2, df3, output_dir)

    def add_candidate(
            self,
            full_name=None,
            candidate_id:int = None,
            candidate_obj=None,
            is_local=False
    ):
        candidate_data = {
            "oej_id": None,
            "ine_id": None,
            "candidate": full_name,
            "level": "unknown",
            "positions": "No identificado",
            "circuit": "",
            "states": "",
            "locations": "",
            "specialties": "",
        }
        if not candidate_obj and candidate_id:
            # candidate_id = int(candidate_id)
            if full_name:
                candidate_data = self.ready_cats.get(candidate_id)
                if candidate_data:
                    return self.simple_add_candidate(full_name, candidate_data)
            candidate_obj = Candidate.objects.filter(id=candidate_id).first()
        if candidate_obj:
            candidate_id = candidate_obj.id
            if not full_name:
                full_name = candidate_obj.full_name_normalized
            state = candidate_obj.seat.judicial_district.state.short_name
            circuit = candidate_obj.seat.judicial_district.circuit
            candidate_data = {
                "oej_id": candidate_obj.id,
                "ine_id": candidate_obj.id_ine,
                "candidate": candidate_obj.full_name,
                "level": "federal",
                "positions": candidate_obj.seat.position.full_name,
                "circuit": roman.toRoman(circuit),
                "state": state,
                "locations": "",
                "specialties": candidate_obj.seat.topic.name,
            }
        elif is_local:
            candidate_data["candidate"] = full_name
            candidate_data["level"] = "local"
            candidate_data["positions"] = "Locales del Poder Judicial"
        else:
            # raise ValueError("Either full_name or candidate_id must be provided.")
            pass
        self.simple_add_candidate(full_name, candidate_data)
        return self.simple_add_candidate(candidate_id, candidate_data)
        # if candidate_id:
        #     self.ready_cats[candidate_id] = candidate
        #     # self.ready_cats[str(candidate_id)] = candidate
        # self.ready_cats[full_name] = candidate
        # return candidate

    def simple_add_candidate(self, key, candidate_data):
        if key:
            self.ready_cats[key] = candidate_data
        return candidate_data

    def build_real_candidates_dict(self):
        candidates = Candidate.objects\
            .filter(seat__position__by_circuit=False)\
            .select_related(
                'seat__judicial_district',
                'seat__judicial_district__state',
                'seat__position', 'seat__topic'
            )
        for candidate in candidates:
            # full_name = candidate.full_name
            # self.national_candidates[cand_id] = f"{cand_id}-{full_name}"
            # cand_id = candidate.id
            # self.national_candidates[cand_id] = candidate
            self.add_candidate(candidate_obj=candidate)

    def build_ready_candidates_dict(self):
        for name, key in ready_cats.items():
            try:
                oej_id = int(key)
                self.add_candidate(candidate_id=oej_id, full_name=name)
            except ValueError:
                if key == "local":
                    self.add_candidate(full_name=name, is_local=True)
                else:
                    self.skip_candidates.add(name)

    def text_special_normalizer(self, text, delete_spaces=None):
        import unidecode
        import re
        if not text:
            return text
        if delete_spaces is None:
            delete_spaces = self.delete_spaces
        text = text.upper().strip()
        text = unidecode.unidecode(text)
        final_text = text.replace('Ü', 'U')
        final_text = re.sub(r' +', ' ', final_text)
        final_text = final_text.strip()
        if delete_spaces:
            return re.sub(r'[^a-zA-Z\d]', '', final_text)
        else:
            return re.sub(r'[^a-zA-Z\d ]', '', final_text)

    def add_from_list(
            self, name_data, field, standard_name, to_normalize=True):
        exclude_fullname = False
        oej_id = int(name_data.get('id'))
        short_names = name_data.get(field, "").split(',')
        names_search = set()
        for short_name in short_names:
            short_name = short_name.strip()
            # self.names_dict[short_name] = oej_id
            self.add_candidate(
                full_name=short_name, candidate_id=oej_id)
            if to_normalize:
                short_name_std = self.text_special_normalizer(short_name)
                # self.names_dict[short_name_std] = oej_id
                self.add_candidate(
                    full_name=short_name_std, candidate_id=oej_id)
            else:
                short_name_std = short_name
            if not short_name_std:
                continue
            # self.names_search.add(short_name_std)
            names_search.add(short_name_std)
            if short_name_std in standard_name:
                exclude_fullname = True
        return exclude_fullname, names_search

    def standarize_names(self, delete_spaces=True):
        """
        Name structure:
        id
        full_name
        short_names (separated by commas)
        apodos (separated by commas)
        """
        self.delete_spaces = delete_spaces
        for name_data in nicknames:
            oej_id = int(name_data.get('id'))

            full_name = name_data.get('full_name')
            std_name = self.text_special_normalizer(full_name)
            # self.names_dict[std_name] = oej_id
            self.add_candidate(full_name=std_name, candidate_id=oej_id)
            exclude_full_name, names_search = self.add_from_list(
                name_data, 'short_names', std_name)
            if not exclude_full_name:
                names_search.add(std_name)

            full_name_accent = name_data.get('full_name_accent')
            # std_name_accent = self.text_special_normalizer(full_name_accent)
            accent_names_search = set()
            if full_name_accent:
                full_name_accent = full_name_accent.strip()
                # self.names_dict[full_name_accent] = oej_id
                self.add_candidate(
                    full_name=full_name_accent, candidate_id=oej_id)
                exclude_accent_name, accent_names_search = self.add_from_list(
                    name_data, 'short_names_accents', full_name_accent,
                    to_normalize=False)
                if not exclude_accent_name:
                    accent_names_search.add(full_name_accent)

            _, nickname_search = self.add_from_list(
                name_data, 'apodos', std_name, to_normalize=False)
            all_search = names_search.union(accent_names_search, nickname_search)
            for search_name in all_search:
                self.names_search.add(search_name)
                # self.names_dict[search_name] = oej_id
                self.add_candidate(
                    full_name=search_name, candidate_id=oej_id)

        # Save the dictionary to a JSON file

    def build_candidates_dict(self):
        pass

    def find_name_old(self, name, forced=True):
        """
        Find the standardized name in the dictionary.
        """
        std_name = self.text_special_normalizer(name, delete_spaces=True)
        if std_name in self.names_dict:
            return self.names_dict[std_name]
        elif name in self.names_dict:
            return self.names_dict[name]
        elif forced:
            return self.text_special_normalizer(name, delete_spaces=False)
        else:
            return None

    def find_name(self, name, forced=True):
        """
        Find the standardized name in the dictionary.
        """
        std_name = self.text_special_normalizer(name, delete_spaces=True)
        if candidate_data := self.ready_cats.get(std_name):
            return candidate_data
        elif candidate_data := self.ready_cats.get(name):
            return candidate_data
        elif name in self.skip_candidates:
            return None
        elif forced:
            std_name = self.text_special_normalizer(
                name, delete_spaces=False)
            if candidate_data := self.ready_cats.get(std_name):
                return candidate_data
            return self.add_candidate(full_name=std_name)
        else:
            return None

    def to_date(self, date_str):
        from datetime import datetime
        date_format = '%Y-%m-%d'
        if not date_str:
            return None
        return datetime.strptime(date_str, date_format).date()

    def process_ads_data(self, json_file_path):
        """
        Process the ads data from a JSON file and prepare two dataframes.

        Args:
            json_file_path (str): Path to the JSON file containing the ads data

        Returns:
            tuple: Two dataframes, one for File 1 and one for File 2
        """
        # Load JSON data
        with open(json_file_path, 'r', encoding='utf-8') as file:
            self.all_data = json.load(file)

        self.file1_records = []
        self.file2_records = []

        for ad in self.all_data:
            self.process_add(ad)

        # Create DataFrames
        df1 = pd.DataFrame(self.file1_records)
        df2 = pd.DataFrame(self.file2_records)

        return df1, df2

    def process_add(self, ad):
        # Create a base record with all fields
        record = {}

        # Process standard fields first
        for key, value in ad.items():
            if key in self.integer_fields:
                # Convert to int if the value is a string
                if isinstance(value, str) and value.isdigit():
                    record[key] = int(value)
                else:
                    record[key] = value
            elif key not in self.special_fields:
                record[key] = value

        # Convert boolean values to 1/0
        for key in self.boolean_fields:
            if key in ad:
                record[key] = 1 if ad[key] else 0
            else:
                record[key] = 0

        # Join text arrays with line breaks
        for field in self.divide_fields:
            if field in ad and ad[field]:
                record[field] = '\n'.join([str(item) for item in ad[field]])
            else:
                record[field] = ''

        # Process keywords: replace %20 with space and join with line breaks
        if 'keywords' in ad and ad['keywords']:
            record['keywords'] = '\n'.join(
                [str(k).replace('%20', ' ') for k in ad['keywords']])
        else:
            record['keywords'] = ''

        # Expand nested dictionaries to direct columns
        for nested_field in self.nested_fields:
            if nested_field in ad and isinstance(ad[nested_field], dict):
                for sub_key, sub_value in ad[nested_field].items():
                    record[f"{nested_field}_{sub_key}"] = sub_value

        # Create platform columns with 0/1 values
        ad_platforms = ad.get('publisher_platforms', [])
        for platform in self.platforms:
            record[f"platform_{platform}"] = 1 if platform in ad_platforms else 0

        record = self.process_record_dates(ad, record)
        record['is_survey'] = self.process_record_survey(record)

        # Process candidates and build full names
        candidates = ad.get('candidates', [])
        # candidates_data = []
        unique_candidates = set()
        if candidates is None:
            candidates = []

        str_keywords = record.get('keywords', '')
        keywords = str_keywords.split('\n') if str_keywords else []
        for keyword_combo in keywords:
            keyword_combo = keyword_combo.strip()
            cand_data = self.find_name(keyword_combo, forced=False)
            if cand_data:
                # candidates_data.append(cand_data)
                key = cand_data.get('oej_id') or cand_data.get('candidate')
                unique_candidates.add(key)

        try:
            for candidate in candidates:
                pass
        except TypeError:
            print(f"Error processing candidates for ad: {ad}")
            return
        some_skip = False

        for candidate in candidates:
            # Extract name parts, handling possible None values
            first_name = candidate.get('first_name', '')
            last_name1 = candidate.get('last_name1', '')
            last_name2 = candidate.get('last_name2', '')

            # Build full name (skip null/None values)
            name_parts = []
            if first_name and first_name != 'null' and first_name is not None:
                name_parts.append(str(first_name))
            if last_name1 and last_name1 != 'null' and last_name1 is not None:
                name_parts.append(str(last_name1))
            if last_name2 and last_name2 != 'null' and last_name2 is not None:
                name_parts.append(str(last_name2))

            full_name = ' '.join(name_parts)

            if full_name:
                # Normalize the full name
                cand_data = self.find_name(full_name)
                if cand_data:
                    # candidates_data.append(cand_data)
                    key = cand_data.get('oej_id') or cand_data.get('candidate')
                    unique_candidates.add(key)
                else:
                    some_skip = True

        if not unique_candidates and some_skip:
            return

        record = self.process_quatities(record, unique_candidates)
        # For File 1: Add all candidates in one column with line breaks
        # str_candidates = [str(name) for name in unique_candidates if name]
        str_candidates = []
        for cand_key in unique_candidates:
            if isinstance(cand_key, int):
                cand_data = self.ready_cats.get(cand_key)
                if cand_data:
                    str_candidates.append(cand_data['candidate'])
                    continue
            cand_data = self.find_name(cand_key, forced=False)
            if cand_data:
                str_candidates.append(cand_data['candidate'])
            else:
                str_candidates.append(str(cand_key))

        # For File 2: Create one record per candidate
        if unique_candidates:
            for candidate_name in unique_candidates:
                candidate_record = record.copy()
                if isinstance(candidate_name, int):
                    # TODO Right now
                    candidate_name = self.national_candidates.get(
                        candidate_name, candidate_name)
                else:
                    # TODO Right now
                    if candidate_name not in self.national_candidates:
                        default_dict = {}
                        for _, plural_field in self.concat_fields:
                            default_dict[plural_field] = set()
                        self.other_candidates.setdefault(
                            candidate_name, default_dict)
                    for field, plural in self.concat_fields:
                        if field in candidate_record:
                            self.other_candidates[candidate_name][plural].add(
                                candidate_record[field])
                candidate_name = candidate_name.strip()
                candidate_record['candidate'] = candidate_name
                # Remove the combined candidates field
                if 'candidates_full_names' in candidate_record:
                    del candidate_record['candidates_full_names']

                self.file2_records.append(candidate_record)

        # For File 2: Create one record per candidate
        for cand_key in unique_candidates:
            cand_data = None
            if isinstance(cand_key, int):
                cand_data = self.ready_cats.get(cand_key)
                if cand_data:
                    str_candidates.append(cand_data['candidate'])

            if not cand_data:
                cand_data = self.find_name(cand_key, forced=True)
            if not cand_data:
                raise ValueError(
                    f"algo está mal con cand_data, cand_key {cand_key}")
            str_candidates.append(cand_data['candidate'])
            oej_id = cand_data.get('oej_id')
            candidate_record = record.copy()
            if not oej_id:
                default_dict = {}
                for _, plural_field in self.concat_fields:
                    default_dict[plural_field] = set()
                self.other_candidates.setdefault(
                    candidate_name, default_dict)
                for field, plural in self.concat_fields:
                    if field in candidate_record:
                        self.other_candidates[candidate_name][plural].add(
                            candidate_record[field])
            # candidate_name = candidate_name.strip()
            candidate_record.update(cand_data)
            self.file2_records.append(candidate_record)
        if not unique_candidates:
            # Handle case with no candidates
            candidate_record = record.copy()
            candidate_record['candidate'] = ''
            self.file2_records.append(candidate_record)
        record['candidates_full_names'] = '\n'.join(str_candidates)
        self.file1_records.append(record)

    def process_record_dates(self, ad, record):
        from datetime import datetime
        for date_field in self.date_fields:
            record[date_field] = self.to_date(ad.get(date_field, ''))
        begin_campaigns = self.to_date("2025-03-31")
        end_campaigns = self.to_date("2025-05-29")
        election_date = self.to_date("2025-06-01")
        stop_time = record.get("ad_delivery_stop_time")
        if not stop_time:
            stop_time = datetime.now().date()
        if record["ad_delivery_start_time"] < begin_campaigns:
            period = "anticipate"
        elif stop_time >= election_date:
            period = "election_day"
        elif stop_time > end_campaigns:
            period = "post_campaign"
        else:
            period = "campaign"
        record['period'] = period
        for date_field in self.date_fields:
            if date_value := record.get(date_field):
                record[date_field] = date_value.strftime('%Y-%m-%d')
        return record

    def process_quatities(self, record, candidate_full_names):
        # Add candidate count
        len_candidates = len(candidate_full_names)
        record['quantity'] = len_candidates
        spend_lower_bound = record.get('spend_lower_bound', 0)
        spend_upper_bound = record.get('spend_upper_bound', 0)
        currency = record.get('currency', 'MXN')
        if currency == 'USD':
            spend_lower_bound *= 20
            spend_upper_bound *= 20
            record['currency'] = 'MXN'
            record['spend_lower_bound'] = spend_lower_bound
            record['spend_upper_bound'] = spend_upper_bound
        if len_candidates > 1:
            spend_lower_bound = int(spend_lower_bound)
            spend_upper_bound = int(spend_upper_bound)
            record['spend_lower'] = spend_lower_bound / len_candidates
            record['spend_upper'] = spend_upper_bound / len_candidates
        else:
            record['spend_lower'] = record['spend_lower_bound']
            record['spend_upper'] = record['spend_upper_bound']
        return record

    def process_record_survey(self, record):
        survey_words = [
            'encuesta', 'encuestas', 'sondeo', 'sondeos', 'encuestadora',
            'encuestadoras', 'preferencia', 'preferencias',
        ]
        is_survey = record.get('is_survey', 0)

        for content_field in self.divide_fields:
            for word in survey_words:
                if word in record.get(content_field, '').lower():
                    is_survey = 1
                    break
            if is_survey:
                break
        return is_survey

    def build_candidates_dataframe(self):
        """
        Build a DataFrame for candidates with their details.

        Returns:
            DataFrame: DataFrame containing candidate details
        """
        import pandas as pd
        from django.db.models import Q
        import operator
        from functools import reduce
        from oej.models import Position

        # Prepare candidate records
        candidate_records = []
        others_positions = [
            "Otros del Poder judicial", "No especificado",
        ]
        national_positions = Position.objects.filter(by_circuit=False)\
            .values_list('full_name', flat=True)
        circuit_positions = Position.objects.filter(by_circuit=True)\
            .values_list('full_name', flat=True)
        for pos in national_positions:
            print(f"-{pos}-")

        def eval_count(candidate_obj, all_names):
            full_name = candidate_obj.full_name_normalized
            sub_counts = sum([
                1 for sub_name in all_names if sub_name in full_name])
            return sub_counts > 1

        for candidate_name, details in self.other_candidates.items():
            record = {'candidate': candidate_name, 'id': None}
            for _, plural in self.concat_fields:
                str_data = [str(item) for item in details[plural] if item]
                record[plural] = ', '.join(str_data) if str_data else ''
            specified_positions = [
                str(item) for item in details['positions']
                if item and item != 'No especificado']
            if len(specified_positions) == 1:
                if specified_positions[0] == 'Otras posiciones (no judiciales)':
                    continue

            real_positions = [
                str(item) for item in specified_positions
                if item and str(item) not in others_positions]

            final_position = None
            if len(real_positions) == 1:
                record['positions'] = real_positions[0]
                final_position = real_positions[0]
            if final_position:
                candidate = Candidate.objects.filter(
                    full_name_normalized=candidate_name).first()
                if candidate:
                    record['id'] = candidate.id
            scjn = 'Ministras y ministros de la SCJN'
            if not record['id']:
                if final_position in national_positions:
                    candidate = Candidate.objects.filter(
                        full_name_normalized__icontains=candidate_name,
                        seat__position__full_name__icontains=final_position
                    ).first()
                    if candidate:
                        record['id'] = candidate.id
            state = record.get('states', '')
            if not record['id'] and state and ',' not in state:
                if final_position in circuit_positions:
                    candidate = Candidate.objects.filter(
                        full_name_normalized__icontains=candidate_name,
                        seat__position__full_name__icontains=final_position,
                        seat__judicial_district__state__short_name=state
                    )
                    count = candidate.count()
                    if count == 1:
                        record['id'] = candidate.first().id
                    elif count > 1:
                        print(f"Multiple candidates found for {candidate_name}"
                              f" in {final_position} ({count})")

            record['ad_snapshot_url'] = ''
            record['alternatives'] = ''
            if not record['id']:
                name_ads = [ad for ad in self.file2_records
                            if ad.get('candidate') == candidate_name]

                if name_ads:
                    record['ad_snapshot_url'] = name_ads[0].get(
                        'ad_snapshot_url', '')
            if not record['id']:
                if new_id := ready_cats.get(candidate_name):
                    record['id'] = new_id
                    print(f"Using ready candidate: {candidate_name} ({new_id})")
            if not record['id'] and final_position:
                candidates = Candidate.objects.filter(
                    seat__position__full_name=final_position)
                sub_names = candidate_name.split(' ')
                alternatives = []
                if state and not ',' in state:
                    candidates = candidates.filter(
                        seat__judicial_district__state__short_name=state)
                    candidates = candidates.filter(
                        reduce(
                            operator.or_,
                            [Q(full_name_normalized__icontains=name)
                             for name in sub_names]))

                    for cand in candidates:
                        many = eval_count(cand, sub_names)
                        if not many:
                            continue
                        topic = cand.seat.topic.name
                        alternatives.append(
                            f"{cand.full_name_normalized} - {topic} ({cand.id})")
                elif final_position in circuit_positions:
                    candidates = candidates.filter(
                        reduce(
                            operator.or_,
                            [Q(full_name_normalized__icontains=name)
                             for name in sub_names]))
                    for cand in candidates:
                        many = eval_count(cand, sub_names)
                        if not many:
                            continue
                        topic = cand.seat.topic.name
                        state = cand.seat.judicial_district.state.short_name
                        alternatives.append(
                            f"{cand.full_name_normalized} - {topic} - {state} ({cand.id})")
                elif final_position in national_positions:
                    candidates = candidates.filter(
                        reduce(
                            operator.or_,
                            [Q(full_name_normalized__icontains=name)
                             for name in sub_names]))
                    for cand in candidates:
                        many = eval_count(cand, sub_names)
                        if not many:
                            continue
                        alternatives.append(
                            f"{cand.full_name_normalized} ({cand.id})")
                if alternatives:
                    record['alternatives'] = '\n'.join(alternatives)
            candidate_records.append(record)

        # Create DataFrame
        df_candidates = pd.DataFrame(candidate_records)
        return df_candidates

    def get_best_match(self, title, candidates):
        from difflib import SequenceMatcher as Matcher
        title = title.replace("La Jornada_", "")

        best_matchs = [
            (Matcher(None, title, cand.full_name_normalized).ratio(), cand)
            for cand in candidates]

        if not best_matchs:
            return None

        best_matchs.sort(key=lambda x: x[0], reverse=True)
        if best_matchs[0][0] > 0.9:
            return best_matchs[0][1]



    def export_to_excel(self, df1, df2, df3, output_dir='.'):
        """
        Export the dataframes to Excel files.

        Args:
            df1 (DataFrame): DataFrame for File 1
            df2 (DataFrame): DataFrame for File 2
            output_dir (str): Directory to save the Excel files
        """
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        columns_to_export = [
            'id', 'page_id', 'ad_delivery_start_time', 'ad_delivery_stop_time',
            'period', 'is_survey', 'ad_snapshot_url', 'bylines',
            'page_name', 'candidate',
            'real_position', 'currency', 'category', 'state',
            'location_details', 'specialty', 'vote_promotion',
            'ad_creative_bodies', 'ad_creative_link_captions',
            'ad_creative_link_descriptions', 'ad_creative_link_titles',
            'keywords', 'estimated_audience_size_lower_bound',
            'estimated_audience_size_upper_bound', 'impressions_lower_bound',
            'impressions_upper_bound', 'spend_lower_bound', 'spend_upper_bound',
            'quantity', 'spend_lower', 'spend_upper'
        ]

        all_integer_fields = self.integer_fields + self.boolean_fields

        # Function to prepare dataframe for export
        def prepare_dataframe(df):
            # Select only the specified columns that exist in the dataframe
            available_columns = [col for col in columns_to_export if col in df.columns]
            df_export = df[available_columns].copy()

            # Convert specified columns to integers
            for col in all_integer_fields:
                if col in df_export.columns:
                    df_export[col] = pd.to_numeric(df_export[col], errors='coerce').fillna(0).astype(int)

            return df_export

        # df1_export = prepare_dataframe(df1)
        df2_export = prepare_dataframe(df2)

        # Export to Excel
        # file1_path = os.path.join(output_dir, 'meta_ads_file1.xlsx')
        # file2_path = os.path.join(output_dir, 'meta_ads_file2.xlsx')
        file_candidates_path = os.path.join(output_dir, 'candidates.xlsx')

        # df1.to_excel(file1_path, index=False)
        # print(f"File 1 exported to {file1_path} with {len(df1)} records")
        #
        # df2_export.to_excel(file2_path, index=False)
        # print(f"File 2 exported to {file2_path} with {len(df2)} records")

        df3.to_excel(file_candidates_path, index=False)
        print(f"Candidates exported to {file_candidates_path} with {len(df3)} records")
