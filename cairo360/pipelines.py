import json
import os

class Cairo360Pipeline:
    def open_spider(self, spider):
        self.file = open('all_articles.json', 'w', encoding='utf-8')
        self.file.write('[\n')
        self.first_item = True

    def close_spider(self, spider):
        self.file.write('\n]')
        self.file.close()

    def process_item(self, item, spider):
        if not self.first_item:
            self.file.write(',\n')
        self.first_item = False
        line = json.dumps(dict(item), ensure_ascii=False, indent=4)
        self.file.write(line)
        return item
