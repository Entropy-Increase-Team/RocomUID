from fuzzywuzzy import process
import pygtrie
from .map.rocom_map import rocom_name_list

class Roster:
    def __init__(self):
        self._roster = pygtrie.CharTrie()
        self.update()

    def update(self):
        self._roster.clear()
        for idx, names in rocom_name_list.items():
            for n in names:
                if n not in self._roster:
                    self._roster[n] = idx
        self._all_name_list = self._roster.keys()

    async def get_name(self, name):
        return self._roster[name] if name in self._roster else ''
    
    async def guess_name(self, name):
        """@return: id, name, score"""
        name, score = process.extractOne(name, self._roster.keys())
        return self._roster[name], score

roster = Roster()

async def get_rocom_name(name):
    rocom_name = await roster.get_name(name)
    confi = 100
    guess = False
    if rocom_name != '':
        return rocom_name
    if rocom_name == '':
        rocom_name, confi = await roster.guess_name(name)
        guess = True
    if confi < 60:
        return 0
    if guess:
        return rocom_name
    return ''