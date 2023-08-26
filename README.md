# CCFSearcher

### 1 简介

起因是因为搜索 CCF-A 或者 CCF-B 的文章需要先找到会议再一个个搜，显得效率比较低，目前有一些工具例如 [CCFrank](https://chrome.google.com/webstore/detail/ccfrank/pfcajmbenomfbjnbjhgbnbdjmiklnkie) , [Aminer](https://www.aminer.cn) 可以一定程度上解决问题，但是因为自己爱折腾，所以还是打算简单写一个本地的检索工具。

本项目是基于 [dblp](https://dblp.uni-trier.de/) 数据库开发的 CCF 期刊会议搜索工具。因为自己的变成能力不是很强，所以目前主要采用 Python 来实现。

CCF 标注的资料来源于：[中国计算机学会推荐国际学术会议和期刊目录](https://www.ccf.org.cn/Academic_Evaluation/By_category/) 

### 2 环境要求

本项目尽量用 Python 自带的库，去掉安装环境的烦恼，尽量实现 “能安装Python就能跑” 的想法 👍🏻️。

```python
# 代码中会用到的库
from abc import ABC, abstractmethod
import xml.etree.ElementTree as ET
import requestes
import datetime
import yaml
import re
import os
```

### 3 代码部分

#### 3.1 应该是这样运行的

[还在画……]

#### 3.2 核心文件介绍

本项目的运行采用 `.yaml` 文件进行配置：

+ `config.yaml` ：核心的配置信息
+ `publication.yaml` ：录入 CCF 文档的信息（目前只能手动更新和维护😭️，以后想办法自动化）

核心代码可以分成四个文件：

+ `data_manager.py` ：主要负责从 dblp 数据库下载 xml 格式的文件和管理本地缓存的 xml 文件
+ `output_writer.py` ：主要负责将匹配的数据输出成特定格式的文件，例如 markdown。
+ `search_core.py` ：搜索的核心部分，会需要用到 `data_manager.py` 和`output_writer.py` 的功能
+ `paper_search.py` ：目前只是一个套壳，后续如果有开发命令行输入或者 GUI 可能会用到吧。

#### 3.2 配置文件

`config.yaml` 主要是负责核心的配置信息：

```yaml
# 基本设置
basic_config:
  data_yaml: ./publication.yaml # 会议、期刊的信息录入
  root_path: ./data/			# 下载数据存放的根目录
  file_format: xml				# 默认就是 xml 格式，或许在未来可以有多样的选择
  search_prefix: https://dblp.uni-trier.de/search/publ/api?q=toc%3Adb/	# dblp连接的前缀
  
# 输出设置
output_config:
  output_format: markdown	# 目前只有 markdown 可以选
  output_path: ./output/	# 输出文件所在的目录
  # 每一个匹配项目的输出内容设置
  # 会议（conf）和期刊（journals）可以分别设置，更多的信息可以看一看 xml 文件所给的属性
  conf:
    - title
    - type
    - author
    - venue
    - year
    - ee
    - doi
    - url
    # - key
    # - pages
  journals:
    - title
    - type
    - author
    - venue
    - year
    - volume
    - pages
    - ee
    - doi
    - url
    # - key
    # - pages
```

`publication.yaml` 主要录入了 CCF 的会议和期刊的数据：

⚠️：目前只有CCF-A和大部分CCF-B，会持续更新——2023.8.26

为了方便检索，为每一个会议或者期刊的数据提供一个编码，具体的编码规则如下：

```yaml
# Path:  A    XX     X    XX   (6)
# Info: CCF Domain Type Number 
# CCF: A, B, C
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
# Type: 
#   - 0 journals
#   - 1 conf
# Number: 只是用来区分
```

由于使用 yaml 文件来配置，信息在读取的时候会转化成字典（dict），因此录入的顺序不做要求

对于期刊而言，由于一些期刊一年会出很多期，所以所需要的信息和会议不同：

```yaml
A01000:		# 编码：A 01 0 00
  Level: CCF-A		# [CCF-A, CCF-B, CCF-C]
  Type: journals	# [journals, conf]
  Domian: 计算机体系结构/并行与分布计算/存储系统
  Acronym: TOCS		
  Name: ACM Transactions on Computer Systems
  URL: http://dblp.uni-trier.de/db/journals/tocs/
  Publisher: 
    - ACM
  Path: tocs/tocs	# 根据 dblp 数据库的 path 记录
  Amount: 1			# 一年有多少期
  Number: 36		# 为了计算出对应的 volume，需要提供一个年份（这里是2018）
  Year: 2018		# 以及对应的 volume 的值（这里是 36）
```

对于会议而言，比较简单：

```yaml
A03102:			# 编码：A 03 1 02
  Acronym: S&P
  Domian: 网络与信息安全
  Level: CCF-A	# [CCF-A, CCF-B, CCF-C]
  Name: IEEE Symposium on Security and Privacy
  Publisher: IEEE
  Type: conf	# [journals, conf]
  Path: sp/sp
  URL: http://dblp.uni-trier.de/db/conf/sp/
```

值得注意的是 `Path` 的值，以上面的 sp2023 会议为例子，在 dblp 上面的获取 xml 文件的 URL 是：

https://dblp.uni-trier.de/search/publ/api?q=toc%3Adb/conf/sp/sp2023.bht%3A&h=1000&format=xml

可以看到 `/conf/sp/sp2023.bht` 其中的 `sp/sp` 部分是我们需要填入 `Path` 的。

#### 3.3 写点代码

如果觉得好用，不妨来改改我糟糕的代码吧！

##### A. 将匹配的结果输出成自己喜欢的格式

可以在 `output_writer.py` 中看到源代码。这里采用一个工厂的模式，如果你需要添加你自己的输出方式，可以遵循以下步骤：

1. 继承 `output_writer` 抽象类，以及定义好 `write_single()` 函数，当然你也需要先看看 `output_writer` 类都干了些什么。可以参考已经写好的 `markdown_writer` 类。

   ```python
   class output_writer(ABC):
       def __init__(self, output_config:dict) -> None:
           super().__init__()
           ...
       def write_header(self, input:str, 
                        level_list:list, 
                        type_list:list ,
                        domain_list:list, 
                        year_range:list):
           ...
           
       def write(self, result: list):
           for record in result:
               self.write_single(record)
   
       @abstractmethod
       def write_single(self, record: dict):
           # 需要你继承并完成的函数
           pass
   ```

   **小贴士**：这里传入的 `result` 是一个关于 `record` 的列表。其中 `record` 是一个字典类型的数据，具体有什么内容可以看 `config.yaml` 中关于 `conf` 和 `journals` 的设置，但是不一定所有的数据都会有所有的标签，所以要注意异常情况，可以参考在 `markdown_writer` 中的处理方式：

   ```python
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
           info=''
           for atr in config:
               if atr not in record: continue	# 可能不存在对应 atr，就直接跳过吧。
               info += '**{atr}**: {value}\n'.format(atr=atr, value=record[atr])
           info += '\n\n'
           self.file.write(info)
           self.file.flush()
   
   ```

   

2. 由于我采用的是工厂模式，所以要记得在工厂 `output_writer_factory` 中给你输出方式取个名字：

   ```python
   class output_writer_factory:
       def create_output_writer(output_config: dict):
           type = output_config['output_format']
           # output_path = output_config['output_path']
           if type == 'markdown':
               return markdown_writer(output_config)
           else:
               raise ValueError(f"type {type} not recognized")
   ```

3. 在实际运行的时候，输出的格式是通过读取 `config.yaml` 中的配置来进行设置的，因此记得在 `config.yaml` 中添加刚刚给你输出模式取的名字

   ```yaml
   output_config:
     output_format: markdown	# 这里，这里！
   ```

##### B. 觉得这个匹配模式不够智能

目前在 `SearchCore` 中实现的匹配是基于正则表达式的，可能会比较简单，同时由于 dblp 数据库中可用于检索的只有标题，因此匹配的结果可能有偏差。如果有什么好的 idea 可以改一改这个部分的代码。

`SearchCore` 的处理流程：

1. 根据输入的关键词生成用于检索的 pattern
2. 根据 options 按顺序生成要在 `DataManager` 中检索的编码（例如：A01000），在根据编码在 `publication.yaml` 中检索对应的信息并调用 `DataManager` 中相关的方法生成文件存储的路径
3. 遍历生成好的文件路径列表，读取每一个文件并尝试用 pattern 匹配标题（title），将匹配的项目根据设置好的格式存储为字典类型交给 `output_writer` 类输出

