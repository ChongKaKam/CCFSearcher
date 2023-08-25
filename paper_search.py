"""
date: 2023.8.23 
author: Chong KaKam
version: 0.1
"""
# import modules
import datetime
import yaml
# import files
from output_writer import *
from data_manager import *
from search_core import *

# class
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

    