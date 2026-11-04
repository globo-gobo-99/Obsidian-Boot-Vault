import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('boop',Path(__file__).parents[1]/'boop.py');boop=importlib.util.module_from_spec(spec);spec.loader.exec_module(boop)
class BoopTests(unittest.TestCase):
 def test_missing_notifier_does_not_send(self):
  with patch.object(boop.shutil,'which',return_value=None),patch.object(boop.subprocess,'run') as run:
   self.assertEqual(boop.main([]),2);run.assert_not_called()
 def test_check_is_read_only(self):
  with patch.object(boop.shutil,'which',return_value=None),patch.object(boop.subprocess,'run') as run:
   self.assertEqual(boop.main(['--check']),0);run.assert_not_called()
 def test_explicit_message_is_not_a_shell_command(self):
  with patch.object(boop.shutil,'which',return_value='/fake/rootshell-notify'),patch.object(boop.subprocess,'run',return_value=subprocess.CompletedProcess([],0)) as run:
   self.assertEqual(boop.main(['--device','My iPad','--body','Done; $(do-not-execute)']),0)
   self.assertIn('Done; $(do-not-execute)',run.call_args.args[0]);self.assertNotIn('shell',run.call_args.kwargs)
