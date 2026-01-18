export async function runQuery(question) {
  const resp = await fetch('/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question })
  })

  if (!resp.ok) {
    let detail
    try {
      detail = await resp.json()
    } catch {
      detail = { error: 'request_failed' }
    }
    throw new Error(typeof detail?.detail === 'string' ? detail.detail : JSON.stringify(detail))
  }

  return resp.json()
}

async function requestJson(path, options = {}) {
  const resp = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options
  })
  if (!resp.ok) {
    let detail
    try {
      detail = await resp.json()
    } catch {
      detail = { error: 'request_failed' }
    }
    throw new Error(typeof detail?.detail === 'string' ? detail.detail : JSON.stringify(detail))
  }
  if (resp.status === 204) return null
  return resp.json()
}

export async function listProducts() {
  return requestJson('/admin/products')
}

export async function createProduct(payload) {
  return requestJson('/admin/products', { method: 'POST', body: JSON.stringify(payload) })
}

export async function updateProduct(id, payload) {
  return requestJson(`/admin/products/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })
}

export async function deleteProduct(id) {
  return requestJson(`/admin/products/${id}`, { method: 'DELETE' })
}

export async function listSales(params = {}) {
  const qs = new URLSearchParams(params)
  return requestJson(`/admin/sales?${qs.toString()}`)
}

export async function createSale(payload) {
  return requestJson('/admin/sales', { method: 'POST', body: JSON.stringify(payload) })
}

export async function updateSale(id, payload) {
  return requestJson(`/admin/sales/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })
}

export async function deleteSale(id) {
  return requestJson(`/admin/sales/${id}`, { method: 'DELETE' })
}
