#!/usr/bin/env python
# coding:utf-8

import re
import sys


# 单条SQL统计项
class SqlItem:

    def __init__(self, sql_id, sql_cost):
        self.sql_id = sql_id
        self.sql_cost = sql_cost
        self.sql = ''

    def set_sql(self, sql):
        self.sql = sql


# SQL累计统计项
class AccumItem:

    def __init__(self, sql_id, sql_cost):
        self.sql_id = sql_id
        self.accum_cost = sql_cost
        self.accum_times = 1

    def accum(self, sql_cost):
        self.accum_cost += sql_cost
        self.accum_times += 1


time = re.compile("Time：(\\d+) ms - ID：(.+)")

last = None
topx = []
accum = {}

logfile = sys.argv[1] if len(sys.argv) >= 2 else "ec-2019-07-05.log"
topn = int(sys.argv[2]) if len(sys.argv) >= 3 else 10

with open(logfile, "r") as f:
    for line in f:
        z = time.search(line)
        if not z:
            if last is not None:
                last.set_sql(line.strip())
                topx.append(last)
                topx = sorted(topx, key=lambda t: t.sql_cost, reverse=True)[0:topn]
                last = None

            continue

        sqlID = z.group(2)
        cost = int(z.group(1))
        last = SqlItem(sqlID, cost)

        if sqlID not in accum:
            accum[sqlID] = AccumItem(sqlID, cost)
        else:
            accum[sqlID].accum(cost)

print("单次执行时间排行榜 Single top" + str(topn) + ":")
for idx, v in enumerate(topx):
    print("#", idx + 1, " Cost:", v.sql_cost, "ms ID:", v.sql_id)
    print(v.sql)

accumTop20 = sorted(accum.values(), key=lambda x: x.accum_cost, reverse=True)[0:topn]

print()
print("累积执行时间排行榜 Accumulative top" + str(topn) + ":")

for idx, v in enumerate(accumTop20):
    print("#", idx + 1, "Accum Cost:", v.accum_cost, "ms, ID:", v.sql_id, "times:", v.accum_times)

timesTop20 = sorted(accum.values(), key=lambda x: x.accum_times, reverse=True)[0:topn]

print()
print("执行总次数排行榜 Exec Times top" + str(topn) + ":")

for idx, v in enumerate(timesTop20):
    print("#", idx + 1, "Accum Times:", v.accum_times, "times, ID:", v.sql_id, "Accum Cost:", v.accum_cost)

avgTop20 = sorted(accum.values(), key=lambda x: x.accum_cost / x.accum_times, reverse=True)[0:topn]

print()
print("平均执行时间排行榜 Avg Cost top" + str(topn) + ":")

for idx, v in enumerate(avgTop20):
    print("#", idx + 1, "Avg Cost:", v.accum_cost / v.accum_times, "ms, ID:", v.sql_id)
