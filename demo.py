import requests
import xml.etree.ElementTree as ET

url = "https://dblp.uni-trier.de/search/publ/api?q=toc%3Adb/journals/tkde/tkde35.bht%3A&h=5&format=xml"

response = requests.get(url)
key = ['']
# 确保请求成功
if response.status_code == 200:
    xml_content = response.content
    root = ET.fromstring(xml_content)
    print(root)
    # 从此处开始解析您感兴趣的 XML 部分
    # 例如，获取所有的标题:
    e_list = root.findall("./hits/hit")
    print(e_list)
    for entry in e_list:
        title = entry.find("info/title")
        ee = entry.find("info/ee")
        doi = entry.find("info/doi")
        _type = entry.find('info/type')
        author = entry.find('info/authors/author')
        # key = entry.find("info/key")
        print(title.text)
        print(ee.text)
        print(doi.text)
        print(_type.text)
        print(author.text)


else:
    print("Error:", response.status_code)
