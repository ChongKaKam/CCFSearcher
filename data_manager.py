# import modules
import xml.etree.ElementTree as ET
import requests
import yaml
import os

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
    
    # TODO:
    # def update(self):
    #     pass
    # def delete(self):
    #     pass

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
    