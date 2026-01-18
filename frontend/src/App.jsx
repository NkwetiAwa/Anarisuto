import React, { useState } from 'react'
import { runQuery } from './api'
import ChartView from './components/ChartView.jsx'
import ProductsPanel from './components/ProductsPanel.jsx'
import SalesPanel from './components/SalesPanel.jsx'

import { Container, Content, Header, Nav, Sidebar, Sidenav } from 'rsuite'

const examples = [
  'Show total revenue trend from 2020 to 2026',
  'Compare revenue in 2022 and 2026',
  'Revenue by category in 2024',
  'Top 3 products by revenue in 2026'
]

export default function App() {
  const [view, setView] = useState('chat')
  const [question, setQuestion] = useState(examples[0])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [payload, setPayload] = useState(null)

  // Run query and get result
  async function executeQuery(q) {
    setLoading(true)
    setError('')

    try {
      const result = await runQuery(q)
      setPayload(result)
    } catch (err) {
      setPayload(null)
      setError(err?.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  function onSubmit(e) {
    e.preventDefault()
    executeQuery(question)
  }

  return (
    <Container className="appShell">
      <Sidebar width={260} collapsible={false} className="appSidebar">
        <div className="brand">
          <div className="brandMark">A</div>
          <div className="brandText">
            <div className="brandTitle">Anarisuto</div>
            <div className="brandSub">Smart Analytics</div>
          </div>
        </div>

        <Sidenav appearance="subtle">
          <Sidenav.Body>
            <Nav activeKey={view} onSelect={setView}>
              <Nav.Item eventKey="chat">Dashboard</Nav.Item>
              <Nav.Item eventKey="products">Products</Nav.Item>
              <Nav.Item eventKey="sales">Sales</Nav.Item>
            </Nav>
          </Sidenav.Body>
        </Sidenav>
      </Sidebar>

      <Container>
        <Header className="appHeader">
          <div>
            <div className="headerTitle">Mini Data Intelligence Tool</div>
            <div className="headerSub">Natural Language to SQL</div>
          </div>
        </Header>

        <Content className="appContent">
          {view === 'chat' ? (
            <>
              <div className="panelCard">
                <form className="form" onSubmit={onSubmit}>
                  <label className="label">Question</label>
                  <textarea
                    className="input"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    rows={3}
                    placeholder="e.g., Show total revenue trend from 2020 to 2026"
                  />
                  <div className="actions">
                    <button className="btn" type="submit" disabled={loading || !question.trim()}>
                      {loading ? 'Running…' : 'Submit'}
                    </button>
                    <div className="examples">
                      {examples.map((ex) => (
                        <button
                          key={ex}
                          type="button"
                          className="chip"
                          onClick={() => {setQuestion(ex);executeQuery(ex)}}
                          disabled={loading}
                        >
                          {ex}
                        </button>
                      ))}
                    </div>
                  </div>
                </form>
              </div>

              {error ? <div className="error">{error}</div> : null}

              <div className="panelCard">
                <ChartView payload={payload} />
              </div>
            </>
          ) : null}

          {view === 'products' ? <ProductsPanel /> : null}
          {view === 'sales' ? <SalesPanel /> : null}
        </Content>
      </Container>
    </Container>
  )
}
