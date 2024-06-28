import json
from bs4 import BeautifulSoup
import re
import hashlib
import requests
import os
import shutil
from retrying import retry
from datetime import datetime

base_json= {
    'id':"",
    'seq': "",
    'url': "",
    'type': "",
    'title': "",
    'text_orig': "",
    'title_type_text_to_embed': "",
    'title_type_to_embed' : "",
    'thumbnail': "",
    'subfamily': "",
}

name_len = {
    "url" : "",
    "len" : "",
    "type" : ""
}

max_len = 0

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def generate_hash(url, seq, j_type):
    combined_str = f"{url}_{j_type}_{seq}"
    return url+"!"+ hashlib.sha256(combined_str.encode()).hexdigest()

def extract_general_fields(soup):
    title_tag = soup.find('title')
    title = title_tag.get_text(strip=True).split("|")[0].strip() if title_tag else 'No Title Found'
    base_json['title'] = title

    thumbnail_tag = soup.find('div', class_='easyzoom easyzoom--overlay')
    thumbnail = thumbnail_tag.find('a')['href'] if thumbnail_tag else 'No Thumbnail Found'
    base_json['thumbnail'] = thumbnail

    url_tag = soup.find('meta', property='og:site_name')
    url = url_tag['content'] if url_tag else 'No URL Found'
    base_json['url'] = url

    meta_tags = soup.find_all('meta', attrs={'name': 'product_line'})

    if meta_tags:
        product_line = meta_tags[0]['content']
        base_json["subfamily"] = product_line.split("^")[3]
    else:
        base_json.pop('subfamily', None)

def extract_key_specs(soup):

    key_specs_json = base_json.copy()

    key_specs_section = soup.find('p', class_='highlight')
    key_specs = []
    text_orig = ""
    
    if key_specs_section:
        key_specs_container = key_specs_section.find_next('div', class_='top-three')
        
        for dl in key_specs_container.find_all('dl', class_='top-specifications__list'):
            spec_name = dl.find('dt').get_text(strip=True)
            spec_value_us = dl.find('dd', class_='unit-us').get_text(strip=True)
            spec_value_metric = dl.find('dd', class_='unit-metric').get_text(strip=True)
            spec_text = f"{spec_name}: {spec_value_us} / {spec_value_metric}"
            key_specs.append(spec_text)
            text_orig += spec_text + " \n "

    j_type = "key spec"

    title_type_text_to_embed = f"{base_json['title']} {j_type}: {text_orig.strip()}"
   
    key_specs_json['seq'] = -1
    key_specs_json['text_orig'] = text_orig.strip()
    key_specs_json['title_type_text_to_embed'] = title_type_text_to_embed
    key_specs_json['title_type_to_embed'] = base_json['title'] + " " + j_type

    global max_len
    if len(title_type_text_to_embed) > max_len:
        max_len = len(title_type_text_to_embed) 
        name_len["url"] = base_json['url']
        name_len['len'] = max_len
        name_len['type'] = j_type
    key_specs_json['type'] = j_type
    key_specs_json['id'] = generate_hash(key_specs_json['url'],key_specs_json['seq'],key_specs_json['type'])
    
    if not key_specs_json["text_orig"]:
        key_specs_json = {}
    
    return [key_specs_json]

def extract_overview(soup):
    overview_json = base_json.copy()

    overview_sections = [div for div in soup.find_all('div', class_='pdp-overview__wrapper') if 'pdp-overview__wrapper' in div['class'] and len(div['class']) == 1]
    overview_text = ""
    
    for section in overview_sections:
        for tag in section.find_all(['h3', 'h2', 'h4', 'p']):
            overview_text += tag.get_text(strip=True) + " \n "

    j_type = "overview"

    title_type_text_to_embed = f"{overview_json['title']} {j_type}: {overview_text.strip()}"

    overview_json['seq'] = -1
    overview_json['text_orig'] = overview_text.strip()
    overview_json['title_type_text_to_embed'] = title_type_text_to_embed
    global max_len
    if len(title_type_text_to_embed) > max_len:
        max_len = len(title_type_text_to_embed) 
        name_len["url"] = base_json['url']
        name_len['len'] = max_len
        name_len['type'] = j_type
    overview_json['type'] = j_type
    overview_json['id'] = generate_hash(overview_json['url'],overview_json['seq'],overview_json['type'])
    overview_json['title_type_to_embed'] = base_json['title'] + " " + j_type
 
    if not overview_json['text_orig']:
        overview_json = {}

    return [overview_json]

