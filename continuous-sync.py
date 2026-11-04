#!/usr/bin/env python3
"""Supervise one Sync writer while this computer is running; not an OS boot hook."""
import argparse
from datetime import datetime, timezone
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('ob_sk_bootstrap', HERE/'bootstrap-vault.py')
boot = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = boot
spec.loader.exec_module(boot)


def process_identity(pid):
    try:
        return Path(f'/proc/{pid}/stat').read_text().split(') ',1)[1].split()[19]
    except (OSError, IndexError):
        return None


def paths(settings):
    folder = settings.state/'ob-sk'/settings.vault_id
    return folder, folder/'continuous-status.json', folder/'continuous-supervisor.lock'


def status(settings):
    _, path, _ = paths(settings)
    try:
        saved = json.loads(path.read_text())
    except (OSError, ValueError):
        saved = {'state':'not-started'}
    pid = saved.get('pid')
    saved['supervisor_running'] = bool(pid and saved.get('process_identity') and
                                      process_identity(pid)==saved['process_identity'])
    saved['native_writer_lease_fresh'] = boot.active_writer(settings)
    return saved


def retryable(lines, code):
    if code == 0:
        return True
    text = '\n'.join(lines)
    return any(s in text for s in ['Sync stopped with an error', 'request timed out',
                                   'Another Sync writer started during setup'])


def serve(settings):
    folder, state_path, lock_path = paths(settings)
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    with lock_path.open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('A supervisor already owns this replica.')
            return 0
        stopping = threading.Event()
        child = None
        state = dict(pid=os.getpid(), process_identity=process_identity(os.getpid()),
                     script=str(Path(__file__).resolve()), restarts=0,
                     last_fully_synced_at=None)
        def update(value):
            state.update(state=value, observed_at=datetime.now(timezone.utc).isoformat())
            temp = state_path.with_name(f'.status-{os.getpid()}.tmp')
            temp.write_text(json.dumps(state, indent=2)+'\n')
            os.replace(temp, state_path)
        def stop(signum, frame):
            stopping.set()
            if child is not None and child.poll() is None:
                try:os.killpg(child.pid, signal.SIGTERM)
                except ProcessLookupError:pass
        old_handlers = {sig:signal.signal(sig,stop) for sig in (signal.SIGINT,signal.SIGTERM)}
        delay = 2
        try:
            update('starting')
            while not stopping.is_set():
                if boot.active_writer(settings):
                    update('external-writer')
                    stopping.wait(2)
                    continue
                update('connecting')
                child = subprocess.Popen([sys.executable,str(HERE/'bootstrap-vault.py'),'--continuous'],
                    stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1,
                    start_new_session=True)
                # Never retain raw CLI output: a short sanitized state is enough.
                failures=[]
                for line in child.stdout:
                    if 'Fully synced' in line:
                        state['last_fully_synced_at']=datetime.now(timezone.utc).isoformat()
                        update('synced');delay=2
                        print('Fully synced',flush=True)
                    elif 'Connection successful.' in line:
                        update('connected')
                    elif any(x in line for x in ['Sync stopped with an error','request timed out',
                                                 'Another Sync writer started during setup']):
                        failures.append(next(x for x in ['Sync stopped with an error','request timed out',
                                                         'Another Sync writer started during setup'] if x in line))
                    if stopping.is_set():break
                child.stdout.close()
                code=child.wait(timeout=10)
                child=None
                if stopping.is_set():break
                state['last_exit_code']=code
                if not retryable(failures,code):
                    update('needs-setup')
                    print('Sync needs setup or authentication; run single-sync.py for the diagnostic.',flush=True)
                    return 2
                state['restarts']+=1
                update('retrying')
                print(f'Sync disconnected; retrying in {delay} seconds.',flush=True)
                stopping.wait(delay);delay=min(delay*2,60)
            update('stopped')
            return 0
        finally:
            if child is not None and child.poll() is None:
                try:
                    os.killpg(child.pid,signal.SIGTERM);child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid,signal.SIGKILL);child.wait()
                except ProcessLookupError:pass
            for sig,handler in old_handlers.items():signal.signal(sig,handler)
            fcntl.flock(lock,fcntl.LOCK_UN)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--status',action='store_true')
    group.add_argument('--stop',action='store_true')
    args=parser.parse_args(argv)
    try:
        settings=boot.settings_from_env()
        if args.status:
            print(json.dumps(status(settings),indent=2));return 0
        if args.stop:
            saved=status(settings)
            if saved['supervisor_running'] and saved.get('script')==str(Path(__file__).resolve()):
                os.kill(saved['pid'],signal.SIGTERM)
                print('Stop requested for this replica supervisor.')
            else:print('No matching supervisor is running; external writers are untouched.')
            return 0
        return serve(settings)
    except (boot.SetupNeeded,OSError,subprocess.TimeoutExpired):
        print('Supervisor could not start or stop cleanly; inspect local setup and single-sync diagnostics.',file=sys.stderr)
        return 2


if __name__=='__main__':
    sys.exit(main())
