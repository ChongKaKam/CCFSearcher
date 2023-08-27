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
    # Domian:
    #   - 01 计算机体系结构/并行与分布计算/存储系统
    #   - 02 计算机网络
    #   - 03 网络与信息安全
    #   - 04 软件工程/系统软件/程序设计语言
    #   - 05 数据库/数据挖掘/内容检索
    #   - 06 计算机图形学与多媒体
    #   - 07 人工智能
    #   - 08 计算机科学理论
    #   - 09 交叉/综合/新兴
    input_str = 'network anomaly detection'
    level = 'AB'
    paper_type = ['conf']
    domain_list = ['02', '03', '05', '09']
    year_range = [2018, 2023]
    # run
    print('run at', datetime.datetime.today().ctime())
    good = PaperSearch('./config.yaml')
    good.search(input_str, level, paper_type, domain_list, year_range)

    