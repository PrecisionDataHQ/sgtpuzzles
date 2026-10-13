"""Prepare pinned free Puzzles source; exclude Play-only graphics and backup credentials."""
from pathlib import Path
import subprocess
import re
import shutil
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'.sources/sgtpuzzles'
revision='8ec4ab867446837514ea35b17cf8f8ee1ed2d9b2'
if not source.exists():
    subprocess.run(['git','clone','--depth','1','--branch','2025-09-12-1919-23762278','https://github.com/chrisboyle/sgtpuzzles',str(source)],check=True)
if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=revision:
    raise SystemExit('Use a fresh pinned Puzzles source tree; preserve existing work.')
def original(name):
    return subprocess.check_output(['git','-C',str(source),'show',revision+':'+name],text=True)
p=source/'app/build.gradle.kts';s=original('app/build.gradle.kts')
s=s.replace('applicationId = "name.boyle.chris.sgtpuzzles"','applicationId = "io.precisiondata.joyorbit.puzzles"')
s=s.replace('29.0.13846066','29.0.14206865').replace('        ndk {', '        ndk {')
s=s.replace('        targetSdk = 36','        ndk { abiFilters += "arm64-v8a" }\n        targetSdk = 36')
a=s.index('fun idForSimon()');b=s.index('fun issuesURL()',a)
s=s[:a]+'fun idForSimon(): String = "UNOFFICIAL-JoyOrbit"\n\n'+s[b:];p.write_text(s)
android='{http://schemas.android.com/apk/res/android}'
p=source/'app/src/main/AndroidManifest.xml';tree=E.fromstring(original('app/src/main/AndroidManifest.xml'))
application=tree.find('application');application.attrib.pop(android+'backupAgent',None)
for child in list(application):
    if child.tag=='meta-data' and 'backup' in child.get(android+'name','').lower():application.remove(child)
    if child.tag=='provider':child.set(android+'authorities','${applicationId}.fileprovider')
E.register_namespace('android',android[1:-1]);p.write_text(E.tostring(tree,encoding='unicode'))
for p in (source/'app/src/main/res').glob('values*/strings.xml'):
    tree=E.parse(p);root=tree.getroot()
    for child in list(root):
        if child.get('name')=='backup_api_key':root.remove(child)
    tree.write(p,encoding='unicode')
shutil.copy2(source/'LICENCE',ROOT/'theme/licenses/Puzzles-MIT.txt')
print('Pinned Puzzles source prepared without backup keys or Play-only graphics.')
