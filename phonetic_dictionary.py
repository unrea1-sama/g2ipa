import sqlite3
import urllib.request
import re
import time
import os
import random

online_dictionary_url = 'http://www.iciba.com/word?w='

db_name = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), 'phonetics.db')
print('load offline database {}'.format(db_name))
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0'


class PhoneticDictionary:
    def __init__(self):
        self._init_complete = False
        self._db_conn = sqlite3.connect(db_name, isolation_level=None)
        self._db_cursor = self._db_conn.cursor()
        self._create_table()
        self._init_complete = True
        # cache not existed query to save time
        self._not_exist_query = {}

    def query(self, word):
        word = word.lower()
        # if the word's phonetic can't be found in offline source and online source
        if word in self._not_exist_query.keys():
            return None
        phonetic = self._query_db(word)
        if phonetic is None:
            phonetic = self._query_online(word)
            if phonetic is not None:
                self._store(word, phonetic)
            else:
                self._not_exist_query[word] = 1
                print('could not found phonetic for word: {}'.format(word))
        return phonetic

    def _query_db(self, word):
        self._db_cursor.execute(
            'select * from phonetics where word=?;', (word,))
        r = self._db_cursor.fetchone()
        if r:
            return r[2]
        return None

    def _query_online(self, word):
        req = urllib.request.Request(
            online_dictionary_url+word, headers={'User-Agent': user_agent})
        print(req.get_full_url())
        # error other than 404 is ignored
        # 404 indicates that the word doesn't exist
        while 1:
            try:
                phonetic = self.__query_online(req)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    print('could not found {} in online dictionary!'.format(word))
            except urllib.error.URLError:
                pass
            else:
                break
        return phonetic

    def __query_online(self, request):
        time.sleep(random.randint(1, 5))
        with urllib.request.urlopen(request) as f:
            # patter to extact bre phonetic
            pattern1 = re.compile(
                r'Mean_symbols.*?<li>.*?\[(.*?)\]')
            data = f.read().decode('utf-8')
            match = pattern1.search(data)
            if match is None:
                return None
            else:
                return match.group(1)

    def _store(self, word, phonetic):
        self._db_cursor.execute(
            'insert into phonetics (word,phonetic) values (?,?)', ((word, phonetic)))

    def _create_table(self):
        # create table phonetics when the table doesn't exist
        query = "select * from sqlite_master where type='table' and name='phonetics';"
        self._db_cursor.execute(query)
        r = self._db_cursor.fetchone()
        if r is None:
            query = '''
            create table phonetics(
                id INTEGER PRIMARY KEY   AUTOINCREMENT,
                word TEXT,
                phonetic TEXT
            );
            '''
            self._db_cursor.execute(query)

    def make_dictionary(self, words):
        # perform query on word list and make cache in database
        for word in words:
            self.query(word)

    def __del__(self):
        self._db_conn.close()


if __name__ == '__main__':
    pd = PhoneticDictionary()
    print(pd.query('commissioners'))
