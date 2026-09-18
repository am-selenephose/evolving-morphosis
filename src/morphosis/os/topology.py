"""One topology source for the interactive view and architecture.svg."""
from html import escape

NODES=(
('kernel','Constitutional Kernel','governance','INDEPENDENT AUTHORITY','kernel.py',650,60),
('known','Known fast path','intelligence','MODEL PROPOSAL','application.py',320,150),
('unknown','Unknown future path','intelligence','MODEL PROPOSAL','application.py',980,150),
('identity','Model surface identity','intelligence','SYSTEM COMPILED','schemas.py',650,190),
('graph','Capability intelligence graph','intelligence','INDEPENDENT EVALUATION','graph.py',650,280),
('probe','Probe synthesis','intelligence','MODEL PROPOSAL','probes.py',480,370),
('sandbox','Sandbox fabric','intelligence','INDEPENDENT EVALUATION','probes.py',820,370),
('compiler','Morphogenesis compiler','intelligence','SYSTEM COMPILED','compiler.py',480,460),
('verification','Adaptation verification','intelligence','INDEPENDENT EVALUATION','compiler.py',820,460),
('qualification','Multi-objective qualification','intelligence','INDEPENDENT EVALUATION','qualifier.py',650,550),
('bundle','Evolution Bundle v3','intelligence','SYSTEM COMPILED','schemas.py',650,640),
('policy','Policy gate','governance','HUMAN AUTHORITY','kernel.py',650,730),
('shadow','Shadow','serving','SYSTEM COMPILED','deployment.py',370,820),
('canary','Canary / ramp','serving','SYSTEM COMPILED','deployment.py',650,820),
('serving','Strands serving admission','serving','INDEPENDENT AUTHORITY','agents.py',930,820),
('observability','Observability / requalification','lineage','INDEPENDENT AUTHORITY','application.py',650,910),
('evidence','Evidence / artifact store','lineage','INDEPENDENT AUTHORITY','storage.py',130,460),
('ledger','Evolution ledger / revision DAG','lineage','INDEPENDENT AUTHORITY','storage.py',1170,460),
('archive','Failure memory','lineage','PROPOSAL INPUT ONLY','application.py',650,1000))
EDGES=(('known','identity'),('unknown','identity'),('identity','graph'),('graph','probe'),('probe','sandbox'),('sandbox','compiler'),('compiler','verification'),('verification','qualification'),('qualification','bundle'),('bundle','policy'),('kernel','policy'),('policy','shadow'),('shadow','canary'),('canary','serving'),('serving','observability'),('observability','graph'),('observability','archive'),('archive','compiler'),('graph','evidence'),('bundle','ledger'))
EVENT_FOR_NODE={'identity':'CandidateBootstrapped','probe':'ProbeProposed','graph':'CapabilityObserved','compiler':'AdaptationCompiled','verification':'AdaptationVerified','bundle':'EvolutionBundleCreated','qualification':'QualificationCompleted','shadow':'ShadowStarted','canary':'CanaryStarted','serving':'CandidatePromoted','observability':'RequalificationRequested'}

def topology(snapshot):
    nodes=[]
    for id,label,plane,trust,file,x,y in NODES:
        refs=[e['event_id'] for e in snapshot['events'] if EVENT_FOR_NODE.get(id)==e['event_type']]
        nodes.append(dict(id=id,label=label,plane=plane,trust=trust,purpose=label+' within the canonical Evolution OS',implementation='src/morphosis/os/'+file,
            status='IMPLEMENTED REFERENCE' if file!='agents.py' else 'STRANDS SHARED COMMANDS',inputs=[a for a,b in EDGES if b==id],outputs=[b for a,b in EDGES if a==id],evidence=refs,x=x,y=y))
    return {'nodes':nodes,'edges':[{'from':a,'to':b} for a,b in EDGES],'trace':[e['event_id'] for e in snapshot['events']]}

