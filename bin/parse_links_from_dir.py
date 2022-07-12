#!/usr/bin/env python3
"""
bin/parse_links_from_dir.py ~/projects/aws-cloudformation-user-guide/doc_source "https://raw.githubusercontent.com/awsdocs/aws-cloudformation-user-guide/main/doc_source/"

bin/parse_links_from_dir.py ~/projects/aws-sam-developer-guide/doc_source "https://raw.githubusercontent.com/awsdocs/aws-sam-developer-guide/main/doc_source/"
"""
import itertools
import os
import sys


def main():
    directories = sys.argv[1::2]
    base_urls = sys.argv[2::2]
    is_prop = lambda f: f.startswith("aws-properties") or f.startswith("sam-property")
    is_resource = lambda f: f.startswith("aws-resource") or f.startswith("sam-resource")
    matching_files = (
        url + f
        for d, url in zip(directories, base_urls)
        for f in os.listdir(d)
        if is_resource(f) or is_prop(f)
    )
    for f in sorted(matching_files):
        print(f)


if __name__ == "__main__":
    main()
