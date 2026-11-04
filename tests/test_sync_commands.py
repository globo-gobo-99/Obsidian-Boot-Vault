from pathlib import Path
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT=Path(__file__).parents[1]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
service=load('sync_supervisor_test',ROOT/'continuous-sync.py')
single=load('single_sync_test',ROOT/'single-sync.py')

class SyncCommandTests(unittest.TestCase):
 def test_single_pass_rejects_continuous_and_forwards_other_args(self):
  self.assertEqual(single.main(['--continuous']),2)
  with patch.object(single.subprocess,'run',return_value=subprocess.CompletedProcess([],0)) as run:
   self.assertEqual(single.main(['--check']),0)
   self.assertEqual(run.call_args.args[0][-1],'--check')
   self.assertNotIn('--continuous',run.call_args.args[0])

 def test_failure_classification_does_not_repeat_authentication(self):
  self.assertTrue(service.retryable(['Sync stopped with an error'],2))
  self.assertTrue(service.retryable([],0))
  self.assertFalse(service.retryable(['Login required'],2))
  self.assertFalse(service.retryable(['unknown failure'],2))

 def test_stale_pid_identity_is_not_a_live_supervisor(self):
  with tempfile.TemporaryDirectory() as td:
   settings=service.boot.settings_from_env({'OB_SK_WORKSPACE_ROOT':td})
   folder,path,_=service.paths(settings);folder.mkdir(parents=True)
   path.write_text(json.dumps({'pid':os.getpid(),'process_identity':'not-the-current-process'}))
   self.assertFalse(service.status(settings)['supervisor_running'])

 def test_supervisor_recovers_disconnect_and_stops_its_own_child(self):
  with tempfile.TemporaryDirectory() as td:
   base=Path(td);script=base/'continuous-sync.py';shutil.copy(ROOT/'continuous-sync.py',script)
   fake='''import os,sys,time
from pathlib import Path
class SetupNeeded(Exception):pass
class Settings:
 state=Path(os.environ['TEST_SYNC_STATE'])
 vault_id='fixture'
def settings_from_env():return Settings()
def active_writer(settings):return False
if __name__=='__main__':
 p=Settings.state/'count';p.parent.mkdir(parents=True,exist_ok=True)
 count=int(p.read_text())+1 if p.exists() else 1;p.write_text(str(count))
 print('Fully synced',flush=True)
 if count==1:
  print('Sync stopped with an error',flush=True);sys.exit(2)
 time.sleep(60)
'''
   (base/'bootstrap-vault.py').write_text(fake)
   env=dict(os.environ,TEST_SYNC_STATE=str(base/'state'))
   child=subprocess.Popen([sys.executable,str(script)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
   try:
    statusfile=base/'state/ob-sk/fixture/continuous-status.json';deadline=time.monotonic()+10;saved={}
    while time.monotonic()<deadline:
     if statusfile.exists():
      saved=json.loads(statusfile.read_text())
      if saved.get('restarts',0)>=1 and saved.get('state')=='synced':break
     time.sleep(.05)
    self.assertEqual(saved.get('state'),'synced',saved)
    self.assertGreaterEqual(saved.get('restarts',0),1)
    report=subprocess.run([sys.executable,str(script),'--status'],env=env,capture_output=True,text=True)
    self.assertTrue(json.loads(report.stdout)['supervisor_running'])
    stopped=subprocess.run([sys.executable,str(script),'--stop'],env=env,capture_output=True,text=True)
    self.assertEqual(stopped.returncode,0,stopped.stderr)
    self.assertEqual(child.wait(timeout=5),0)
    self.assertEqual(json.loads(statusfile.read_text())['state'],'stopped')
   finally:
    if child.poll() is None:child.terminate();child.wait(timeout=5)
    child.stderr.close()

if __name__=='__main__':unittest.main()
