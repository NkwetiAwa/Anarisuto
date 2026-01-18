import React, { useEffect, useMemo, useState } from 'react'
import { Button, ButtonGroup, Form, Input, Message, Modal, Table } from 'rsuite'
import { createProduct, deleteProduct, listProducts, updateProduct } from '../api'

const { Column, HeaderCell, Cell } = Table

export default function ProductsPanel() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')

  const [showAddModal, setShowAddModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [editing, setEditing] = useState(null)
  const [deleting, setDeleting] = useState(null)

  const [formValue, setFormValue] = useState({ name: '', category: '' })
  const [editValue, setEditValue] = useState({ name: '', category: '' })

  const stats = useMemo(() => {
    const total = items.length
    const counts = new Map()
    for (const p of items) {
      const key = (p.category || 'Uncategorized').trim() || 'Uncategorized'
      counts.set(key, (counts.get(key) || 0) + 1)
    }
    const topCategories = Array.from(counts.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([category, count]) => ({ category, count }))
    return { total, topCategories }
  }, [items])

  async function refresh() {
    setLoading(true)
    setErr('')
    try {
      const res = await listProducts()
      setItems(res.items || [])
    } catch (e) {
      setErr(e?.message || 'Failed to load products')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  async function onAdd() {
    setErr('')
    const name = (formValue.name || '').trim()
    const category = (formValue.category || '').trim()
    if (!name || !category) {
      setErr('Please provide name and category.')
      return
    }

    try {
      const created = await createProduct({ name, category })
      setItems((prev) => [created, ...prev])
      setFormValue({ name: '', category: '' })
      setShowAddModal(false)
    } catch (e) {
      setErr(e?.message || 'Failed to create product')
    }
  }

  async function onEdit(row) {
    setErr('')
    setEditing(row)
    setEditValue({ name: row.name || '', category: row.category || '' })
    setShowEditModal(true)
  }

  async function onSaveEdit() {
    if (!editing) return

    const name = (editValue.name || '').trim()
    const category = (editValue.category || '').trim()
    if (!name || !category) {
      setErr('Please provide name and category.')
      return
    }

    setErr('')
    try {
      const updated = await updateProduct(editing.id, { name, category })
      setItems((prev) => prev.map((p) => (p.id === editing.id ? updated : p)))
      setShowEditModal(false)
      setEditing(null)
    } catch (e) {
      setErr(e?.message || 'Failed to update product')
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
      await deleteProduct(deleting.id)
      setItems((prev) => prev.filter((p) => p.id !== deleting.id))
      setShowDeleteModal(false)
      setDeleting(null)
    } catch (e) {
      setErr(e?.message || 'Failed to delete product')
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
        <h2>Products</h2>
        <ButtonGroup>
          <Button appearance="ghost" onClick={refresh} loading={loading}>
            Refresh
          </Button>
          <Button appearance="ghost" onClick={() => setShowAddModal(true)} aria-label="Add product">
            + New Product
          </Button>
        </ButtonGroup>
      </div>

      <div className="panelCard">
        <div className="analyticsGrid">
          <div className="statCard">
            <div className="statLabel">Total products</div>
            <div className="statValue">{stats.total}</div>
          </div>
          {stats.topCategories.map((c) => (
            <div className="statCard" key={c.category}>
              <div className="statLabel">{c.category}</div>
              <div className="statValue">{c.count}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="panelCard">
        <Table height={420} data={items} loading={loading} bordered cellBordered wordWrap>
          <Column width={80} align="left" fixed>
            <HeaderCell>ID</HeaderCell>
            <Cell dataKey="id" />
          </Column>

          <Column flexGrow={2}>
            <HeaderCell>Name</HeaderCell>
            <Cell dataKey="name" />
          </Column>

          <Column flexGrow={1}>
            <HeaderCell>Category</HeaderCell>
            <Cell dataKey="category" />
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
          <Modal.Title>New product</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form fluid formValue={formValue} onChange={setFormValue}>
            <Form.Group>
              <Form.ControlLabel>Name</Form.ControlLabel>
              <Form.Control name="name" accepter={Input} autoComplete="off" />
            </Form.Group>
            <Form.Group>
              <Form.ControlLabel>Category</Form.ControlLabel>
              <Form.Control name="category" accepter={Input} autoComplete="off" />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button onClick={() => setShowAddModal(false)} appearance="subtle">
            Cancel
          </Button>
          <Button onClick={onAdd} appearance="primary" disabled={!formValue.name?.trim() || !formValue.category?.trim()}>
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
          <Modal.Title>Edit product</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form fluid formValue={editValue} onChange={setEditValue}>
            <Form.Group>
              <Form.ControlLabel>Name</Form.ControlLabel>
              <Form.Control name="name" accepter={Input} autoComplete="off" />
            </Form.Group>
            <Form.Group>
              <Form.ControlLabel>Category</Form.ControlLabel>
              <Form.Control name="category" accepter={Input} autoComplete="off" />
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
          <Button
            onClick={onSaveEdit}
            appearance="primary"
            disabled={!editValue.name?.trim() || !editValue.category?.trim()}
          >
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
          <Modal.Title>Delete product</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {deleting ? (
            <div>
              Delete product <strong>{deleting.name}</strong>? This will also delete its sales.
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
