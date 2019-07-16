#!/usr/bin/env python
# coding:utf-8


import os
import sys
import re

find_impl = re.compile(r"""class\s+(\w+Impl)\b.+?\bimplements\b.*?\b(\w+Service)\b""", re.X)

service = {}


def add_service(impl_name, service_name):
    if service_name not in service:
        service[service_name] = [impl_name]
    else:
        service[service_name].append(impl_name)


def walk_dir(root_dir):
    for root, dirs, files in os.walk(root_dir, True):
        for name in files:
            if name.endswith("Impl.java"):
                java = os.path.join(root, name)
                # print(java)

                with open(java, 'r') as java_file:
                    java_source = java_file.read()

                z = find_impl.search(java_source)
                if z:
                    add_service(z.group(1), z.group(2))


if __name__ == '__main__':
    logfile = sys.argv[1] if len(sys.argv) >= 2 else "/Users/bingoobjca/bjcagit/econtract"
    walk_dir(logfile)

    print("total service that has impls :", len(service))
    for service_name, impls in service.items():
        if len(impls) > 1:
            print(service_name, " has more impls ", impls)

    print()

    for service_name, impls in service.items():
        if len(impls) == 1:
            print(service_name, " has only impl", impls)
        else:
            print(service_name, " has more impls ", impls)
