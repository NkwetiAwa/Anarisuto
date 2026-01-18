import React, { useEffect, useMemo, useState } from 'react'
import { Button, ButtonGroup, Form, Input, Message, Modal, SelectPicker, Table } from 'rsuite'
import { createSale, deleteSale, listProducts, listSales, updateSale } from '../api'

const { Column, HeaderCell, Cell } = Table

function toInt(v) {
  const n = Number(v)
  if (!Number.isFinite(n)) return null
  return Math.trunc(n)
}

function toFloat(v) {
  const n = Number(v)
  if (!Number.isFinite(n)) return null
  return n
}

export default function SalesPanel() {
  const [products, setProducts] = useState([])
  const [sales, setSales] = useState([])
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')

  const [showAddModal, setShowAddModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [editing, setEditing] = useState(null)
  const [deleting, setDeleting] = useState(null)

  const [formValue, setFormValue] = useState({ product_id: null, year: '', revenue: '' })
  const [editValue, setEditValue] = useState({ product_id: null, year: '', revenue: '' })

  const stats = useMemo(() => {
    const totalRevenue = sales.reduce((acc, s) => acc + (Number(s.revenue) || 0), 0)
    const years = sales.map((s) => Number(s.year)).filter((y) => Number.isFinite(y))
    const latestYear = years.length ? Math.max(...years) : null

    const yearly = new Map()
    for (const s of sales) {
      const y = Number(s.year)
      if (!Number.isFinite(y)) continue
      yearly.set(y, (yearly.get(y) || 0) + (Number(s.revenue) || 0))
    }

    const last3 = []
    if (latestYear != null) {
      for (let y = latestYear; y >= latestYear - 2; y--) {
        last3.push({ year: y, revenue: yearly.get(y) || 0 })
      }
    }

    return { totalRevenue, latestYear, last3 }
  }, [sales])

  function formatMoney(n) {
    const num = Number(n) || 0
    return `$${num.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`
  }

  const productOptions = useMemo(
    () =>
      products.map((p) => ({
        label: `${p.name} (${p.category})`,
        value: p.id
      })),
    [products]
  )

  async function refresh() {
    setLoading(true)
    setErr('')
    try {
      const [p, s] = await Promise.all([listProducts(), listSales({ limit: 200, offset: 0 })])
      setProducts(p.items || [])
      setSales(s.items || [])
    } catch (e) {
      setErr(e?.message || 'Failed to load sales')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  async function onAdd() {
    setErr('')
    const product_id = formValue.product_id
    const year = toInt(formValue.year)
    const revenue = toFloat(formValue.revenue)

    if (!product_id || !year || revenue == null) {
      setErr('Please provide product, year, and revenue.')
      return
    }

    try {
      const created = await createSale({ product_id, year, revenue })
      setSales((prev) => [created, ...prev])
      setFormValue({ product_id: null, year: '', revenue: '' })
      setShowAddModal(false)
    } catch (e) {
      setErr(e?.message || 'Failed to create sale')
    }
  }

  async function onEdit(row) {
    setErr('')
    setEditing(row)
    setEditValue({
      product_id: row.product_id ?? null,
      year: String(row.year ?? ''),
      revenue: String(row.revenue ?? '')
    })
    setShowEditModal(true)
  }

  async function onSaveEdit() {
    if (!editing) return
    const product_id = editValue.product_id ?? editing.product_id
    const yearNum = toInt(editValue.year)
    const revenueNum = toFloat(editValue.revenue)

    if (!product_id || !yearNum || revenueNum == null) {
      setErr('Please provide product, year, and revenue.')
      return
    }

    setErr('')
    try {
      const updated = await updateSale(editing.id, { product_id, year: yearNum, revenue: revenueNum })
      setSales((prev) => prev.map((s) => (s.id === editing.id ? updated : s)))
      setShowEditModal(false)
      setEditing(null)
    } catch (e) {
      setErr(e?.message || 'Failed to update sale')
    }
  }

  async function onRemove(row) {
    setErr('')
    setDeleting(row)
    setShowDeleteModal(true)
  }

  async function onConfirmDelete() {
    if (!deleting) return
    setErr('')
    try {
      await deleteSale(deleting.id)
      setSales((prev) => prev.filter((s) => s.id !== deleting.id))
      setShowDeleteModal(false)
      setDeleting(null)
    } catch (e) {
      setErr(e?.message || 'Failed to delete sale')
    }
  }

  return (
    <div>
      {err ? (
        <Message type="error" showIcon style={{ marginBottom: 12 }}>
          {err}
        </Message>
      ) : null}

      <div className="panelHeader">
        <h2>Sales</h2>
        <ButtonGroup>
          <Button appearance="ghost" onClick={refresh} loading={loading}>
            Refresh
          </Button>
          <Button appearance="ghost" onClick={() => setShowAddModal(true)} aria-label="Add sale">
            + New Sales
          </Button>
        </ButtonGroup>
      </div>

      {/* <div className="panelCard"> */}
        <div className="analyticsGrid">
          <div className="statCard">
            <div className="statLabel">Total revenue</div>
            <div className="statValue">{formatMoney(stats.totalRevenue)}</div>
          </div>
          {stats.last3.length ? (
            stats.last3.map((x) => (
              <div className="statCard" key={x.year}>
                <div className="statLabel">Revenue {x.year}</div>
                <div className="statValue">{formatMoney(x.revenue)}</div>
              </div>
            ))
          ) : (
            <div className="statCard">
              <div className="statLabel">Revenue (last 3 years)</div>
              <div className="statValue">—</div>
            </div>
          )}
        </div>
      {/* </div> */}

      <div className="panelCard">
        <Table height={420} data={sales} loading={loading} bordered cellBordered wordWrap>
          <Column width={90} fixed>
            <HeaderCell>ID</HeaderCell>
            <Cell dataKey="id" />
          </Column>

          <Column width={110}>
            <HeaderCell>Year</HeaderCell>
            <Cell dataKey="year" />
          </Column>

          <Column flexGrow={2}>
            <HeaderCell>Product</HeaderCell>
            <Cell>
              {(rowData) => (
                <div>
                  <div>{rowData.product_name || `#${rowData.product_id}`}</div>
                  <div className="muted">{rowData.product_category || ''}</div>
                </div>
              )}
            </Cell>
          </Column>

          <Column flexGrow={1}>
            <HeaderCell>Revenue</HeaderCell>
            <Cell>{(rowData) => formatMoney(rowData.revenue)}</Cell>
          </Column>

          <Column width={180} fixed="right">
            <HeaderCell>Actions</HeaderCell>
            <Cell>
              {(rowData) => (
                <ButtonGroup>
                  <Button size="xs" appearance="link" onClick={() => onEdit(rowData)}>
                    Edit
                  </Button>
                  <Button size="xs" appearance="link" color="red" onClick={() => onRemove(rowData)}>
                    Delete
                  </Button>
                </ButtonGroup>
              )}
            </Cell>
          </Column>
        </Table>
      </div>

      <Modal open={showAddModal} onClose={() => setShowAddModal(false)} size="sm">
        <Modal.Header>
          <Modal.Title>New sale</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form fluid formValue={formValue} onChange={setFormValue}>
            <Form.Group>
              <Form.ControlLabel>Product</Form.ControlLabel>
              <Form.Control
                name="product_id"
                accepter={SelectPicker}
                data={productOptions}
                cleanable
                searchable
                placeholder="Select product"
                block
              />
            </Form.Group>
            <Form.Group>
              <Form.ControlLabel>Year</Form.ControlLabel>
              <Form.Control name="year" accepter={Input} placeholder="2026" autoComplete="off" />
            </Form.Group>
            <Form.Group>
              <Form.ControlLabel>Revenue</Form.ControlLabel>
              <Form.Control name="revenue" accepter={Input} placeholder="12345.67" autoComplete="off" />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button onClick={() => setShowAddModal(false)} appearance="subtle">
            Cancel
          </Button>
          <Button onClick={onAdd} appearance="primary">
            Add
          </Button>
        </Modal.Footer>
      </Modal>

      <Modal
        open={showEditModal}
        onClose={() => {
          setShowEditModal(false)
          setEditing(null)
        }}
        size="sm"
      >
        <Modal.Header>
          <Modal.Title>Edit sale</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form fluid formValue={editValue} onChange={setEditValue}>
            <Form.Group>
              <Form.ControlLabel>Product</Form.ControlLabel>
              <Form.Control
                name="product_id"
                accepter={SelectPicker}
                data={productOptions}
                cleanable
                searchable
                placeholder="Select product"
                block
              />
            </Form.Group>
            <Form.Group>
              <Form.ControlLabel>Year</Form.ControlLabel>
              <Form.Control name="year" accepter={Input} autoComplete="off" />
            </Form.Group>
            <Form.Group>
              <Form.ControlLabel>Revenue</Form.ControlLabel>
              <Form.Control name="revenue" accepter={Input} autoComplete="off" />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button
            onClick={() => {
              setShowEditModal(false)
              setEditing(null)
            }}
            appearance="subtle"
          >
            Cancel
          </Button>
          <Button onClick={onSaveEdit} appearance="primary">
            Save
          </Button>
        </Modal.Footer>
      </Modal>

      <Modal
        open={showDeleteModal}
        onClose={() => {
          setShowDeleteModal(false)
          setDeleting(null)
        }}
        size="xs"
      >
        <Modal.Header>
          <Modal.Title>Delete sale</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {deleting ? (
            <div>
              Delete sale <strong>#{deleting.id}</strong> for{' '}
              <strong>{deleting.product_name || `product #${deleting.product_id}`}</strong> in{' '}
              <strong>{deleting.year}</strong>?
            </div>
          ) : null}
        </Modal.Body>
        <Modal.Footer>
          <Button
            onClick={() => {
              setShowDeleteModal(false)
              setDeleting(null)
            }}
            appearance="subtle"
          >
            Cancel
          </Button>
          <Button color="red" onClick={onConfirmDelete} appearance="primary">
            Delete
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  )
}
