import pandas as pd
import json
import os
from oej.ads.names import names


class ExportAds:

    def __init__(
            self,
    ):
        self.names_dict = {}
        print("Processing ads data...")
        self.standarize_names()

    def run(
            self,
            json_file_path='fixture/ads/all_ads_list.json',
            output_dir='fixture/ads',
    ):
        df1, df2 = self.process_ads_data(json_file_path)

        # Export to Excel
        self.export_to_excel(df1, df2, output_dir)

    def text_special_normalizer(self, text, delete_spaces=True):
        import unidecode
        import re
        if not text:
            return text
        text = text.upper().strip()
        text = unidecode.unidecode(text)
        final_text = text.replace('Ü', 'U')
        final_text = re.sub(r' +', ' ', final_text)
        final_text = final_text.strip()
        if delete_spaces:
            return re.sub(r'[^a-zA-Z]', '', final_text)
        else:
            return re.sub(r'[^a-zA-Z ]', '', final_text)

    def standarize_names(self):
        """
        Name structure:
        full_name
        short_names (separated by commas)
        apodos (separated by commas)
        """
        for name in names:
            full_name = name.get('full_name')
            std_name = self.text_special_normalizer(full_name)
            self.names_dict[std_name] = full_name
            short_names = name.get('short_names', "").split(',')
            for short_name in short_names:
                short_name = short_name.strip()
                self.names_dict[short_name] = full_name
                short_name_std = self.text_special_normalizer(short_name)
                self.names_dict[short_name_std] = full_name
            apodos = name.get('apodos', '').split(',')
            apodos = [apodo.strip() for apodo in apodos if apodo.strip()]
            for apodo in apodos:
                self.names_dict[apodo] = full_name
                apodo_std = self.text_special_normalizer(apodo)
                self.names_dict[apodo_std] = full_name
        # Save the dictionary to a JSON file

    def find_name(self, name, forced=True):
        """
        Find the standardized name in the dictionary.
        """
        std_name = self.text_special_normalizer(name)
        if std_name in self.names_dict:
            return self.names_dict[std_name]
        elif name in self.names_dict:
            return self.names_dict[name]
        elif forced:
            return self.text_special_normalizer(name, delete_spaces=False)
        else:
            return None

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
            data = json.load(file)

        file1_records = []
        file2_records = []
        integer_fields = [
            'spend_lower_bound', 'spend_upper_bound',
            'estimated_audience_size_lower_bound',
            'estimated_audience_size_upper_bound',
            'impressions_lower_bound', 'impressions_upper_bound'
        ]
        special_fields = [
            'ad_creative_bodies', 'ad_creative_link_captions',
            'ad_creative_link_descriptions', 'ad_creative_link_titles',
            'keywords', 'estimated_audience_size', 'impressions', 'spend',
            'publisher_platforms', 'candidates', 'vote_promotion'
        ]
        divide_fields = [
            'ad_creative_bodies', 'ad_creative_link_captions',
            'ad_creative_link_descriptions', 'ad_creative_link_titles']
        platforms = [
            'facebook', 'instagram', 'messenger', 'threads', 'audience_network']

        for ad in data:
            # Create a base record with all fields
            record = {}

            # Process standard fields first
            for key, value in ad.items():
                if key in integer_fields:
                    # Convert to int if the value is a string
                    if isinstance(value, str) and value.isdigit():
                        record[key] = int(value)
                    else:
                        record[key] = value
                elif key not in special_fields:
                    record[key] = value

            # Convert boolean values to 1/0
            for key, value in ad.items():
                if isinstance(value, bool):
                    record[key] = 1 if value else 0

            # Join text arrays with line breaks
            for field in divide_fields:
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
            for nested_field in ['estimated_audience_size', 'impressions', 'spend']:
                if nested_field in ad and isinstance(ad[nested_field], dict):
                    for sub_key, sub_value in ad[nested_field].items():
                        record[f"{nested_field}_{sub_key}"] = sub_value

            # Create platform columns with 0/1 values
            ad_platforms = ad.get('publisher_platforms', [])
            for platform in platforms:
                record[f"platform_{platform}"] = 1 if platform in ad_platforms else 0

            # Process candidates and build full names
            candidates = ad.get('candidates', [])
            candidate_full_names = []

            if candidates is None:
                candidates = []
            if not candidates:
                str_keywords = record.get('keywords', '')
                keywords = str_keywords.split('\n') if str_keywords else []
                for keyword in keywords:
                    keyword = keyword.strip()
                    std_name = self.find_name(keyword, forced=False)
                    if std_name:
                        candidate_full_names.append(std_name)

            try:
                for candidate in candidates:
                    pass
            except TypeError:
                print(f"Error processing candidates for ad: {ad}")
                continue

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
                    std_name = self.find_name(full_name)
                    candidate_full_names.append(std_name)

            # Add candidate count
            record['quantity'] = len(candidates)
            if len(candidates) > 1:
                spend_lower_bound = record.get('spend_lower_bound', 0)
                spend_upper_bound = record.get('spend_upper_bound', 0)
                spend_lower_bound = int(spend_lower_bound)
                spend_upper_bound = int(spend_upper_bound)
                record['spend_lower'] = spend_lower_bound / len(candidates)
                record['spend_upper'] = spend_upper_bound / len(candidates)
            else:
                record['spend_lower'] = record['spend_lower_bound']
                record['spend_upper'] = record['spend_upper_bound']

            # For File 1: Add all candidates in one column with line breaks
            record['candidates_full_names'] = '\n'.join(candidate_full_names)

            # Add to File 1 records
            file1_records.append(record)

            # For File 2: Create one record per candidate
            if candidate_full_names:
                unique_candidates = set(candidate_full_names)
                for candidate_name in unique_candidates:
                    candidate_record = record.copy()
                    candidate_record['candidate'] = candidate_name
                    # Remove the combined candidates field
                    if 'candidates_full_names' in candidate_record:
                        del candidate_record['candidates_full_names']

                    file2_records.append(candidate_record)
            else:
                # Handle case with no candidates
                candidate_record = record.copy()
                candidate_record['candidate'] = ''
                if 'candidates_full_names' in candidate_record:
                    del candidate_record['candidates_full_names']

                file2_records.append(candidate_record)

        # Create DataFrames
        df1 = pd.DataFrame(file1_records)
        df2 = pd.DataFrame(file2_records)

        return df1, df2


    def export_to_excel(self, df1, df2, output_dir='.'):
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

        # Export to Excel
        file1_path = os.path.join(output_dir, 'meta_ads_file1.xlsx')
        file2_path = os.path.join(output_dir, 'meta_ads_file2.xlsx')

        df1.to_excel(file1_path, index=False)
        df2.to_excel(file2_path, index=False)

        print(f"File 1 exported to {file1_path} with {len(df1)} records")
        print(f"File 2 exported to {file2_path} with {len(df2)} records")
