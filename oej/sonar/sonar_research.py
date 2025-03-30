from openai import OpenAI
import json

from django.conf import settings
from oej.models import Candidate


class SonarResearch:

    def __init__(
            self, ai_company="openai",
            engine="sonar-deep-research",
            to_json: bool = False,
    ):
        api_key_name = "OPENAI_API_KEY"
        base_url = None
        match ai_company:
            case "sonar":
                api_key_name = "SONAR_API_KEY"
                base_url = "https://api.perplexity.ai"
            case "deepseek":
                api_key_name = "DEEPSEEK_API_KEY"
                base_url = "https://api.deepseek.com/v1"
            case "openai":
                api_key_name = "OPENAI_API_KEY"
        self.is_openai = ai_company == "openai"
        openai_api_key = getattr(settings, api_key_name, None)

        self.client = OpenAI(api_key=openai_api_key, base_url=base_url)
        self.engine = engine
        self.messages: list[dict] = []
        self.candidate: Candidate | None = None
        self.to_json = to_json
        self.response = None

    def build_prompt(
            self,
            prompt_path: str,
            candidate: Candidate | None = None
    ):
        import re

        self.messages = []
        self.candidate = candidate
        with open(prompt_path, "r", encoding="utf-8") as file:
            user_prompt = file.read()

        all_messages = user_prompt.split("\n====\n")
        for message in all_messages:
            # extract the role and content from the message (role between %)
            # and content after the role
            role = re.search(r"%(\w{2,14}?)%", message)
            if role:
                role = role.group(1).strip()
                content = re.sub(r"%(\w{2,14}?)%", "", message).strip()
                self.build_msg(content, role=role)
            else:
                self.build_msg(message, role="user")

    def send_prompt(self, user_prompt: str | None = None):

        if user_prompt:
            self.build_msg(user_prompt, role="user")
        response_format = {"type": "json_object"} \
            if self.to_json else None
        web_search_options = None
        if self.engine == "sonar-deep-research":
            web_search_options = {
                "search_context_size": "high"
            }

        self.response = self.client.chat.completions.create(
            model=self.engine,
            messages=self.messages,
            web_search_options=web_search_options,
            response_format=response_format,
        )
        final_content = self.clean_content()
        if self.candidate:
            self.get_price()
            self.get_citations()
            self.candidate.gemini_text = final_content
            self.candidate.status_register_id = 'draft'
            self.candidate.save()
        return final_content

    def clean_content(self):
        # Remove all content between <think> tags
        if self.to_json:
            json_response = self.response.choices[0].message.content
            if not json_response:
                return None
            try:
                return json.loads(json_response)
            except Exception as e:
                print(f"Error parsing JSON: {e}")
                return None
        content = self.response.choices[0].message.content
        if self.engine == "sonar-deep-research":
            tags = ["<think>", "</think>"]
            while tags[0] in content:
                start = content.index(tags[0])
                end = content.index(tags[1]) + len(tags[1])
                content = content[:start] + content[end:]
        content = content.strip()
        return content

    def get_citations(self):
        # Extract citations from the response
        citations = self.response.model_extra.get("citations", [])
        self.candidate.sources = citations
        return citations

    def get_price(self):

        def calculate_price(tokens, price_per_million=40):
            return {
                "tokens": tokens,
                "price": price_per_million * tokens / 1_000_000
            }

        usage = self.response.usage
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens
        extra = usage.model_extra
        citations = extra.get("citation_tokens", 0)
        reasoning = extra.get("reasoning_tokens", 0)
        num_search_queries = extra.get("num_search_queries", 0)
        price_details = {
            "input": calculate_price(input_tokens, 40),
            "output": calculate_price(output_tokens, 160),
            "citation": calculate_price(citations, 160),
            "reasoning": calculate_price(reasoning, 60),
            "queries": {
                "num_search_queries": num_search_queries,
                "price": num_search_queries * 0.1,
            },
        }
        total_price = sum([price["price"] for price in price_details.values()])
        print(f"Total price: ${total_price:.2f}")
        self.candidate.price = total_price
        self.candidate.price_details = price_details

    def special_format(self, text):
        if self.candidate:
            candidate_name = self.candidate.full_name_normalized
            text = text.format(
                candidate_name=candidate_name,
                position=self.candidate.position)
        return text

    def build_msg(self, prompt, role="user"):

        if self.to_json and role == "assistant":
            try:
                prompt = json.dumps(json.loads(prompt), ensure_ascii=False)
            except Exception as e:
                print(f"Error converting to json: {e}")
                print("prompt:", prompt)
        prompt = self.special_format(prompt)
        if not self.is_openai:
            content = prompt
        else:
            content = [
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        self.messages.append({
            "role": role,
            "content": content
        })

