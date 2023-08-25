# import modules
from abc import ABC, abstractmethod
import datetime
import os

# class
class output_writer(ABC):
    def __init__(self, output_config:dict) -> None:
        super().__init__()
        self.output_config = output_config
        output_path = output_config['output_path']
        if output_path[-1]=='/':
            self.output_path = output_path
        else:
            self.output_path = output_path+'/'
        # print('PATH:',self.output_path)
        if not os.path.exists(self.output_path): 
            os.makedirs(self.output_path) 
        
        now = datetime.datetime.today()
        self.output_path += 'output_{month}_{day}_{hour}_{minute}.md'.format(month=now.month, day=now.day, hour=now.hour, minute=now.minute)
        self.file = open(self.output_path, 'w')
    def write_header(self, input:str, level_list:list, type_list:list ,domain_list:list, year_range:list):
        self.file.write('# output file\n')
        self.file.write('Time: '+datetime.datetime.today().ctime()+'\n')
        self.file.write('Input: '+input+'\n')
        self.file.write('Level_list: '+str(level_list)+'\n')
        self.file.write('Type_list: '+str(type_list)+'\n')
        self.file.write('Domian_list: '+str(domain_list)+'\n')
        self.file.write('Year_range: '+str(year_range)+'\n')
        self.file.write('  \n\n')
        self.file.flush()

    # @abstractmethod
    def write(self, result: list):
        for record in result:
            self.write_single(record)

    @abstractmethod
    def write_single(self, record: dict):
        pass

class markdown_writer(output_writer):
    def __init__(self, output_config: dict) -> None:
        super().__init__(output_config)
        self.counts = 0

    def write_single(self, record: dict):
        type = ''
        if record['type'] == 'Journal Articles':
            type = 'journals'
        elif record['type'] == 'Conference and Workshop Papers':
            type = 'conf'
        else:
            print('ERROR: unknown type:', record['type'])
            return None
        config = self.output_config[type]

        # info = ' {counts}.'.format(counts = self.counts)
        # self.counts+=1
        info=''

        for atr in config:
            if atr not in record: continue
            info += '**{atr}**: {value}\n'.format(atr=atr, value=record[atr])
        info += '\n\n'
        self.file.write(info)
        self.file.flush()

# register
class output_write_factory:
    def create_output_writer(output_config: dict):
        type = output_config['output_format']
        # output_path = output_config['output_path']
        if type == 'markdown':
            return markdown_writer(output_config)
        else:
            raise ValueError(f"type {type} not recognized")