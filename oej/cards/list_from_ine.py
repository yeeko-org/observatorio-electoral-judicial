import camelot
import pandas as pd
import json
import os
import re
from typing import List, Dict, Any


class PDFTableExtractor:
    """Extract tables from PDF and convert to structured data."""

    def __init__(self, pdf_path: str):
        """Initialize the extractor with PDF path."""
        self.pdf_path = pdf_path

        # Define expected column names based on your description
        self.expected_headers = [
            "Poder que postula", "Circuito Judicial", "Especialidad",
            "Nombre", "Sexo", "Circunscripción Plurinominal"
        ]

    def extract_tables(self):
        """Extract all tables from the PDF."""
        # Try lattice mode first (for tables with lines)
        print("Extracting tables in lattice mode...")
        tables = camelot.read_pdf(
            self.pdf_path,
            pages='all',
            flavor='lattice'
        )
        print("len(tables):", len(tables))

        # If that doesn't work well, try stream mode
        if len(tables) == 0:
            tables = camelot.read_pdf(
                self.pdf_path,
                pages='all',
                flavor='stream'
            )

        return tables

    def process_tables(self, tables):
        """Process and combine extracted tables."""
        combined_df = pd.DataFrame()
        last_row = None

        for i, table in enumerate(tables):
            df = table.df

            headers = df.iloc[0].values
            clean_headers = [re.sub(r'\s+', ' ', h) for h in headers]
            clean_headers = [h.replace("\n", " ") for h in clean_headers]
            clean_headers = [h.strip() for h in clean_headers]
            # Handle headers - use first row as headers if it contains
            # expected header names
            some_header_found = any(header in clean_headers
                                    for header in self.expected_headers)
            if i == 0 or some_header_found:
                df = df.iloc[1:].reset_index(drop=True)
                df.columns = clean_headers

            # If this is the first table, use it as our base
            if combined_df.empty:
                combined_df = df
                continue

            # Check if the first row of this table is a continuation
            # of the last row
            first_row = df.iloc[0] if not df.empty else None

            if first_row is None:
                continue

            # Count empty cells to determine if this is likely a continuation
            empty_cells = sum(
                1 for cell in first_row if not cell or cell.strip() == "")

            if empty_cells >= len(first_row) - 2:  # Most cells are empty
                # Merge the non-empty cells with the last row of
                # the previous table
                for col in df.columns:
                    if first_row[col] and first_row[col].strip():
                        last_pos = combined_df.columns.get_loc(col)
                        value = first_row[col]
                        if combined_df.iloc[-1][col]:
                            combined_df.iloc[-1, last_pos] += f" {value}"
                        else:
                            combined_df.iloc[-1, last_pos] = value

                # Append the rest of the rows
                # (skip the first one we just processed)
                if len(df) > 1:
                    combined_df = pd.concat(
                        [combined_df, df.iloc[1:]], ignore_index=True)
            else:
                # Regular append
                combined_df = pd.concat(
                    [combined_df, df], ignore_index=True)

        return combined_df

    def parse_name_components(self, df):
        """Split the name column into first name and last names."""
        if "Nombre" in df.columns:
            # Create new columns for name components if they don't exist
            if "first_last_name" not in df.columns:
                df["first_last_name"] = ""
            if "second_last_name" not in df.columns:
                df["second_last_name"] = ""
            if "first_name" not in df.columns:
                df["first_name"] = ""

            # Process each row
            for idx, row in df.iterrows():
                if pd.notna(row["Nombre"]) and row["Nombre"].strip():
                    # Split the name (based on your example,
                    # it seems to be in format:
                    # LAST_NAME1 LAST_NAME2 FIRST_NAME)
                    name_parts = row["Nombre"].strip().split()

                    if len(name_parts) >= 3:
                        df.at[idx, "first_last_name"] = name_parts[0]
                        df.at[idx, "second_last_name"] = name_parts[1]
                        df.at[idx, "first_name"] = " ".join(name_parts[2:])
                    elif len(name_parts) == 2:
                        df.at[idx, "first_last_name"] = name_parts[0]
                        df.at[idx, "second_last_name"] = name_parts[1]
                        sex = row["Sexo"].strip()
                        if sex not in ["M", "H"]:
                            # The col sex has the first name
                            first_name, real_rex = sex.rsplit(" ", 1)
                            df.at[idx, "first_name"] = first_name
                            df.at[idx, "Sexo"] = real_rex
                    elif len(name_parts) == 1:
                        print("name_parts one", name_parts)
                        df.at[idx, "first_last_name"] = name_parts[0]

        return df

    def clean_dataframe(self, df):
        """Clean the dataframe - handle NaN values, whitespace, etc."""
        # Replace NaN with empty strings
        df = df.fillna("")

        # Clean whitespace from string columns
        for col in df.columns:
            if df[col].dtype == object:  # String columns
                df[col] = df[col].apply(
                    lambda x: x.strip() if isinstance(x, str) else x)

        return df

    def extract_and_process(self):
        """Extract tables from PDF and process them into a clean dataframe."""
        tables = self.extract_tables()
        combined_df = self.process_tables(tables)
        combined_df = self.parse_name_components(combined_df)
        combined_df = self.clean_dataframe(combined_df)
        return combined_df

    def to_json(self, output_file):
        """Extract data and save to JSON file."""
        df = self.extract_and_process()

        # Convert to JSON records
        records = df.to_dict(orient='records')

        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=4)

        print(f"Successfully extracted {len(records)} records to {output_file}")
        return records


# Example usage
# if __name__ == "__main__":
def extract_pdf_data(file_name: str):
    common_path = "G:\Mi unidad\YEEKO\Proyectos\oej\listas"
    pdf_path = os.path.join(common_path, f"{file_name}.pdf")
    output_json = os.path.join(common_path, f"{file_name}.json")
    extractor = PDFTableExtractor(pdf_path)
    data = extractor.to_json(output_json)


# from oej.cards.list_from_ine import extract_pdf_data
# extract_pdf_data("listado_jueces")
# extract_pdf_data("listado_magis")
# extract_pdf_data("magis_superior")
# extract_pdf_data("scjn")
# extract_pdf_data("listado_magis")
# extract_pdf_data("tdj")

