"""Generate static projections by executing the canonical Python reference engine."""
import argparse
import json
from pathlib import Path
from .os.application import MorphosisApplication
from .os import schemas
from .os.topology import architecture_svg

FIXED='2026-09-15T06:00:00Z'

def seed(app):
    rows=[('reference-native','reference','reference://native'),('future-model-x','reference','reference://echo'),
          ('regression-candidate','reference','reference://broken'),('unbound-future-model','future-provider','https://future.invalid/v1')]
    surfaces=[]
    for model,provider,endpoint in rows:
        surfaces.append(app.command('bootstrap',{'model':model,'provider':provider,'endpoint':endpoint,'claims':['future.semantic_patch.v1']}))
    for index in (0,2,3):app.command('evaluate',{'surface_id':surfaces[index]['surface_id']})
    b=app.command('bundle',{'surface_id':surfaces[0]['surface_id'],'rollback':True})
    for _ in range(7):app.command('advance',{'transaction_id':b['transaction']['transaction_id']})
    return surfaces


def write(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False)+'\n')

def export(destination,architecture_path=None):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    app=MorphosisApplication(clock=lambda:FIXED);surfaces=seed(app);snapshot=app.snapshot()
    for name,value in [('system',snapshot),('models',snapshot['models']),('evidence',snapshot['evidence']),('events',snapshot['events']),('architecture',snapshot['architecture'])]:write(destination/f'{name}.json',value)
    contract_schemas={name:cls.model_json_schema() for name,cls in vars(schemas).items() if isinstance(cls,type) and issubclass(cls,schemas.Record) and cls is not schemas.Record}
    write(destination/'schemas.json',contract_schemas)
    scenarios={}
    # Each scenario begins from precisely the exported snapshot; no handcrafted decision data.
    for surface in surfaces:
        replay=MorphosisApplication(clock=lambda:FIXED);seed(replay);before=replay.snapshot()['sequence']
        result=replay.command('evaluate',{'surface_id':surface['surface_id']})
        scenarios[surface['surface_id']]={'result':result,'snapshot':replay.snapshot(),'events':replay.events(before)}
    write(destination/'scenarios.json',scenarios)
    if architecture_path is not None:Path(architecture_path).write_text(architecture_svg(snapshot))
    return app


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[2]/'site/generated');parser.add_argument('--architecture-svg',type=Path)
    args=parser.parse_args();app=export(args.output,args.architecture_svg)
    print(f'Exported backend reference: {len(app.events())} events, head {app.snapshot()["ledger_head"]}')

if __name__=='__main__':main()
