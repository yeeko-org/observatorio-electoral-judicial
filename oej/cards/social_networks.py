
class Network:
    network_types = {
        1: ["facebook"],
        2: ["twitter", "x.com"],
        3: ["instagram"],
        4: ["youtube"],
        5: ["tiktok"],
    }
    new_network_types = [
        {
            "id": 7,
            "name": "whatsapp",
            "keywords": ["whatsapp", "wa.link", "wa.me"]
        },
        {
            "id": 8,
            "name": "linkedin",
            "keywords": ["linkedin"]
        },
        {
            "id": 9,
            "name": "threads",
            "keywords": ["threads"]
        },
        {
            "id": 10,
            "name": "linktree",
            "keywords": ["linktr.ee"]
        },
        {
            "id": 11,
            "name": "spotify",
            "keywords": ["spotify"]
        },
        {
            "id": 12,
            "name": "bluesky",
            "keywords": ["bluesky", "bsky"]
        }
    ]

    def __init__(self):
        self.other_networks = []
        for net in self.new_network_types:
            self.other_networks.extend(net["keywords"])

        self.every_keywords = []
        for value1 in self.network_types.values():
            self.every_keywords.extend(value1)

    def identify_real_id(self, social_network):
        tipo = social_network.get("idTipoRed")
        if tipo < 6:
            return tipo
        url = social_network.get("descripcionRed", "").lower()
        for key, value in self.network_types.items():
            if any(keyword in url for keyword in value):
                return key
        for network in self.new_network_types:
            if any(keyword in url for keyword in network["keywords"]):
                return network["id"]
        return 6

    def identify_social_networks(self, file_name):
        import json
        counters = {}
        # with open(file_path, encoding='utf-8') as jsonfile:
        with open(file_name, encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)
        social_networks = data.get("redesSociales", [])
        like_others = 0
        print("Total social networks:", len(social_networks))
        for social_network in social_networks:
            tipo = social_network.get("idTipoRed")
            url = social_network.get("descripcionRed", "").lower()
            real_id = tipo
            if tipo == 6:
                real_id = self.identify_real_id(social_network)
                if real_id == 6:
                    print(f"Other network: {url}")
            counters.setdefault(real_id, 0)
            counters[real_id] += 1
            if tipo == 6:
                continue
            net_type = self.network_types.get(tipo)
            try:
                has_keyword = any(keyword in url for keyword in net_type)
                if not has_keyword:
                    print(f"Network {tipo} not found: {url}")
            except TypeError:
                print(f"net_type is None for tipo {tipo}")
        print(f"Total like_others: {like_others}")
        print("Counters:", counters)

    def save_catalog_social_networks(self):
        from oej.models import SocialNetwork
        if SocialNetwork.objects.exists():
            print("Social networks already exist")
            return
        for network in self.network_types.values():
            first_name = network[0]
            social_network = SocialNetwork(name=first_name.capitalize())
            social_network.icon = f"{first_name}_blanco.png"
            social_network.keywords = network
            social_network.save()
        icons = 0
        SocialNetwork.objects.create(name="Otras redes")
        for network in self.new_network_types:
            name = network["name"]
            name = name.capitalize()
            social_network = SocialNetwork(name=name)
            if icons < 3:
                social_network.icon = f"{name}_blanco.png"
            social_network.keywords = network["keywords"]
            social_network.save()
            icons += 1

    def save_social_networks(self):
        from oej.models import Candidate, SocialNetwork, SocialNetworkAccount
        networks_dict = {
            net.id: net for net in SocialNetwork.objects.all()}
        empty_candidates = Candidate.objects.all()
        for candidate in empty_candidates:
            ine_data = candidate.ine_data or {}
            social_networks = ine_data.get("redesSociales", [])
            for social_account in social_networks:
                net_id = self.identify_real_id(social_account)
                social_network = networks_dict.get(net_id)
                SocialNetworkAccount.objects.get_or_create(
                    candidate=candidate,
                    social_network=social_network,
                    url=social_account.get("descripcionRed"),
                )
            candidate.social_networks = social_networks
            candidate.save()


def main():
    network = Network()
    network.save_catalog_social_networks()
    base_url = "G:\Mi unidad\YEEKO\Proyectos\oej\conoceles_ine"
    network.identify_social_networks(f"{base_url}/magistraturas.json")
    network.save_social_networks()
# identify_social_networks("G:\Mi unidad\YEEKO\Proyectos\oej\conoceles_ine\magistraturas.json")
# identify_social_networks("G:\Mi unidad\YEEKO\Proyectos\oej\conoceles_ine\magistraturas.json")