def architecture_svg(snapshot):
    """Render architecture.svg from the same node/edge records used by the UI."""
    graph=topology(snapshot); nodes={n['id']:n for n in graph['nodes']}
    width,height=1600,1120; box_w,box_h=236,64; ox,oy=150,72
    trust_color={'MODEL PROPOSAL':'#ff8db7','SYSTEM COMPILED':'#ff5b96','INDEPENDENT EVALUATION':'#74d7ff','INDEPENDENT AUTHORITY':'#53e6b1','HUMAN AUTHORITY':'#ffd17a','PROPOSAL INPUT ONLY':'#b996a5'}
    plane_label={'governance':'GOVERNANCE','intelligence':'INTELLIGENCE / EVOLUTION','serving':'SERVING','lineage':'LINEAGE / OBSERVABILITY'}
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
      '<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#020103"/><stop offset=".55" stop-color="#070207"/><stop offset="1" stop-color="#020103"/></linearGradient><filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#9c3a63"/></marker><style>.title{font:700 34px Georgia,serif;fill:#fff7fb}.sub{font:500 12px ui-monospace,monospace;fill:#bd9aaa;letter-spacing:1.2px}.plane{font:700 10px ui-monospace,monospace;fill:#ff8db7;letter-spacing:1.7px}.node{fill:#090409;stroke:#6b1e3d;stroke-width:1.2}.nodehot{fill:#11050d;stroke:#ff4e8d;stroke-width:1.35}.label{font:600 15px Georgia,serif;fill:#ffe8f1}.meta{font:500 9px ui-monospace,monospace;fill:#a98a98}.edge{stroke:#87304f;stroke-width:1.25;fill:none;marker-end:url(#arrow)}.loop{stroke:#ff4f8d;stroke-width:1.35;fill:none;stroke-dasharray:5 5;marker-end:url(#arrow)}.band{fill:#0a0408;stroke:#2e0f1d;stroke-width:1}</style></defs>',
      '<rect width="1600" height="1120" fill="url(#bg)"/>','<ellipse cx="820" cy="520" rx="520" ry="360" fill="#ff2f78" opacity=".035" filter="url(#glow)"/>',
      '<text x="70" y="62" class="plane">EVOLVING MORPHOSIS · EVOLUTION OS V3</text>','<text x="70" y="106" class="title">Canonical model evolution control plane</text>',
      '<text x="70" y="135" class="sub">ONE PYTHON AUTHORITY · HASHED EVIDENCE · STRANDS SHARED COMMANDS · REVERSIBLE PROMOTION · EVENT-DRIVEN UI</text>']
    bands={'governance':(145,88),'intelligence':(220,560),'serving':(785,120),'lineage':(910,150)}
    for plane,(y,h) in bands.items():
        parts.append(f'<rect x="50" y="{y}" width="1500" height="{h}" rx="6" class="band" opacity=".72"/><text x="68" y="{y+19}" class="plane">{plane_label[plane]}</text>')
    for e in graph['edges']:
        a,b=nodes[e['from']],nodes[e['to']]
        ax,ay=a['x']+ox,a['y']+oy; bx,by=b['x']+ox,b['y']+oy; mid=(ay+by)/2
        cls='loop' if (e['from'],e['to']) in {('observability','graph'),('archive','compiler')} else 'edge'
        parts.append(f'<path d="M {ax} {ay+box_h/2} C {ax} {mid}, {bx} {mid}, {bx} {by-box_h/2}" class="{cls}"/>')
    for n in graph['nodes']:
        x=n['x']+ox-box_w/2; y=n['y']+oy-box_h/2; color=trust_color.get(n['trust'],'#ff8db7'); hot=n['trust'] in ('HUMAN AUTHORITY','MODEL PROPOSAL')
        parts.append(f'<g id="node-{escape(n["id"])}" transform="translate({x:.1f} {y:.1f})"><rect width="{box_w}" height="{box_h}" rx="5" class="{"nodehot" if hot else "node"}"/>')
        parts.append(f'<circle cx="18" cy="18" r="4" fill="{color}" filter="url(#glow)"/><text x="31" y="23" class="label">{escape(n["label"])}</text>')
        parts.append(f'<text x="18" y="44" class="meta" fill="{color}">{escape(n["trust"])}</text><text x="18" y="57" class="meta">{escape(n["implementation"].split("/")[-1])} · evidence {len(n["evidence"])}</text></g>')
    parts += ['<line x1="70" y1="1090" x2="1530" y2="1090" stroke="#35101f"/>','<text x="800" y="1110" class="meta" text-anchor="middle">MODEL PROPOSALS NEVER CERTIFY THEMSELVES · HARD INVARIANTS AND SOURCE-MERGE AUTHORITY REMAIN OUTSIDE MODEL CONTROL</text>','</svg>']
    return ''.join(parts)+'\n'
