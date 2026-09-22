import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync, readFileSync} from 'node:fs';

const manifest=JSON.parse(readFileSync('adapters/appdeploy/manifest.json','utf8'));
const data=readFileSync('adapters/appdeploy/data.js','utf8');
const backend=readFileSync('adapters/appdeploy/backend/index.ts','utf8');

test('AppDeploy remains a deployment overlay, not Morphosis policy authority',()=>{
  assert.equal(manifest.canonical_authority,'src/morphosis/os');
  assert.equal(manifest.claims.external_model_execution,false);
  assert.equal(manifest.claims.production_agentcore,false);
  assert.equal(manifest.claims.source_auto_merge,false);
  assert.match(data,/@appdeploy\/client/);
  assert.match(backend,/fixture proof is explicitly non-production/);
  assert.match(backend,/HUMAN_APPROVAL_REQUIRED/);
});

test('AppDeploy overlay does not fork the locked shared UI',()=>{
  for(const path of manifest.shared_ui) assert.ok(existsSync(path),`missing canonical UI file: ${path}`);
  for(const name of ['index.html','app.js','styles.css','visuals.js']) {
    assert.equal(existsSync(`adapters/appdeploy/${name}`),false,`shared UI must not be duplicated: ${name}`);
  }
});
