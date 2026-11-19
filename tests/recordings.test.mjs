import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {findRecordings} from "../web/recordings.mjs";
const rows = JSON.parse(readFileSync(new URL("../web/recordings.json", import.meta.url))).recordings;

test("original cues and alternative spellings resolve to archival records", () => {
  assert.equal(new Set(rows.map(r => r.reel)).size, 12);
  assert.equal(new Set(rows.map(r => r.url)).size, rows.length);
  assert.ok(findRecordings(rows,"Devil’s Island","Halifax County").length);
  assert.ok(findRecordings(rows,"Eastern Passage","Halifax County").length);
  assert.equal(findRecordings(rows,"William Riley","Hants County").length, 0);
  const [r] = findRecordings(rows,"Go Down Moses William Riley","Halifax County");
  assert.equal(r.year,1943);
  assert.equal(new URL(r.url).searchParams.get("t"),r.cue);
  const alias = findRecordings(rows,"Three English Rovers","").find(r => r.number === 23);
  assert.equal(alias.otherTitles.length, 1);
});
