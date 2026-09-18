"""Real Strands orchestration bound to an injected canonical application instance."""
from strands import Agent,tool
from strands.tools.executors import SequentialToolExecutor
from morphosis.demo_model import DeterministicFutureModel,_tool_call,_text,_collect_tool_results,_decode_tool_result


def command_tool(application):
    @tool
    async def morphosis_command(name:str,payload:dict,command_id:str)->dict:
        """Invoke the canonical Morphosis application; candidate proposals never certify themselves.

        Args:
            name: Application command name.
            payload: Strict command proposal or canonical record IDs.
            command_id: Stable idempotency key for this request.
        """
        return application.command(name,payload,command_id=command_id)
    return morphosis_command


class ReferenceEvolutionModel(DeterministicFutureModel):
    """Synthetic planner exercising a real multi-turn tool loop; no model-provider claim."""
    def __init__(self):
        super().__init__({},'');self.config={'model_id':'morphosis-reference-orchestrator-v3'};self.surface_id=None;self.transaction_id=None
    async def stream(self,messages,tool_specs=None,system_prompt=None,**kwargs):
        results=_collect_tool_results(messages)
        last=_decode_tool_result(results[-1]['content'][0]) if results else None
        if self.turn==0:
            name='bootstrap';payload={'model':'future-model-x','provider':'reference','endpoint':'reference://echo','claims':['future.semantic_patch.v1']}
        elif self.turn==1:
            self.surface_id=last['surface_id'];name='evaluate';payload={'surface_id':self.surface_id}
        elif self.turn==2:
            name='bundle';payload={'surface_id':self.surface_id,'rollback':True}
        elif self.turn<=9:
            if self.turn==3:self.transaction_id=last['transaction']['transaction_id']
            name='advance';payload={'transaction_id':self.transaction_id}
        else:
            async for e in _text('Reference evolution completed through canonical application services. Transaction: '+str(last)):yield e
            return
        index=self.turn;self.turn+=1
        async for e in _tool_call('morphosis_command',f'v3-{index}',{'name':name,'payload':payload,'command_id':f'reference-agent-{index}'}):yield e


def create_reference_agent(application):
    return Agent(model=ReferenceEvolutionModel(),system_prompt='Propose bounded Morphosis commands. The independent Constitutional Kernel owns all decisions. Never supply evaluator observations or authority fields.',
        tools=[command_tool(application)],tool_executor=SequentialToolExecutor(),callback_handler=None)