def extract_benefits(soup):
    benefits_json_list = []
    
    benefit_sections = soup.find_all('div', class_='pdp-usp__wrapper__item')
    g_seq = 0

    for seq, section in enumerate(benefit_sections):
        
        benefit_json = base_json.copy()
        
        benefit_title_tag = section.find('h4')
        benefit_description_tag = section.find('p')
        
        if benefit_title_tag:
            benefit_title = benefit_title_tag.get_text(strip=True)
            benefit_title = clean_text(benefit_title)
        else:
            benefit_title = ""
        
        if benefit_description_tag:
            benefit_description = benefit_description_tag.get_text(strip=True)
        else:
            benefit_description = ""
        
        j_type = "benefit"
        
        text_orig = f"{benefit_title} \n {benefit_description}"
        title_type_text_to_embed = f"{benefit_json['title']} {j_type}: {text_orig}"
        
        benefit_json['seq'] = seq
        benefit_json['text_orig'] = text_orig.strip()
        benefit_json['title_type_text_to_embed'] = title_type_text_to_embed
        global max_len
        if len(title_type_text_to_embed) > max_len:
            max_len = len(title_type_text_to_embed) 
            name_len["url"] = base_json['url']
            name_len['len'] = max_len
            name_len['type'] = j_type
        benefit_json['type'] = j_type
        benefit_json['id'] = generate_hash(benefit_json['url'], benefit_json['seq'], benefit_json['type'])
        benefit_json['title_type_to_embed'] = base_json['title'] + " " + j_type
        
        benefits_json_list.append(benefit_json)

        g_seq+=1
    

    if g_seq == 1:
        benefits_json_list[0]['seq'] = -1

    return benefits_json_list

def extract_features(soup):
    features_json_list = []
    seq = 0
    
    feature_sections = soup.find_all('div', class_='benefits-features--content')
    
    for section in feature_sections:
        controls = section.find_all('div', class_='benefits-features--accordion-control')
        contents = section.find_all('div', class_='benefits-features--accordion-content')
        
        for control, content in zip(controls, contents):
            feature_json = base_json.copy()
            
            feature_title = control.find('span', class_='acc-header').get_text(strip=True)
            
            feature_points = []
            additional_texts = []
            
            for li in content.find_all('li'):
                feature_points.append(li.get_text(strip=True))
            
            for div in content.find_all('div', recursive=False):
                for text in div.find_all(string=True, recursive=False):
                    if text.strip():
                        feature_points.append(text.strip())
                     
            feature_description = " \n ".join(feature_points + additional_texts).strip()
            
            j_type = "feature"
            
            text_orig = f"{feature_title} \n {feature_description}".strip()
            title_type_text_to_embed = f"{feature_json['title']} {j_type}: {text_orig}".strip()
            
            feature_json['seq'] = seq
            feature_json['text_orig'] = text_orig.strip()
            feature_json['title_type_text_to_embed'] = title_type_text_to_embed
            global max_len
            if len(title_type_text_to_embed) > max_len:
                max_len = len(title_type_text_to_embed) 
                name_len["url"] = base_json['url']
                name_len['len'] = max_len
                name_len['type'] = j_type
            feature_json['type'] = j_type
            feature_json['id'] = generate_hash(feature_json['url'], feature_json['seq'], feature_json['type'])
            feature_json['title_type_to_embed'] = base_json['title'] + " " + j_type
            
            features_json_list.append(feature_json)
            
            seq += 1

        if seq == 1:
            features_json_list[0]['seq'] = -1
    
    return features_json_list

