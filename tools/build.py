#!/usr/bin/env python3
"""从明确许可的上游生成 Quantumult X 域名规则；仅使用 Python 标准库。"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import ipaddress
import json
import re
import sys
import tarfile
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = 'https://github.com/v2fly/domain-list-community'
SHARED = {
    'amazonaws.com', 'cloudfront.net', 'azure.com', 'azureedge.net',
    'windows.net', 'cloudflare.com', 'akamaihd.net', 'akamaized.net',
    'fastly.net', 'googleapis.com', 'googleusercontent.com', 'gstatic.com',
    'live.com', 'microsoft.com', 'sharepoint.com', 'sharepointonline.com',
    'auth0.com', 'algolia.net', 'intercom.io', 'intercomcdn.com',
    'launchdarkly.com', 'segment.io', 'sentry.io', 'stripe.com',
    'identrust.com', 'doubleclick.net', 'googletagmanager.com',
    'googleadservices.com', 'google-analytics.com',
}


def csv_write(path, columns, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def load_archive(content):
    """只在内存读取普通文件，不解压任意路径或符号链接。"""
    data = {}
    license_text = ''
    with tarfile.open(fileobj=io.BytesIO(content), mode='r:gz') as archive:
        commit = archive.pax_headers.get('comment', '')
        if not re.fullmatch('[0-9a-f]{40}', commit):
            raise ValueError('上游压缩包未包含可核验的提交标识')
        for item in archive:
            if not item.isfile():
                continue
            parts = item.name.split('/')
            if len(parts) == 3 and parts[1] == 'data':
                if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.!@+-]*', parts[2]):
                    raise ValueError(f'不安全的分类名：{parts[2]}')
                if item.size > 10_000_000:
                    raise ValueError('单个上游文件超过大小限制')
                data[parts[2]] = archive.extractfile(item).read().decode('utf-8')
            elif len(parts) == 2 and parts[1] == 'LICENSE':
                license_text = archive.extractfile(item).read().decode('utf-8')
    if not license_text.startswith('MIT License'):
        raise ValueError('上游许可已变化或不可确认，停止构建')
    if not data:
        raise ValueError('上游没有规则数据')
    return data, license_text, commit


class Resolver:
    def __init__(self, data):
        self.entries = defaultdict(list)
        self.memo = {}
        for name, text in data.items():
            for number, line in enumerate(text.splitlines(), 1):
                content = line.split('#', 1)[0].strip()
                if not content:
                    continue
                tokens = content.split()
                term = tokens[0]
                kind, sep, value = term.partition(':')
                if not sep:
                    kind, value = 'domain', term
                attrs = frozenset(t[1:] for t in tokens[1:] if t.startswith('@'))
                unknown = [t for t in tokens[1:] if not t.startswith(('@', '&'))]
                if unknown:
                    raise ValueError(f'{name}:{number} 未识别的附加字段')
                entry = (kind, value, attrs, name, number)
                self.entries[name].append(entry)
                for token in tokens[1:]:
                    if token.startswith('&'):
                        if kind == 'include':
                            raise ValueError('暂不支持 include 的 affiliation')
                        self.entries[token[1:]].append(entry)

    def resolve(self, name, stack=()):
        if name in stack:
            raise ValueError('循环引用：' + ' -> '.join((*stack, name)))
        if name in self.memo:
            return self.memo[name]
        if name not in self.entries:
            raise ValueError(f'引用不存在的分类：{name}')
        result = set()
        for entry in self.entries[name]:
            kind, value, attrs, source, line = entry
            if kind != 'include':
                result.add(entry)
                continue
            for child in self.resolve(value, (*stack, name)):
                tags = child[2]
                if all((tag[1:] not in tags if tag.startswith('-') else tag in tags) for tag in attrs):
                    result.add(child)
        self.memo[name] = tuple(sorted(result, key=lambda e: (e[0], e[1], tuple(sorted(e[2])), e[3], e[4])))
        return self.memo[name]


def normalize(entry, ads_only=False):
    kind, value, attrs, source, line = entry
    if ads_only and 'ads' not in attrs:
        return None, '不是广告属性规则'
    if not ads_only and 'ads' in attrs:
        return None, '广告属性：不混入业务规则'
    if kind not in ('full', 'domain'):
        return None, '关键词或正则：不作无损转换声明'
    try:
        value = value.rstrip('.').encode('idna').decode('ascii').lower()
    except UnicodeError:
        return None, '域名编码不合法'
    try:
        ipaddress.ip_address(value)
    except ValueError:
        pass
    else:
        return None, 'IP 地址不能作为域名条件直接转换'
    if len(value) > 253 or '.' not in value or any(
        not re.fullmatch(r'[a-z0-9_](?:[a-z0-9_-]{0,61}[a-z0-9_])?', label)
        for label in value.split('.')
    ):
        return None, '域名格式或长度需要审查'
    if value in SHARED:
        return None, '共享平台或身份服务根域名：需单独决定去向'
    return ('host' if kind == 'full' else 'host-suffix', value), ''


def render(name, safe, commit):
    header = ('# 名称：' + name + '\n# 来源：' + REPO + '/tree/' + commit + '/data/' + name
              + '\n# 原作者：V2Fly / V2Ray 社区贡献者；上游许可：MIT\n'
              '# 本地修改：转换格式、去重、分离广告属性、隔离关键词/正则及共享根域名。\n'
              '# 状态：静态校验通过不代表真实设备验证通过。内部策略由 force-policy 覆盖。\n')
    return header + ''.join(f'{kind}, {value}, proxy\n' for kind, value in sorted(safe))


def build(content):
    data, license_text, commit = load_archive(content)
    manifest = json.loads((ROOT/'sources/selection.json').read_text())
    resolver = Resolver(data)
    missing = sorted(set(manifest['services']) - set(resolver.entries))
    if missing:
        raise ValueError('选定分类已在上游消失：' + ', '.join(missing))
    output = {}; review = []; catalog = []; owners = defaultdict(set)
    for name in sorted(resolver.entries):
        category = manifest['services'].get(name)
        row = {'服务': name, '分类': category or '其他上游分类', '已构建': bool(category),
               '域名规则数': '', '待审查数': '', '来源': f'{REPO}/tree/{commit}/data/{name}'}
        if category:
            safe = set(); count = 0
            for entry in resolver.resolve(name):
                rule, reason = normalize(entry)
                if rule:
                    safe.add(rule)
                else:
                    kind, value, attrs, source, line = entry
                    review.append({'服务': name, '源文件': source, '行号': line, '类型': kind,
                                   '内容': value, '原因': reason})
                    count += 1
            if not safe:
                raise ValueError(f'{name} 没有可发布的域名条件，停止构建')
            output[name] = render(name, safe, commit)
            for kind, value in safe:
                owners[(kind, value)].add(name)
            row.update(域名规则数=len(safe), 待审查数=count)
        catalog.append(row)
    # 全部解析成功后再落盘，避免上游异常时产生部分更新。
    source_dir = ROOT/'sources/v2fly/data'
    source_dir.mkdir(parents=True, exist_ok=True)
    for name, text in data.items():
        (source_dir/name).write_text(text)
    for name, text in output.items():
        path = ROOT/'rules/services'/f'{name}.list'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    (ROOT/'LICENSE').write_text(license_text)
    (ROOT/'sources/v2fly/LICENSE').write_text(license_text)
    for folder, expected in [(source_dir, set(data)), (ROOT/'rules/services', {n+'.list' for n in output})]:
        for path in folder.iterdir():
            if path.is_file() and path.name not in expected:
                path.unlink()
    source_meta = {'项目': REPO, '许可': 'MIT', '提交': commit,
                   '压缩包SHA256': hashlib.sha256(content).hexdigest(),
                   '上游文件数': len(data), '上游含虚拟分类数': len(resolver.entries),
                   '构建模块数': len(output), '域名规则数': sum(t.count(', proxy\n') for t in output.values())}
    (ROOT/'sources/lock.json').write_text(json.dumps(source_meta, ensure_ascii=False, indent=2)+'\n')
    csv_write(ROOT/'catalog/services.csv', list(catalog[0]), catalog)
    csv_write(ROOT/'reports/review.csv', ['服务','源文件','行号','类型','内容','原因'], review)
    overlaps = []
    for (kind, value), names in sorted(owners.items()):
        if len(names) > 1:
            overlaps.append({'类型':'相同条件','域名':value,'涉及服务':' / '.join(sorted(names)),'上层后缀':''})
        labels = value.split('.')
        for i in range(len(labels)-1):
            ancestor = '.'.join(labels[i:])
            others = owners.get(('host-suffix',ancestor),set()) - names
            if others:
                overlaps.append({'类型':'后缀包含','域名':value,'涉及服务':' / '.join(sorted(names | others)),'上层后缀':ancestor})
    csv_write(ROOT/'reports/overlaps.csv', ['类型','域名','涉及服务','上层后缀'], overlaps)
    print(json.dumps(source_meta, ensure_ascii=False, indent=2))


def validate():
    manifest = json.loads((ROOT/'sources/selection.json').read_text())
    lock = json.loads((ROOT/'sources/lock.json').read_text())
    data = {p.name:p.read_text() for p in (ROOT/'sources/v2fly/data').iterdir() if p.is_file()}
    resolver = Resolver(data)
    errors = []; count = 0
    for name in manifest['services']:
        path = ROOT/'rules/services'/f'{name}.list'
        if not path.exists():
            errors.append(f'缺失模块：{name}'); continue
        expected = {rule for entry in resolver.resolve(name) if (rule := normalize(entry)[0])}
        if path.read_text() != render(name, expected, lock['提交']):
            errors.append(f'生成结果与上游快照及转换规则不一致：{name}')
        seen = set()
        for line in path.read_text().splitlines():
            if not line or line.startswith('#'):
                continue
            fields = [x.strip() for x in line.split(',')]
            if len(fields)!=3 or fields[0] not in ('host','host-suffix') or fields[2]!='proxy':
                errors.append(f'格式错误：{name}'); continue
            key = tuple(fields)
            if key in seen:
                errors.append(f'重复条件：{name} / {fields[1]}')
            seen.add(key); count += 1
    if errors:
        raise ValueError('\n'.join(errors))
    print(f'校验通过：{len(manifest["services"])} 个模块，{count} 条域名规则')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, help='使用本地上游 tar.gz 构建')
    parser.add_argument('--refresh', action='store_true', help='下载最新上游并构建；不会自动提交或推送')
    parser.add_argument('--check', action='store_true', help='检查当前生成文件')
    args = parser.parse_args()
    if args.refresh:
        req=urllib.request.Request('https://codeload.github.com/v2fly/domain-list-community/tar.gz/refs/heads/master',headers={'User-Agent':'quantumultx-rules-maintenance'})
        with urllib.request.urlopen(req,timeout=60) as response:
            content=response.read(20_000_001)
        if len(content)>20_000_000:
            raise ValueError('上游包超过大小限制')
        build(content)
    elif args.archive:
        build(args.archive.read_bytes())
    if args.check or args.refresh or args.archive:
        validate()
    else:
        parser.print_help()


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f'失败：{exc}', file=sys.stderr)
        sys.exit(1)
