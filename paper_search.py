"""
date: 2023.8.23 
author: Chong KaKam
version: 0.1
"""
# import modules
import xml.etree.ElementTree as ET
import requests
import datetime
import yaml
import re
import os
# import files
from output_writer import *

# class:
class DataManager:
    # Initialization
    def __init__(self, root_path:str, file_format:str, data_yaml:str, search_prefix:str) -> None:
        # 1 set root path:
        #   xxx/xxx/
        if root_path[-1]=='/':
            self.root_path = root_path
        else:
            self.root_path = root_path + '/'
        # 2 set format
        self.file_format = file_format
        # 3 read data from a yaml configuration file.
        with open(data_yaml, 'r') as file:
            self.data = yaml.safe_load(file)
        # 4 set search prefix
        self.search_prefix = search_prefix
        self.max_try = 10
        # -- initialization done --
    # Basic operation
    def has_item(self, id:str):
        return id in self.data
    def get_item(self, id:str):
        if self.has_item(id):
            return self.data[id]
        else:
            print('Do not have id:', id)
            return None
    def if_file_exists(self,item:dict, year:int):
        return os.path.exists(self.make_save_path(item, year))
    def if_file_exists(self, save_path:str):
        return os.path.exists(save_path)
    def update(self):
        pass
    # DataManager <-> Web server
    # make the full path accroding to the type of item
    def _full_path(self, item:dict, year:int):
        if item['Type'] == 'journals':
            volume = int(item['Number']) + int(item['Amount'])*(year - int(item['Year']))
            return 'journals/'+item['Path']+str(volume)
        elif item['Type'] == 'conf':
            return 'conf/'+item['Path']+str(year)
        elif item['Type'] == 'conf-journals':
            journal_item = self.get_item(item['Path'])
            volume = int(journal_item['Number']) + int(journal_item['Amount']) * int(year - int(journal_item['Year']))
            return 'journals/'+journal_item['Path'] + str(volume)
        else:
            print("ERROR: unknown type:", item['Type'])
            return None
    # generate a save path: root_path/xxx/xxx/xxx.xml
    def make_save_path(self, item:dict, year:int):
        full_path = self._full_path(item, year)
        return (self.root_path + full_path + '.' + self.file_format)
    # generate a url: https://xxxxx/xxx/xxx
    def make_url(self, item:dict, year:int, h=1000, f=0):
        full_path = self._full_path(item, year)
        return self.search_prefix + full_path + '.bht%3A&h={h}&f={f}&format={format}'.format(h=h, f=f, format=self.file_format)
    # Get file from url and save in save_path, if there is no content, return false.
    def Get_File(self, url:str, save_path:str) -> bool: 
        # if the dir exists
        dir = os.path.dirname(save_path)
        if not os.path.exists(dir): 
            os.makedirs(dir)
        num_try = 0
        while num_try < self.max_try:
            try:
                # download file
                print('Get file from:', url, 'save:', save_path)
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                if response.status_code == 200:
                    xml_content = response.text
                    hits = ET.fromstring(xml_content).find('.//hits')
                    total = int(hits.attrib['total'])
                    if total > 0:
                        with open(save_path, 'w', encoding='utf-8') as file:
                            file.write(xml_content)
                        # print('ok')
                        return True
                    else:
                        print('file from:', url, ' seems to have nothing.')
                        return False
                else:
                    print("error", response.status_code)
                    return False
            except requests.RequestException as e:
                num_try += 1
                print(f"Download error: {e}. Retrying... {num_try}/{self.max_try}")
        print("Failed to download the file after maximum retries.")
        return False
    
    # DataManager <-> Search Engine/User



