#!/usr/bin/env python3
"""校验约定式提交及中文说明；支持本地消息文件和 GitHub PR。"""
import argparse
import json
import os
import re
from pathlib import Path

TITLE=re.compile(r'^(feat|fix|refactor|perf|docs|test|build|ci|chore|style|revert)(\([a-z0-9][a-z0-9-]*\))?(!)?: .+')

def check(title,body):
    errors=[]
    if not TITLE.fullmatch(title):errors.append('标题须采用 type(scope): 中文说明 格式')
    if len(title)>72:errors.append('标题不得超过72个字符')
    if not re.search(r'[\u4e00-\u9fff]',title):errors.append('标题说明须使用中文')
    if not re.search(r'[\u4e00-\u9fff]',body):errors.append('正文须包含中文变更说明')
    if re.match(r'^\w+(?:\([^)]*\))?!:',title) and 'BREAKING CHANGE:' not in body:
        errors.append('破坏性变更须在正文包含 BREAKING CHANGE: 说明')
    return errors

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('message_file',nargs='?')
    parser.add_argument('--pull-request',action='store_true')
    args=parser.parse_args()
    if args.pull_request:
        event=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
        pr=event['pull_request'];title=pr['title'];body=pr.get('body') or ''
    elif args.message_file:
        lines=Path(args.message_file).read_text().splitlines();title=lines[0] if lines else '';body='\n'.join(lines[1:])
    else:parser.error('请指定消息文件或 --pull-request')
    errors=check(title,body)
    if errors:raise SystemExit('\n'.join(errors))
    print('标题格式与中文说明检查通过')

if __name__=='__main__':main()