def extract_individual_specs(soup):
    specs_json_list = []
    seq = 0
    
    headers = soup.find_all('h3', class_='accordion__heading_download')
    
    for header in headers:
        section_title = header.get_text(strip=True)
        section_content = header.find_next_sibling('div', class_='accordion__body_download')
        
        if section_content:
            rows = section_content.find_all('tr')
            body_content = ""
            
            for row in rows:
                spec_name = row.find('td').find('strong').get_text(strip=True)
                us_unit = row.find('span', class_='unit-us').get_text(strip=True)
                metric_unit = row.find('span', class_='unit-metric').get_text(strip=True)
                
                body_content += f"{spec_name}: {us_unit} / {metric_unit} \n"
            
            spec_json = base_json.copy()
            j_type = "product specification"
            
            text_orig = f"{section_title} \n {body_content.strip()}"
            title_type_text_to_embed = f"{base_json['title']} {j_type}: {text_orig}"
            
            spec_json['seq'] = seq
            spec_json['text_orig'] = text_orig.strip()
            spec_json['title_type_text_to_embed'] = title_type_text_to_embed
            global max_len
            if len(title_type_text_to_embed) > max_len:
                max_len = len(title_type_text_to_embed) 
                name_len["url"] = base_json['url']
                name_len['len'] = max_len
                name_len['type'] = j_type
            spec_json['type'] = j_type
            spec_json['id'] = generate_hash(spec_json['url'], spec_json['seq'], spec_json['type'])
            spec_json['title_type_to_embed'] = base_json['title'] + " " + j_type
            
            specs_json_list.append(spec_json)
            seq += 1
            
    if seq == 1:
        specs_json_list[0]['seq'] = -1
    
    return specs_json_list

def extract_equipment(soup, optional=False):
    equipment_json_list = []
    seq = 0  

    standard_equipment_section = soup.find_all('div', class_='pdp-tab__content_download')

    global max_len
    if len(standard_equipment_section) < 2:
        return equipment_json_list

    if optional and len(standard_equipment_section) < 3:
        return equipment_json_list

    standard_equipment_section = standard_equipment_section[2] if optional else standard_equipment_section[1]
    j_type = "optional equipment" if optional else "standard equipment"

    if not standard_equipment_section:
        return equipment_json_list

    standard_equipment_section = standard_equipment_section.find('div', class_="col-lg-12")
    main_title_element = standard_equipment_section.find('h2')
    main_title = main_title_element.get_text(strip=True) if main_title_element else "N/A"

    elements = standard_equipment_section.find_all(['h4', 'ul'])

    current_h4_title = None
    temp_body_content = []

    for element in elements:
        if element.name == 'h4':
            if current_h4_title and temp_body_content:
                equipment_json = base_json.copy()

                text_orig = " \n ".join(temp_body_content)
                text_orig = f"{current_h4_title} \n {text_orig}"
                title_type_text_to_embed = f"{equipment_json['title']} {j_type}: {text_orig}"

                equipment_json.update({
                    'seq': seq,
                    'text_orig': text_orig,
                    'title_type_text_to_embed': title_type_text_to_embed,
                    'title_type_to_embed' : base_json['title'] + " " + j_type,
                    'type': j_type,
                    'id': generate_hash(equipment_json['url'], seq, j_type)
                })

                global max_len
                if len(title_type_text_to_embed) > max_len:
                    max_len = len(title_type_text_to_embed) 
                    name_len["url"] = base_json['url']
                    name_len['len'] = max_len
                    name_len['type'] = j_type

                equipment_json_list.append(equipment_json)
                seq += 1

            current_h4_title = element.get_text(strip=True)
            temp_body_content = []
        elif element.name == 'ul':
            lis = element.find_all('li')
            for li in lis:
                temp_body_content.append(li.get_text(strip=True))

    if current_h4_title and temp_body_content:
        equipment_json = base_json.copy()
        text_orig = " \n ".join(temp_body_content)
        text_orig = f"{current_h4_title} \n {text_orig}"
        title_type_text_to_embed = f"{equipment_json['title']} {j_type}: {text_orig}"

        equipment_json.update({
            'seq': seq,
            'text_orig': text_orig,
            'title_type_text_to_embed': title_type_text_to_embed,
            'title_type_to_embed' : base_json['title'] + " " + j_type,
            'type': j_type,
            'id': generate_hash(equipment_json['url'], seq, j_type)
        })

        equipment_json_list.append(equipment_json)
    
    if seq == 1:
        equipment_json_list[0]['seq'] = -1

    return equipment_json_list

