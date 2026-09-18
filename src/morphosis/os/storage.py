"""SQLite command transactions, content addressed artifacts and hash chained events."""
import json
import sqlite3
import threading
from contextlib import contextmanager
from typing import Protocol
from .schemas import DomainEvent,digest

class ArtifactStore(Protocol):
    def put(self,value:dict)->str:...
    def get(self,artifact_hash:str)->dict:...

class EvolutionLedger(Protocol):
    def events(self,after:int=0)->list:...
    def verify(self)->bool:...

class EventBus(Protocol):
    def events(self,after:int=0)->list:...

class StateStore(Protocol):
    def replay(self)->dict:...

class SQLiteLedger:
    def __init__(self,path):
        self.connection=sqlite3.connect(str(path),check_same_thread=False,isolation_level=None)
        self.connection.execute('PRAGMA journal_mode=WAL')
        self.connection.execute('PRAGMA foreign_keys=ON')
        self.connection.executescript('''CREATE TABLE IF NOT EXISTS events(sequence INTEGER PRIMARY KEY,body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS artifacts(hash TEXT PRIMARY KEY,body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS commands(id TEXT PRIMARY KEY,input_hash TEXT NOT NULL,result TEXT NOT NULL);''')
        self.lock=threading.RLock()

    @contextmanager
    def transaction(self):
        with self.lock:
            self.connection.execute('BEGIN IMMEDIATE')
            try:yield;self.connection.execute('COMMIT')
            except BaseException:self.connection.execute('ROLLBACK');raise

    def put(self,value):
        key=digest(value);body=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
        self.connection.execute('INSERT OR IGNORE INTO artifacts VALUES(?,?)',(key,body));return key

    def get(self,key):
        row=self.connection.execute('SELECT body FROM artifacts WHERE hash=?',(key,)).fetchone()
        if not row:raise ValueError('artifact not found')
        value=json.loads(row[0])
        if digest(value)!=key:raise ValueError('artifact tampering')
        return value

    def events(self,after=0):
        with self.lock:return [json.loads(r[0]) for r in self.connection.execute('SELECT body FROM events WHERE sequence>? ORDER BY sequence',(after,))]

    def verify(self):
        try:
            previous='0'*64
            for sequence,e in enumerate(self.events(),1):
                DomainEvent.model_validate(e)
                if e['sequence']!=sequence or e['previous_hash']!=previous:return False
                body={k:v for k,v in e.items() if k!='event_hash'}
                if digest(body)!=e['event_hash']:return False
                for key in e['evidence']:self.get(key)
                previous=e['event_hash']
            return True
        except (ValueError,KeyError,TypeError):return False

    def append(self,event_type,aggregate_id,payload,now,correlation,evidence=()):
        row=self.connection.execute('SELECT sequence,body FROM events ORDER BY sequence DESC LIMIT 1').fetchone()
        seq=row[0]+1 if row else 1;prior=json.loads(row[1]) if row else None
        body=dict(event_type=event_type,timestamp=now,aggregate_id=aggregate_id,correlation_id=correlation,
            causation_id=prior['event_id'] if prior else None,schema_version='3.0',sequence=seq,payload=payload,
            evidence=list(evidence),previous_hash=prior['event_hash'] if prior else '0'*64)
        body['event_id']=digest(body);body['event_hash']=digest(body)
        event=DomainEvent(**body).json_value()
        self.connection.execute('INSERT INTO events VALUES(?,?)',(seq,json.dumps(event,sort_keys=True,separators=(',',':'))))
        return event

    def replay(self):
        if not self.verify():raise ValueError('ledger integrity verification failed')
        state={}
        for e in self.events():
            mutation=e['payload'].get('mutation')
            if mutation:state.setdefault(mutation['collection'],{})[mutation['id']]=mutation['value']
        return state
