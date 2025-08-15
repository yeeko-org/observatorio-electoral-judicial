import logging
import requests
from datetime import datetime, timedelta


class SendWhatsappMessage:

    def __init__(
            self, template_name: str,
            has_first_name:bool = False, limit_hours=48,
            language="es_MX", is_test=False, contacts=None,
            resource_v1_id="7jwlhced83ba0e9a445d399e5b169e895d4ad",
            resource_v2_id="g18dzef93a3ed548c480db3da0922d96faef9",
            find_text:str | None = None,
    ):
        """
        :param template_name (str): Name of the WhatsApp template to use
        :param has_first_name (bool): If True, includes first name in the message
        :param limit_hours: Number of hours to limit the records (default is 48)
        :param language: Language code for the message (default is "es_MX")
        :param is_test: If True, only returns the records without sending messages
        :param contacts: List of contacts to process (optional)
        :param resource_v1_id: Resource ID for the first Zoho sheet
        :param resource_v2_id: Resource ID for the second Zoho sheet
        :param find_text: Text to find in the message body (optional)
        """
        self.ready_phones = set()
        self.report_sent = {}
        self.sent_records = []
        self.last_sent = None
        self.ready_template = set()
        self.template_name = template_name
        self.has_first_name = has_first_name
        self.limit_hours = limit_hours
        self.language = language
        self.is_test = is_test
        self.skip_review = is_test
        self.contacts = contacts if contacts else []
        self.resource_v1_id = resource_v1_id
        self.resource_v2_id = resource_v2_id
        logging.basicConfig(level=logging.INFO)

    def send_many(self):
        """
        :return: List of records processed
        """
        import time
        self.ready_phones = set()
        real_records = self.get_sheet_data()
        if not self.contacts:
            self.contacts = []

        # for response_id, collector_id, first_name, phone_id in real_records:
        print(f"Total records to process: {len(real_records)}")
        self.sent_records = []
        self.get_conversations_by_number()

        for record in real_records:
            response_id = record.get("Response ID")
            collector_id = record.get("collector_id", "")
            if not collector_id:
                raise ValueError("Collector ID is missing in the record")
            first_name = record.get("Nombre")
            phone_id = record.get("phone_id", "")

            phone_id = phone_id.strip()
            if phone_id in self.report_sent:
                start_time = record.get("start_time", "")
                if start_time:
                    # convert date to string in format "DD/MM/YYYY HH:MM:SS"
                    start_time = start_time.strftime("%d/%m/%Y %I:%M:%S %p")
                self.report_sent[phone_id]["start_time"] = start_time
            if phone_id in self.ready_phones:
                logging.info(f"Skipping {phone_id} as it is already sent")
                continue
            if len(phone_id) != 10:
                logging.error(f"Invalid phone number {phone_id} for {first_name}")
                continue
            if phone_id in self.ready_template:
                logging.info(f"Skipping {phone_id} as it already has the template")
                continue
            if not self.is_test or not self.skip_review:
                has_last_message = self.get_conversations_by_number(phone_id)
                if has_last_message:
                    logging.info(f"Skipping {phone_id} as it already has a conversation from June 29")
                    continue
            self.ready_phones.add(phone_id)
            self.sent_records.append(record)
            if self.is_test:
                continue
            result = self.send_message_whatsapp(
                response_id=response_id,
                first_name=first_name,
                collector_id=collector_id,
                phone_id=phone_id,
            )
            if not result:
                logging.error(f"Failed to send message to {phone_id}")
                continue
            time.sleep(2)  # Sleep to avoid hitting API rate limits
            print(f"Message sent: {result} to {phone_id}")
        print(f"Total messages sent: {len(self.sent_records)}")
        return self.sent_records

    def get_sheet_data(self):
        # Parameters for the API request

        # Get OAuth token
        complete_phones = set()
        token_url = "https://accounts.zoho.com/oauth/v2/token"
        token_params = {
            "grant_type": "refresh_token",
            "client_id": "1000.FXECGGK3QSZ1WJQTVD0VX8EVO8TO5W",
            "client_secret": "185f87269dbce5cca72c655839e07326b5a767fa8f",
            "refresh_token": "1000.58182bc94a41ecbf123f81686821e2ef.62b36b95ccfb221d0417a57bdb2e8780"
        }

        response_token = requests.post(token_url, data=token_params)
        response_token_data = response_token.json()

        access_token = response_token_data.get("access_token")
        new_token = f"Zoho-oauthtoken {access_token}"

        # Headers for API requests
        headers = {
            "Authorization": new_token
        }
        param_map = {
            'method': 'worksheet.records.fetch',
            'worksheet_name': 'Sheet1',
            'header_row': 1,
            # 'criteria': '("¿Ya subió el video/nota de voz?"="No" or "¿Ya subió el video/nota de voz?"="")',
            'column_names': 'Nombre,Response ID,Response start time,'
                            '¿Ya subió el video/nota de voz?,'
                            '¿Cuál es tu número de teléfono celular '
                            '(10 dígitos)?Incluye un número de celular donde '
                            'podamos comunicarnos contigo (preferiblemente con '
                            'WhatsApp). Esto nos permitirá contactarte '
                            'rápidamente si resultas seleccionadx.',
            'records_start_index': 1
        }

        # Fetch records from first resource
        response_v1 = requests.post(
            f"https://sheet.zoho.com/api/v2/{self.resource_v1_id}",
            data=param_map,
            headers=headers
        )
        records_v1 = response_v1.json().get("records", [])
        all_records = []
        for record in records_v1:
            record["collector_id"] = "ePB12q"
            all_records.append(record)

        # Fetch records from second resource
        response_v2 = requests.post(
            f"https://sheet.zoho.com/api/v2/{self.resource_v2_id}",
            data=param_map,
            headers=headers
        )
        records_v2 = response_v2.json().get("records", [])
        for record in records_v2:
            record["collector_id"] = "2CB1D7"
            all_records.append(record)
        logging.info(f"Total records fetched: {len(all_records)}")

        # Calculate time 48 hours ago
        current_time = datetime.now()
        hours_ago = current_time - timedelta(hours=self.limit_hours)

        real_records = []

        for record in all_records:
            response_id = record.get("Response ID")
            start_time_str = record.get("Response start time")
            already_video = record.get("¿Ya subió el video/nota de voz?")
            # if already_video and already_video.lower() == "sí":
            #     pass
            # else:
            #     continue

            # Check phone number length
            phone_key = "¿Cuál es tu número de teléfono celular (10 dígitos)?Incluye un número de celular donde podamos comunicarnos contigo (preferiblemente con WhatsApp). Esto nos permitirá contactarte rápidamente si resultas seleccionadx."
            phone_id = record.get(phone_key, 0)
            if isinstance(phone_id, float):
                phone_id = str(int(phone_id))
            elif isinstance(phone_id, int):
                phone_id = str(phone_id)
            else:
                print(f"Unexpected phone number type: {type(phone_id)} for record {response_id}")
                continue

            if already_video and already_video.lower() == "sí":
                self.ready_phones.add(phone_id)
                complete_phones.add(phone_id)
                continue


            try:
                start_time = datetime.strptime(start_time_str, "%d/%m/%Y %I:%M:%S %p")
            except ValueError:
                try:
                    # Alternative format without AM/PM
                    start_time = datetime.strptime(start_time_str, "%d/%m/%Y %H:%M:%S")
                except ValueError:
                    print(f"Could not parse date: {start_time_str}")
                    continue
            record["start_time"] = start_time
            # Skip records within 48 hours
            if start_time >= hours_ago:
                print(f"Skipping {phone_id} - Start time within 48 hours: {start_time_str}")
                continue

            if len(phone_id) != 10:
                if len(phone_id) == 12 and phone_id.startswith("52"):
                    phone_id = phone_id[2:]
                else:
                    print(f"Número que no tiene extensión de 10: {phone_id}")
                    continue
            record["phone_id"] = phone_id

            real_records.append(record)

        logging.info(f"Full complete phones: {len(complete_phones)}")
        sorted_records = sorted(
            real_records,
            key=lambda x: x.get("start_time", datetime.min),
            reverse=True
        )

        return sorted_records

    def send_message_whatsapp(
            self, response_id, first_name, collector_id, phone_id,
    ):
        """
        Send WhatsApp template message via Bird API

        Args:
            response_id (str): Unique response identifier
            first_name (str | None): First name of the recipient (optional)
            collector_id (str): Survey collector ID
            phone_id (str): Phone number without country code

        Returns:
            bool: True if message sent successfully, False otherwise
        """

        # API configuration
        bird_api_url = "https://api.bird.com/workspaces/"
        workspace_id = "681feda3-19e0-47ac-b1d4-01c51fb334fb"
        channel_id = "d8de810b-6148-4071-8d43-40f3585ec758"
        full_url = f"{bird_api_url}{workspace_id}/channels/{channel_id}/messages"
        api_key = "7yJXDCumXcfKxNdFAmEjlfwhbVwtiSZpGOo5"

        # Format phone number
        phone_number = f"+52{phone_id}"

        # Create survey link
        full_link = f"https://survey.zohopublic.com/zs/{collector_id}?zs_save_uniqueid={response_id}"
        params = { "form_link": full_link }
        if self.has_first_name:
            params["first_name"] = first_name

        # Create payload
        payload = {
            "receiver": {
                "contacts": [
                    {
                        "identifierValue": phone_number
                    }
                ]
            },
            "template": {
                "name": self.template_name,
                "locale": self.language,
                "variables": params
            }
        }

        # Set headers
        headers = {
            "Authorization": f"AccessKey {api_key}",
            "Content-Type": "application/json"
        }

        # Log the payload
        # logging.info(f"Content sent: {json.dumps(payload, indent=2)}")

        try:
            # Make the API call
            response = requests.post(
                url=full_url,
                json=payload,
                headers=headers
            )
            # Check if request was successful
            response.raise_for_status()

            # logging.info(f"WhatsApp message sent successfully: {response.text}")
            return True

        except requests.exceptions.RequestException as e:
            logging.error(f"Error sending WhatsApp message: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            return False

    def get_conversations_by_number(self, phone_number=None):
        bird_api_url = "https://api.bird.com/workspaces/"
        workspace_id = "681feda3-19e0-47ac-b1d4-01c51fb334fb"
        channel_id = "d8de810b-6148-4071-8d43-40f3585ec758"
        full_url = f"{bird_api_url}{workspace_id}/channels/{channel_id}/messages"
        api_key = "7yJXDCumXcfKxNdFAmEjlfwhbVwtiSZpGOo5"
        headers = {
            "Authorization": f"AccessKey {api_key}",
            "Content-Type": "application/json"
        }
        start_at = datetime.now() - timedelta(days=6)
        end_at = datetime.now()
        if phone_number:
            final_phone_number = f"+52{phone_number.strip()}"
            query_params = {
                "limit": 40,
                "direction": "outgoing",
                "to": final_phone_number,
                # "status": ["sent", "delivered"],
                "startAt": start_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "endAt": end_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            }
        else:
            query_params = {
                "limit": 1000,
                "direction": "outgoing",
            }
        response = requests.get(
            url=full_url,
            headers=headers,
            params=query_params
        )
        full_response = response.json()
        results = full_response.get("results", [])
        has_text = False
        for result in results:
            current_has_text = self.set_report_sent(result, phone_number)
            if current_has_text:
                has_text = True
            # body = result.get("body", {})
            # image = body.get("image", {})
            # text = image.get("text", "")
            # if find_text in text:
            #     has_text = True
        return has_text

    def set_report_sent(self, result, phone_number=None):
        """
        Set the report of sent messages
        :param result: Result from the API call
        :param phone_number: Phone number to set the report for
        """
        has_text = False
        template_name = result.get("template", {}).get("name", "")
        if not template_name:
            return False
        if phone_number:
            self.report_sent[phone_number] = {}
        else:
            phone = result.get("receiver", {}).get("contacts", [{ }])[0] \
                .get("identifierValue", "")
            phone_number = phone.replace("+52", "").strip()
            self.report_sent.setdefault(phone_number, {})
        is_success = result.get("status", "") in ["sent", "delivered"]
        if template_name == self.template_name and is_success:
            self.ready_template.add(phone_number)
            has_text = True
        self.report_sent[phone_number].setdefault(
            template_name, {
                "success_count": 0,
                "fail_count": 0,
            })
        field = "success_count" if is_success else "fail_count"
        self.report_sent[phone_number][template_name][field] += 1
        return has_text

    def build_report(self, get_again=False):
        """
        Build a report of sent messages
        :return: Dictionary with phone numbers as keys and their message details
        """
        full_failed_records = {}
        report = self.report_sent
        for record in self.sent_records:
            new_record = {
                "nombre": record['Nombre'],
                "phone_id": record['phone_id'],
                "collector_id": record['collector_id'],
                "response_id": record['Response ID'],
            }
            phone_id = record['phone_id']
            templates_data = report.get(phone_id, {})
            some_success = False
            for template, counts in templates_data.items():
                if template == 'start_time':
                    continue
                if counts.get('success_count', 0) > 0:
                    some_success = True
            if get_again and not some_success:
                self.get_conversations_by_number(phone_id)
            if get_again:
                continue
            start_time = templates_data.get('start_time', None)
            new_record['start_time'] = start_time
            new_record['some_success'] = some_success
            new_record['templates'] = templates_data
            full_failed_records[phone_id] = new_record
        return full_failed_records


class SentBirdReport:
    bird_api_url = "https://api.bird.com/workspaces/"
    workspace_id = "681feda3-19e0-47ac-b1d4-01c51fb334fb"
    channel_id = "d8de810b-6148-4071-8d43-40f3585ec758"

    def __init__(self, total_days=30):
        self.report_sent = []
        self.total_days = total_days
        self.base_url = f"{self.bird_api_url}{self.workspace_id}/channels/{self.channel_id}/messages"

    def __call__(self):
        self.get_each_five_days(total_days=self.total_days)
        self.save_report_in_csv(file_path="fixture/bird_report.csv")

    def get_each_five_days(self, total_days=30):
        """
        Get conversations from Bird API for the last 'total_days' days.
        Getting conversations in batches of 5 days starts from recent to older.
        :return: List of conversations
        """
        print (f"Fetching conversations for the last {total_days} days")
        # raise ValueError("Total days must be a positive integer")

        current_end = datetime.now()
        days_processed = 0

        while days_processed < total_days:
            days_to_fetch = min(5, total_days - days_processed)
            current_start = current_end - timedelta(days=days_to_fetch)

            print(f"Fetching conversations from {current_start} to {current_end}")
            self.get_conversations_by_dates(current_start, current_end)

            current_end = current_start
            days_processed += days_to_fetch

    def get_conversations_by_dates(self, start_at, end_at, page_token=None):

        api_key = "7yJXDCumXcfKxNdFAmEjlfwhbVwtiSZpGOo5"
        headers = {
            "Authorization": f"AccessKey {api_key}",
            "Content-Type": "application/json"
        }
        full_url = self.base_url
        if page_token:
            full_url += f"?pageToken={page_token}"
        query_params = {
            "limit": 1000,
            "direction": "outgoing",
            "startAt": start_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "endAt": end_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }
        response = requests.get(
            url=full_url,
            headers=headers,
            params=query_params
        )
        full_response = response.json()
        results = full_response.get("results", [])
        for result in results:
            self.add_to_report(result)
        if next_pageToken := full_response.get("nextPageToken"):
            print(f"Next page token: {next_pageToken}")
            self.get_conversations_by_dates(start_at, end_at, next_pageToken)

    def add_to_report(self, result):
        """
        La tabla debe tener:
        id del envío
        número de teléfono,
        el nombre del template,
        la fecha de envío
        Status del envío (éxito o error)
        """
        template_name = result.get("template", {}).get("name", "")
        if not template_name:
            return
        phone = result.get("receiver", {}). \
            get("contacts", [{ }])[0].get("identifierValue", "")
        phone = phone.replace("+521", "").strip()
        phone = phone.replace("+52", "").strip()
        is_success = result.get("status", "") in ["sent", "delivered"]
        self.report_sent.append({
            "id": result.get("id"),
            "phone": phone,
            "template": template_name,
            "date": result.get("createdAt"),
            "status": "Éxito" if is_success else "Error"
        })

    def save_report_in_csv(self, file_path="fixture/bird_report.csv"):
        import csv
        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["ID", "Número de Teléfono", "Template", "Fecha de Envío", "Status"])
            for record in self.report_sent:
                writer.writerow([
                    record["id"],
                    record["phone"],
                    record["template"],
                    record["date"],
                    record["status"]
                ])
        print(f"Report saved to {file_path}")
