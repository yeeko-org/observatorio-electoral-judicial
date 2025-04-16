

def get_every_ids():
    import requests
    import json


    base_url = "https://bot-gen-fichas.onrender.com/api/v1/consulta"
    start_id = 166
    all_results = []
    while True:
        if start_id > 16000:
            break
        if start_id % 20 == 0:
            print(f"Processing ID: {start_id}")
        response = requests.post(base_url, json={"id": start_id})
        if response.status_code == 200:
            data = response.json()
            first_response = data.get("response")
            if not first_response:
                break
            all_results.append(first_response[0])
            start_id += 1
        else:
            print(f"Error: {response.status_code}")
            break

    # save all_results to a file json
    filename = "fixture/disentir1.json"
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(json.dumps(all_results, indent=4))


