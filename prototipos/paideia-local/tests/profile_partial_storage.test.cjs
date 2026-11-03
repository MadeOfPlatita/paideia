"use strict";
const test = require('node:test');
const assert = require('node:assert/strict');
const Profile = require('../static/profile_model.js');

function storageWithFailure(initial, failKey) {
  const values = new Map(Object.entries(initial));
  return { values, getItem(key) { return values.has(key) ? values.get(key) : null; },
    setItem(key, value) { values.set(key, String(value)); },
    removeItem(key) { if (key === failKey) throw Error('synthetic failure'); values.delete(key); } };
}

test('save reports a written snapshot even when legacy cleanup fails', () => {
  const legacy = Profile.LEGACY_STORAGE_KEYS[0];
  const storage = storageWithFailure({[legacy]: 'legacy synthetic'}, legacy);
  const profile = Profile.createEmptyProfile();
  Profile.setAnswer(profile, 'detalle_economico.colchon_liquido', Profile.makeAmountAnswer('0'));
  const result = Profile.saveStoredProfile(storage, profile, {}, true);
  assert.equal(result.reason, 'legacy_cleanup_failed');
  assert.equal(result.snapshotWritten, true);
  assert.equal(storage.getItem(legacy), 'legacy synthetic');
  assert.equal(Profile.getAnswer(Profile.loadStoredProfile(storage).profile, 'detalle_economico.colchon_liquido').valor.min_eur, '0');
});

test('updated snapshot survives cleanup failure, reload and verified retry', () => {
  const legacy = Profile.LEGACY_STORAGE_KEYS[0];
  const storage = storageWithFailure({[legacy]: 'synthetic legacy'}, legacy);
  const profile = Profile.createEmptyProfile();
  Profile.setAnswer(profile, 'detalle_economico.colchon_liquido', Profile.makeAmountAnswer('123'));
  const partial = Profile.saveStoredProfile(storage, profile, {}, true);
  assert.equal(partial.snapshotWritten, true);
  assert.equal(partial.ok, false);
  const reloaded = Profile.loadStoredProfile(storage);
  assert.equal(reloaded.error, 'legacy_residue');
  assert.equal(Profile.getAnswer(reloaded.profile, 'detalle_economico.colchon_liquido').valor.min_eur, '123');
  storage.removeItem = key => storage.values.delete(key);
  assert.equal(Profile.saveStoredProfile(storage, reloaded.profile, reloaded.legacyAnswers, true).ok, true);
  assert.equal(storage.getItem(legacy), null);
  assert.equal(Profile.loadStoredProfile(storage).error, null);
});

test('save warns when legacy cleanup returns without removing residue', () => {
  const legacy = Profile.LEGACY_STORAGE_KEYS[0];
  const storage = storageWithFailure({[legacy]: 'synthetic'}, null);
  storage.removeItem = () => {};
  const result = Profile.saveStoredProfile(storage, Profile.createEmptyProfile(), {}, true);
  assert.equal(result.ok, false);
  assert.equal(result.snapshotWritten, true);
  assert.equal(result.reason, 'legacy_cleanup_failed');
});

test('reload reports legacy residue alongside a valid current snapshot', () => {
  const profile = Profile.createEmptyProfile();
  const storage = storageWithFailure({
    [Profile.STORAGE_KEY]: JSON.stringify(Profile.makeSnapshot(profile)),
    [Profile.LEGACY_STORAGE_KEYS[0]]: 'synthetic residue'
  }, null);
  const loaded = Profile.loadStoredProfile(storage);
  assert.equal(loaded.optedIn, false);
  assert.equal(loaded.hasSavedProfile, true);
  assert.equal(loaded.error, 'legacy_residue');
});

test('delete does not report complete when a key remains despite a successful removal call', () => {
  const key = Profile.STORAGE_KEY;
  const storage = storageWithFailure({[key]: 'synthetic'}, null);
  storage.removeItem = () => {};
  const result = Profile.clearStoredProfiles(storage);
  assert.equal(result.ok, false);
  assert.equal(storage.getItem(key), 'synthetic');
});

test('delete does not report complete if post-delete verification is unreadable', () => {
  const storage = storageWithFailure({}, null);
  storage.getItem = () => { throw Error('synthetic read failure'); };
  assert.equal(Profile.clearStoredProfiles(storage).ok, false);
});
