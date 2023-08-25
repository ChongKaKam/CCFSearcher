# import modules
import xml.etree.ElementTree as ET
import requests
import datetime
import yaml
import re
import os
# import files
from output_writer import *
from data_manager import *

class SearchCore:
    def __init__(self, manager:DataManager, output_config: dict) -> None:
        self.manager = manager
        self.output_config = output_config
        self.output = output_writer_factory.create_output_writer(self.output_config)
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