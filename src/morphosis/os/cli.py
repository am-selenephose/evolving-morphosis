"""CLI delegates commands and orchestration to the same application as HTTP."""
import argparse
import asyncio
import json
from .application import MorphosisApplication

def execute(application,name,payload,command_id=None):return application.command(name,payload,command_id)

def main():
    p=argparse.ArgumentParser(description='Canonical Morphosis Evolution OS v3')
    p.add_argument('--db',default=':memory:');p.add_argument('--command');p.add_argument('--payload',default='{}');p.add_argument('--command-id');p.add_argument('--reference-agent',action='store_true')
    args=p.parse_args();app=MorphosisApplication(args.db)
    if args.reference_agent:
        from .agents import create_reference_agent
        result=asyncio.run(create_reference_agent(app).invoke_async('Run the bounded reference evolution.'))
        print(str(result));print(json.dumps(app.snapshot()['deployment'],sort_keys=True))
    elif args.command:print(json.dumps(execute(app,args.command,json.loads(args.payload),args.command_id),sort_keys=True))
    else:print(json.dumps(app.snapshot(),sort_keys=True))

if __name__=='__main__':main()
