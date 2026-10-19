#!/usr/bin/env python3
"""查询一个域名在已生成模块中的候选归属，不推断 Quantumult X 最终命中。"""
import argparse
from pathlib import Path
from urllib.parse import urlsplit

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('domain',help='域名或完整网址')
    args=parser.parse_args()
    value=args.domain.strip()
    try:
        raw_host=urlsplit(value).hostname if '://' in value else value
        if not raw_host or '/' in raw_host or ':' in raw_host:
            parser.error('请输入有效域名或包含域名的完整网址')
        host=raw_host.rstrip('.').encode('idna').decode().lower()
    except (ValueError, UnicodeError):
        parser.error('域名或网址格式不合法')
    matches=[]
    root=Path(__file__).resolve().parents[1]
    for path in sorted((root/'rules/services').glob('*.list')):
        for line in path.read_text().splitlines():
            if not line or line.startswith('#'):continue
            typ,domain,_=[x.strip() for x in line.split(',')]
            if host==domain or (typ=='host-suffix' and host.endswith('.'+domain)):
                matches.append((path.stem,typ,domain))
    print('服务\t匹配类型\t匹配条件')
    for match in matches:print('\t'.join(match))
    if not matches:print('没有找到候选匹配；不代表该域名无需代理或不存在。')
    print('结果仅覆盖当前已生成的模块；多项匹配需要结合主配置和实际日志判断。')

if __name__=='__main__':main()
