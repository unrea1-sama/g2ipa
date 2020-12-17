import sqlite3
import urllib.request
import re


online_dictionary_url = 'https://www.oxfordlearnersdictionaries.com/definition/english/learn?q='
db_name = 'phonetics.db'

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0'


class PhoneticDictionary:
    def __init__(self):
        self._init_complete = False
        self._db_conn = sqlite3.connect(db_name, isolation_level=None)
        self._db_cursor = self._db_conn.cursor()
        self._create_table()
        self._init_complete = True

    def query(self, word):
        phonetic = self._query_db(word)
        if phonetic is None:
            phonetic = self._query_online(word)
            if phonetic is not None:
                self._store(word, phonetic)
            else:
                print('could not found phonetic for word: {}'.format(word))
                return None
        return phonetic

    def _query_db(self, word):
        self._db_cursor.execute(
            'select * from phonetics where word=?;', (word,))
        r = self._db_cursor.fetchone()
        if r is not None:
            return r[2]
        else:
            return None

    def _query_online(self, word):
        req = urllib.request.Request(
            online_dictionary_url+word, headers={'User-Agent': user_agent})
        with urllib.request.urlopen(req) as f:
            pattern1 = re.compile(
                r'<div class="phons_br".*<span class="phon">/(.*?)/<')
            data = f.read().decode('utf-8')
            if match is None:
                return None
            else:
                return match.group(1)

    def _store(self, word, phonetic):
        self._db_cursor.execute(
            'insert into phonetics (word,phonetic) values (?,?)', ((word, phonetic)))

    def _create_table(self):
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


if __name__ == '__main__':
    pd = PhoneticDictionary()
    print(pd.query('learn'))
