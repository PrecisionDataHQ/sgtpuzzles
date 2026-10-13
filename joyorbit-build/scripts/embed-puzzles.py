"""Embed pinned source-built Simon Tatham's Puzzles without Play-only graphics."""
from pathlib import Path
import os
import shutil
import subprocess
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'.sources/sgtpuzzles'
revision='8ec4ab867446837514ea35b17cf8f8ee1ed2d9b2'
if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=revision:
    raise SystemExit('Use the pinned 2025-09-12-1919-23762278 Puzzles source.')
module=ROOT/'build/puzzles-embedded'
module.mkdir(parents=True,exist_ok=True)
for name in ['gradlew','gradlew.bat','settings.gradle.kts','gradle.properties']:
    shutil.copy2(source/name,module/name)
for name in ['gradle','buildSrc','app']:
    def ignored(path,names):return [n for n in names if n in ('build','.cxx','.gradle')]
    shutil.copytree(source/name,module/name,dirs_exist_ok=True,ignore=ignored)
(module/'local.properties').write_text('sdk.dir='+os.environ['ANDROID_SDK_ROOT']+'\n')
top=(source/'build.gradle.kts').read_text().replace('id("com.android.application") version "8.13.0" apply false','id("com.android.library") version "8.13.0" apply false')
(module/'build.gradle.kts').write_text(top)
p=module/'app/build.gradle.kts';s=p.read_text().replace('id("com.android.application")','id("com.android.library")')
s=s.replace('        applicationId = "io.precisiondata.joyorbit.puzzles"','')
s=s.replace('        versionCode = 149','        buildConfigField("int", "VERSION_CODE", "149")')
s=s.replace('        versionName = timestamp(false)','        buildConfigField("String", "VERSION_NAME", "\\\"JoyOrbit Puzzles / source 2025-09-12-1919-23762278\\\"")')
s='\n'.join(line for line in s.splitlines() if not any(token in line for token in ('versionNameSuffix', 'isDebuggable =', 'targetSdk =')))+'\n'
p.write_text(s)
# Preserve activity themes/metadata, but keep this family in its own task/process.
android='{http://schemas.android.com/apk/res/android}'
original=E.parse(module/'app/src/main/AndroidManifest.xml').getroot()
manifest=E.Element('manifest');app=E.SubElement(manifest,'application')
for entry in original.find('application'):
    if entry.tag not in ['activity','service','provider']:continue
    name=entry.get(android+'name','')
    if name.startswith('.'):entry.set(android+'name','name.boyle.chris.sgtpuzzles'+name)
    entry.set(android+'process',':puzzles')
    if entry.tag=='activity':
        entry.set(android+'taskAffinity','io.precisiondata.joyorbit.puzzles')
        entry.set(android+'enableOnBackInvokedCallback','false')
        entry.set(android+'screenOrientation','landscape')
        for child in list(entry):
            if child.tag=='intent-filter':entry.remove(child)
            elif child.tag=='meta-data' and child.get(android+'value','').startswith('.'):
                child.set(android+'value','name.boyle.chris.sgtpuzzles'+child.get(android+'value'))
        parent=entry.get(android+'parentActivityName','')
        if parent.startswith('.'):entry.set(android+'parentActivityName','name.boyle.chris.sgtpuzzles'+parent)
    elif entry.tag=='provider':
        entry.set(android+'authorities','${applicationId}.puzzles.files')
        for child in entry:
            if child.get(android+'resource')=='@xml/file_paths':child.set(android+'resource','@xml/puzzles_file_paths')
    app.append(entry)
E.register_namespace('android',android[1:-1])
E.ElementTree(manifest).write(module/'app/src/main/AndroidManifest.xml',encoding='unicode',xml_declaration=True)
shutil.move(module/'app/src/main/res/xml/file_paths.xml',module/'app/src/main/res/xml/puzzles_file_paths.xml')
base=module/'app/src/main/kotlin/name/boyle/chris/sgtpuzzles'
p=base/'GamePlay.kt';p.write_text(p.read_text().replace('"$packageName.fileprovider"','"$packageName.puzzles.files"').replace('        NavUtils.navigateUpFromSameTask(this)', '        startActivity(android.content.Intent(this, GameChooser::class.java))\n        finish()'))
p=base/'SGTPuzzles.kt';s=p.read_text();a=s.index('        TaskStackBuilder.create(this)');b=s.index('        finish()',a)
s=s[:a]+'        startActivity(intent.setClass(this, GamePlay::class.java))\n'+s[b:];p.write_text(s)
p=base/'NightModeHelper.kt';s=p.read_text();needle='    open class ActivityWithNightMode : AppCompatActivity() {'
s=s.replace(needle,needle+'''
        private var joyStartDown = false
        private var joySelectDown = false
        override fun onWindowFocusChanged(hasFocus: Boolean) {
            if (!hasFocus) { joyStartDown = false; joySelectDown = false }
            super.onWindowFocusChanged(hasFocus)
        }
        override fun dispatchKeyEvent(event: android.view.KeyEvent): Boolean {
            if (event.keyCode == android.view.KeyEvent.KEYCODE_BUTTON_START)
                joyStartDown = event.action == android.view.KeyEvent.ACTION_DOWN
            if (event.keyCode == android.view.KeyEvent.KEYCODE_BUTTON_SELECT)
                joySelectDown = event.action == android.view.KeyEvent.ACTION_DOWN
            if ((joyStartDown && joySelectDown && event.action == android.view.KeyEvent.ACTION_DOWN) ||
                (event.keyCode == android.view.KeyEvent.KEYCODE_BACK &&
                 event.action == android.view.KeyEvent.ACTION_DOWN && event.isLongPress)) {
                finishAffinity()
                return true
            }
            return super.dispatchKeyEvent(event)
        }
''',1);p.write_text(s)
subprocess.run(['sh',str(module/'gradlew'),'-p',str(module),':app:assembleDebug','--no-daemon','--no-configuration-cache'],check=True)
output=ROOT/'build/android-apk/libs';output.mkdir(parents=True,exist_ok=True)
shutil.copy2(module/'app/build/outputs/aar/app-debug.aar',output/'joyorbit-puzzles.aar')
print('Puzzles embedded; rebuild APK with its AndroidX runtime dependencies.')