def save_features_to_txt(features_json_list, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        for feature_json in features_json_list:
            json_str = json.dumps(feature_json, ensure_ascii=False, indent=4)
            file.write(json_str + ' \n ')

def extract_technologies_and_services(soup):
    technologies_services_list = []
    seq = 0

    tabs = soup.find_all('div', class_='technology-tabs__carousel-item')
    tabNames = []

    for tab in tabs:
        tabName = tab.get_text(strip=True)
        tabNames.append(tabName)


    tech_service_elements = soup.find_all('li', class_='tab__header')

    for element in tech_service_elements:
        
        tabindex = int(element.find_parent('div', class_='technology-tabs__content-item')['id'].split("-")[1]) - 1
        tab_name = tabNames[tabindex]

        title_element = element.find('h4')
        title = title_element.get_text(strip=True) if title_element else "N/A"

        description_element = element.find('div', class_='technology-tabs__content__inner-wrapper').find('p')
        description = description_element.get_text(strip=True) if description_element else "N/A"
        description = f"{tab_name} \n {title} \n {description}"

        technology_service_json = base_json.copy()
        j_type = 'compatible technology/service'
        title_type_text_to_embed = f"{technology_service_json['title']} {j_type}: {description}"

        technology_service_json.update({
            'seq': seq,
            'text_orig': description,
            'title_type_text_to_embed': title_type_text_to_embed,
            'title_type_to_embed' : base_json['title'] + " " + j_type,
            'type': j_type,
            'id': generate_hash(technology_service_json['url'], seq, 'technology/service')
        })

        technologies_services_list.append(technology_service_json)
        seq += 1
    
    if seq == 1:
        technologies_services_list[0]['seq'] = -1

    return technologies_services_list

def extract_related_products(soup):
    related_products_list = []
    seq = 0

    related_product_elements = soup.find_all('article', class_='accordion__item')

    for element in related_product_elements:
        main_title_element = element.find('h2')
        main_title = main_title_element.get_text(strip=True) if main_title_element else "N/A"

        products = []

        product_lists = element.find_all('div', class_='compatible-product-list-accordion')
        
        for product_list in product_lists:
            list_title_element = product_list.find('h3')
            list_title = list_title_element.get_text(strip=True) if list_title_element else "N/A"
            products.append(list_title)

            lis = product_list.find('ul').find_all('li')
            for li in lis:
                product = li.get_text(strip=True)
                products.append(product)

        if products:
            text_orig = " \n ".join(products)
            text_orig = f"{main_title} \n {text_orig}"
            related_product_json = base_json.copy()
            j_type = 'related products'
            title_type_text_to_embed = f"{related_product_json['title']} {j_type}: {text_orig}"

            
            related_product_json.update({
                'seq': seq,
                'text_orig': text_orig,
                'title_type_text_to_embed': title_type_text_to_embed,
                'title_type_to_embed' : base_json['title'] + " " + j_type,
                'type': j_type,
                'id': generate_hash(related_product_json['url'], seq, 'related products')
            })

            related_products_list.append(related_product_json)
            seq += 1

    if seq == 1:
        related_products_list[0]['seq'] = -1

    return related_products_list

def html_to_json(html_file_path):
    txt_name = html_file_path.split("/")[1].split(".")[0]

    with open(html_file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')

    extract_general_fields(soup)

    key_specs_json = extract_key_specs(soup)
    overview_json = extract_overview(soup)
    benefit_list_json = extract_benefits(soup)
    feature_list_json = extract_features(soup)
    spec_list_json = extract_individual_specs(soup)
    standard_equipment_json = extract_equipment(soup)
    optional_equipment_json = extract_equipment(soup,optional=True)
    tech_services_json = extract_technologies_and_services(soup)
    related_products_json = extract_related_products(soup)

    all_jsons = []

    all_jsons.extend(key_specs_json)
    all_jsons.extend(overview_json)
    all_jsons.extend(benefit_list_json)
    all_jsons.extend(feature_list_json)
    all_jsons.extend(spec_list_json)
    all_jsons.extend(standard_equipment_json)
    all_jsons.extend(optional_equipment_json)
    all_jsons.extend(tech_services_json)
    all_jsons.extend(related_products_json)

    save_json(all_jsons)
    print(txt_name)
    #save_features_to_txt(all_jsons, f'jsons/{txt_name}.txt')
    
    #for json in all_jsons:
    #    try:
    #        send_json_with_basic_auth(json)
    #        print(txt_name)
    #    except Exception as e:
    #        print(f"failed document: {html_file_path}")

def file_to_json(filepath):
    with open(filepath, 'r') as file:
        for line in file:
            html = line.strip()
            html = "htmls/"+html
            html_to_json(html)

def save_json(json_info):
    for json_data in json_info:
        if json_data:
            filepath = "3k_files (2)/" + json_data['id'].split("!")[1] + ".json"

            with open(filepath, "w") as file:
                file.write(json.dumps(json_data, indent=4))

@retry(stop_max_attempt_number=3, wait_fixed=5000)
def send_json_with_basic_auth(json_data):

    #url = "https://caterpillares-dev.b.lucidworks.cloud:443/api/apps/P3_Semantic_Search_POC/index/P3_Semantic_Search_POC"
    url = "https://caterpillares-dev.b.lucidworks.cloud:443/api/apps/P3_Semantic_Search_POC/index/P3_Semantic_Search_POC_B"

    username = "josue.vargas@accenture.com"
    password= "josue@LW01"

    headers = {
        "Content-Type": "application/json"
    }

    
    auth = (username, password)
    response = requests.post(url, headers=headers, auth=auth, data=json.dumps(json_data))
    
    if response.status_code == 200:
        pass
    else:
        #print(f"Error sending request: {response.status_code}")
        #print(response.text)
        response.raise_for_status()

def local_to_index(directory_path, start_position=0):
    start_time = datetime.now()
    filenames = sorted(os.listdir(directory_path))
    
    failed_docs = []
    
    for idx, filename in enumerate(filenames):
        if idx < start_position:
            continue
        
        file_path = os.path.join(directory_path, filename)
        
        if filename.endswith('.json') and os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                try:
                    data = json.load(file)
                    send_json_with_basic_auth(data)
                    print(filename)
                except Exception as e:
                    print(f"failed document: {filename}")
                    failed_docs.append(filename)
    
    end_time = datetime.now()
    create_execution_report(len(failed_docs),start_time,end_time,"/reports")
    return failed_docs

#def copy_failed_docs(failed_docs, source_directory, destination_directory):
#    if not os.path.exists(destination_directory):
#        os.makedirs(destination_directory)
#
#    for filename in failed_docs:
#        source_path = os.path.join(source_directory, filename)
#        destination_path = os.path.join(destination_directory, filename)
#        
#        if os.path.isfile(source_path):
#            try:
#                shutil.copy2(source_path, destination_path)
#                print(f"Copied {filename} to {destination_directory}")
#            except Exception as e:
#                print(f"Failed to copy {filename}: {e}")
#        else:
#            print(f"File not found: {filename}")

def save_failed_docs_to_file(failed_docs, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        for doc_id in failed_docs:
            file.write(f"{doc_id}\n")

def create_execution_report(failed_docs_count, start_time, end_time, report_directory):
    total_time = end_time - start_time
    report_filename = f"execution_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
    report_path = os.path.join(report_directory, report_filename)
    
    with open(report_path, 'w', encoding='utf-8') as file:
        file.write(f"Start Time: {start_time}\n")
        file.write(f"End Time: {end_time}\n")
        file.write(f"Total Time: {total_time}\n")
        file.write(f"Failed Document numbers: {failed_docs_count}\n")

    print(f"Execution report saved to {report_path}")


file_to_json("all_htmls.txt") #Pa local
#print(local_to_index("3k_files (2)",29430))

#print(local_to_index("3k_missing"))