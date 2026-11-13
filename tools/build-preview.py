"""Packs the app into one page plus its art folder, for a Claude preview page.
The app itself needs no build step; this exists only because a preview page
is published as a single file.

Run: python3 tools/build-preview.py [out_dir]   (default: tools/preview/)
"""
import os, re, shutil, subprocess

import sys
HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.dirname(HERE)
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'preview')

os.makedirs(OUT, exist_ok=True)
shutil.rmtree(os.path.join(OUT, 'art'), ignore_errors=True)
shutil.copytree(os.path.join(APP, 'art'), os.path.join(OUT, 'art'))

index = open(os.path.join(APP, 'index.html')).read()
fonts = re.search(r'<link rel="stylesheet" href="https://fonts[^>]+>', index).group(0)
sheets = re.findall(r'<link rel="stylesheet" href="((?:content|styles)/[^"]+)">', index)
css = '\n'.join(open(os.path.join(APP, s)).read() for s in sheets).replace('url(../art/', 'url(art/')
body = re.search(r'<body>(.*)</body>', index, re.S).group(1)
body = re.sub(r'<script type="module"[^>]*></script>', '', body).strip()

js = subprocess.run([os.path.join(HERE, 'node_modules/.bin/esbuild'), os.path.join(APP, 'app/main.js'),
                     '--bundle', '--format=iife', '--target=es2020', '--log-level=warning'],
                    check=True, capture_output=True, text=True).stdout
assert '</script' not in js

page = f"""<title>Composition Preview</title>
<meta name="claude:viewport-fit-sides" content="cover">
{fonts}
<style>
{css}
</style>
{body}
<script>
{js}
</script>
"""
open(os.path.join(OUT, 'composition-preview.html'), 'w').write(page)

# A stand-in for the wrapper a published page gets, for local checks only.
wrapper = ('<!doctype html><html><head><meta charset=utf8><meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover">'
           '<style>:root{color-scheme:light;padding:env(safe-area-inset-top,0px) 0 env(safe-area-inset-bottom,0px)}'
           'body{margin:0;font:14px system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style></head><body>')
open(os.path.join(OUT, '_local.html'), 'w').write(wrapper + page + '</body></html>')
print('built', len(page) // 1024, 'KB;', sorted(os.listdir(os.path.join(OUT, 'art'))))
