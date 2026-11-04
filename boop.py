#!/usr/bin/env python3
"""Optional manual Rootshell notification adapter; no auto-install or pairing."""
import argparse
import json
import shutil
import subprocess
import sys


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--title',default='D / dot-box')
    parser.add_argument('--body',default='Work finished. Return to the conversation for the result.')
    parser.add_argument('--status',choices=['done','failed','blocked'],default='done')
    parser.add_argument('--device')
    args=parser.parse_args(argv)
    cli=shutil.which('rootshell-notify')
    if args.check:
        print(json.dumps({'cli_installed':bool(cli),'pairing_verified':False,
                          'note':'Use vendor status/test after pairing; no notification sent.'}))
        return 0
    if not cli:
        print('Rootshell notifier is not installed/paired here; no push sent. Use the chat fallback.',file=sys.stderr)
        return 2
    cmd=[cli,'send','--title',args.title,'--body',args.body,'--status',args.status]
    if args.device:cmd+=['--device',args.device]
    result=subprocess.run(cmd,capture_output=True,text=True)
    if result.returncode:
        print('Rootshell notification failed; no delivery claim. Check pairing with the vendor CLI.',file=sys.stderr)
        return 2
    print('Notification request accepted by rootshell-notify; device delivery is not acknowledged here.')
    return 0


if __name__=='__main__':sys.exit(main())
