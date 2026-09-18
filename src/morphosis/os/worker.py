"""Closed reference interpreter. No candidate code, filesystem API, network or secrets."""
import json
import resource
import sys

resource.setrlimit(resource.RLIMIT_CPU,(2,2))
resource.setrlimit(resource.RLIMIT_AS,(128*1024*1024,128*1024*1024))
resource.setrlimit(resource.RLIMIT_FSIZE,(0,0))
resource.setrlimit(resource.RLIMIT_NOFILE,(8,8))
packet=json.loads(sys.stdin.read(1048577))
memory=int(packet['memory_mb'])*1024*1024
resource.setrlimit(resource.RLIMIT_AS,(memory,memory))
if packet['transport'] not in ('json-text','native-json','broken-json'):raise ValueError('transport unavailable')
def transform(value):
    if isinstance(value,dict) and 'document' in value and 'patch' in value:
        result=dict(value['document'])
        if len(value['patch'])>16:raise ValueError('patch budget exceeded')
        for operation in value['patch']:
            if operation['op']!='set':raise ValueError('unsupported patch operation')
            result[operation['key']]=operation['value']
        return result
    return value
value=packet['input']
value=[transform(item) for item in value] if isinstance(value,list) else transform(value)
if packet['transport']=='json-text':result=json.dumps(value,sort_keys=True,separators=(',',':'))
elif packet['transport']=='broken-json':result='malformed provider output'
else:result=value
print(json.dumps({'output':result},sort_keys=True))
