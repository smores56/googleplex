from datetime import date
from .models import Bestseller, BestsellerList, Review

def load_bestsellers():
    lists = []
    with open('googleplex/static/lists.txt') as f:
        lines = [l.strip() for l in f.readlines()]
        while lines[0] == '':
            lines.pop(0)

        info_line, bs_lines = None, []
        for l in lines:
            if l is '' and info_line and bs_lines:
                lists.append(parse_bestseller(info_line, bs_lines))
                info_line, bs_lines = None, []
            elif info_line is None:
                info_line = l
            else:
                bs_lines.append(l)

        lists.append(parse_bestseller(info_line, bs_lines))

    return lists

def parse_bestseller(bestseller_list_info, bestseller_lines):
    bestsellers = []
    for bs_l in bestseller_lines:
        bs_info = bs_l.split('\\', 4)
        name, author = bs_info[0], bs_info[1]
        pub_date, data = date(*[int(x) for x in bs_info[2].split('-')]), bs_info[3]
        reviews = [Review(*r.split(',', 2)) for r in bs_info[4].split('\\')]

        bestsellers.append(Bestseller(name, author, reviews, pub_date, data))

    info = bestseller_list_info.split('\\')
    name, author = info[0], info[1]
    pub_date = date(*[int(x) for x in info[2].split('-')])
    tags = info[3].split(',')

    return BestsellerList(name, bestsellers, author, pub_date, tags)

DATABASE_DATA = load_bestsellers()
