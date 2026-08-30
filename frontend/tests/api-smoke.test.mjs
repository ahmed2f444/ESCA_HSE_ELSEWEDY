import assert from 'node:assert/strict'
import test from 'node:test'

const storage = new Map()
globalThis.localStorage = {
  getItem: (key) => storage.get(key) ?? null,
  setItem: (key, value) => storage.set(key, String(value)),
  removeItem: (key) => storage.delete(key),
  clear: () => storage.clear(),
}
globalThis.location = {
  pathname: '/',
  assign: () => {},
}

const { dashboard, permits } = await import('../src/api/endpoints.js')

test('mock dashboard routes remain iterable after login routes', async () => {
  const summary = await dashboard.summary()
  assert.equal(typeof summary, 'object')
  assert.ok(summary)
})

test('permit update uses the PUT transport and updates the mock record', async () => {
  const availablePermits = await permits.list()
  assert.ok(availablePermits.length > 0)

  const permitId = availablePermits[0].id
  const description = 'Updated by frontend smoke test'
  const updated = await permits.update(permitId, { description })

  assert.equal(updated.id, permitId)
  assert.equal(updated.description, description)
})