class SearchCore:
    def __init__(self, manager:DataManager, output_config: dict) -> None:
        self.manager = manager
        self.output_config = output_config
        self.output = output_write_factory.create_output_writer(self.output_config)
        self.type_dict = {'journals': '0', 'conf': '1'}
    # search
    # param:
    #   - input: input keywords
    #   - level: ABC
    #   - domain: 
    #   - year_range: [2018,2023]
    def search(self, input:str, level_list:list, type_list:list ,domain_list:list, year_range:list):
        self.output.write_header(input, level_list, type_list, domain_list, year_range)
        # preparation
        keywords = input.split(' ')
        pattern_str = self.make_pattern(keywords)
        # t_list = []
        # for i in type_list:
        #     if i == 
        id_list = self.generate_id_list(level_list, type_list, domain_list)
        file_list = self.generate_file_list(id_list, year_range)
        # search:
        result = []
        # print(file_list)
        for file_path in file_list:
            result += self.file_search(file_path, pattern_str)
        # output results
        self.output.write(result)
    
    def _make_records(self, type:str, entry) -> dict:
        output_config = self.output_config[type]
        # author_num = self.output_config['author_num']
        record = {}
        for atr in output_config:
            if atr == 'author':
                info = 'info/authors/author'
            else:
                info = 'info/' + atr
            temp = entry.find(info)
            if temp == None: continue
            record[atr] = temp.text
        return record

    # file_search
    def file_search(self, file_path:str, pattern_str: str):
        type = ''
        if 'journals/' in file_path:
            type = 'journals'
        elif 'conf/' in file_path:
            type = 'conf'
        else:
            print("ERROR: unknown path:", file_path)
            return None
        root = ET.parse(file_path).getroot()
        # print(file_path)
        result = []
        for entry in root.findall("./hits/hit"):
            title = entry.find("info/title")
            if self.match_keywords(title.text, pattern_str):
                record = self._make_records(type, entry)
                result.append(record)
        return result
    # generate_file_list:
    def generate_file_list(self, id_list:list, year_range:list):
        f_list = []
        # print('id:', id_list)
        for id in id_list:
            for year in range(year_range[0], year_range[1]+1):
                item = self.manager.get_item(id)
                save_path = self.manager.make_save_path(item, year)
                # if database do not have file, try to update again
                # append save_path to f_list if it successes.
                if not self.manager.if_file_exists(save_path):
                    url = self.manager.make_url(item, year)
                    if self.manager.Get_File(url, save_path):
                        f_list.append(save_path)
                else:
                    f_list.append(save_path)
        return f_list
                

    # generate_id_list:
    def generate_id_list(self, level_list:list, type_list:list, domain_list:list):
        s_list = []
        for level in level_list:
            for domian in domain_list:
                for type in type_list:
                    num = 0
                    while True:
                        id = self.encoder(level, type, domian, num)
                        num += 1
                        # print('id:', id, s_list)
                        if self.manager.has_item(id):
                            s_list.append(id)
                        else:
                            break
        return s_list

    # convert options and number into id number
    def encoder(self, level:str, type:str, domian, num:int):
        if len(level)==1 and level in 'ABC':
            if type == 'journals':
                s_type = '0'
            elif type == 'conf':
                s_type = '1'
            else:
                print('ERROR: unknown type:', type)
                return None
            return level + str(domian).zfill(2) + s_type + str(num).zfill(2)
        else:
            print('ERROR: unknown level:', level)
            return None
    
    # make a pattern_str and compile
    def make_pattern(self, keywords:list):
        pattern_str = ".*".join(map(re.escape, keywords))
        return pattern_str
    
    # match
    # param:
    #   - text
    #   - pattern_str 
    # return: bool
    def match_keywords(self, text:str, pattern_str:str) -> bool:
        match = re.search(f"(?i){pattern_str}", text)
        return bool(match)
    
class PaperSearch:
    def __init__(self, config_yaml:str) -> None:
        with open(config_yaml, 'r') as file:
            self.config = yaml.safe_load(file)
        self.datamanager = DataManager(
            self.config['basic_config']['root_path'],
            self.config['basic_config']['file_format'],
            self.config['basic_config']['data_yaml'],
            self.config['basic_config']['search_prefix']
            )
        self.searchcore = SearchCore(
            self.datamanager, 
            self.config['output_config']
            )
    def search(self, input:str, level_list:list, type_list:list ,domain_list:list, year_range:list):
        self.searchcore.search(input, level_list, type_list, domain_list, year_range)
        print('results are shown in', self.searchcore.output.output_path)

if __name__=='__main__':
    print('run at', datetime.datetime.today().ctime())
    good = PaperSearch('./config.yaml')
    good.search('network anomaly detection ', 'A', ['conf'], ['02','03','05','09'], [2020,2023])

    