import { useMemo, useState } from 'react'
import { fetchJson } from '../lib/api'
import styles from './Contribute.module.css'

const TARGET_TYPES = [
  { value: 'docs_only', label: '只整理规则文档' },
  { value: 'playable', label: '做可玩版本' },
  { value: 'solver', label: '做自动求解' },
  { value: 'playable_solver', label: '可玩 + 自动求解' },
]

const STEPS = [
  { key: 'upload', label: '上传资料' },
  { key: 'analyze', label: '模型分析' },
  { key: 'user-review', label: '用户 Review' },
  { key: 'workflow', label: '进入工作流' },
]

function activeStep(status) {
  if (!status) return 0
  if (status === 'needs_clarification' || status === 'understanding_ready') return 1
  if (status === 'prd_ready' || status === 'needs_edit') return 2
  if (status === 'review_pending') return 3
  return 0
}

function defaultAnswer(question) {
  return question.options?.[0]?.value || ''
}

export default function Contribute() {
  const [form, setForm] = useState({ name: '', rules: '', target_type: 'playable_solver' })
  const [file, setFile] = useState(null)
  const [job, setJob] = useState(null)
  const [answers, setAnswers] = useState({})
  const [prdDraft, setPrdDraft] = useState('')
  const [editingPrd, setEditingPrd] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const questions = job?.understanding?.questions || []
  const currentStep = activeStep(job?.status)
  const canUpload = form.name && form.rules && file && !loading
  const canAnswer = questions.every(q => answers[q.id]) && !loading
  const canGeneratePrd = job?.status !== 'needs_clarification' && !loading

  const statusText = useMemo(() => {
    const map = {
      needs_clarification: '模型分析发现资料里还有模糊点，需要先补充确认。',
      understanding_ready: '模型分析完成，当前资料足够，可以直接生成 PRD 草稿。',
      prd_ready: 'PRD 已生成，进入用户 Review；可编辑、返回上一步，或确认进入工作流。',
      review_pending: '已进入后续工作流，当前等待维护者 review 后决定是否启动开发。',
      needs_edit: '维护者要求补充或修改 PRD 后再提交。',
    }
    return map[job?.status] || '还没有创建接入申请。'
  }, [job?.status])

  async function run(action) {
    setLoading(true)
    setError('')
    setMessage('')
    try {
      await action()
    } catch (err) {
      setError(err.message || '请求失败')
    } finally {
      setLoading(false)
    }
  }

  function updateQuestionAnswer(questionId, value) {
    setAnswers(prev => ({ ...prev, [questionId]: value }))
  }

  function hydrateAnswers(nextJob) {
    const next = {}
    for (const question of nextJob?.understanding?.questions || []) {
      next[question.id] = defaultAnswer(question)
    }
    setAnswers(next)
  }

  function submitUpload(event) {
    event.preventDefault()
    run(async () => {
      const data = new FormData()
      data.append('name', form.name)
      data.append('rules', form.rules)
      data.append('target_type', form.target_type)
      data.append('image', file)
      const created = await fetchJson('/api/contributions', { method: 'POST', body: data }, 20000)
      setJob(created)
      setPrdDraft(created.prd || '')
      hydrateAnswers(created)
      setMessage('已创建接入申请。系统只会做结构化理解，不会自动执行代码。')
    })
  }

  function submitAnswers() {
    run(async () => {
      const payload = {
        answers: questions.map(question => ({
          question_id: question.id,
          value: answers[question.id],
        })),
      }
      const updated = await fetchJson(`/api/contributions/${job.id}/answers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      setJob(updated)
      hydrateAnswers(updated)
      setMessage('补充信息已提交，模型分析已重新整理。')
    })
  }

  function generatePrd() {
    run(async () => {
      const updated = await fetchJson(`/api/contributions/${job.id}/generate-prd`, { method: 'POST' }, 20000)
      setJob(updated)
      setPrdDraft(updated.prd || '')
      setEditingPrd(false)
      setMessage('PRD 已生成，请先用户 Review；确认后再进入后续工作流。')
    })
  }

  function returnToAnalysis() {
    run(async () => {
      const updated = await fetchJson(`/api/contributions/${job.id}/reanalyze`, { method: 'POST' }, 20000)
      setJob(updated)
      hydrateAnswers(updated)
      setEditingPrd(false)
      setMessage('已返回模型分析。可以处理模糊点，或在资料足够时重新生成 PRD。')
    })
  }

  function savePrd() {
    run(async () => {
      const updated = await fetchJson(`/api/contributions/${job.id}/edit-prd`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: prdDraft }),
      })
      setJob(updated)
      setEditingPrd(false)
      setMessage('PRD 已保存，仍处于提交 review 前的草稿状态。')
    })
  }

  function submitReview() {
    run(async () => {
      const updated = await fetchJson(`/api/contributions/${job.id}/submit-review`, { method: 'POST' })
      setJob(updated)
      setMessage(updated.user_message)
    })
  }

  function resetFlow() {
    setJob(null)
    setAnswers({})
    setPrdDraft('')
    setEditingPrd(false)
    setMessage('')
    setError('')
  }

  return (
    <div className={styles.wrap}>
      <section className={styles.hero}>
        <p className={styles.eyebrow}>受限交互式接入流程</p>
        <h1 className={styles.title}>接入新游戏向导</h1>
        <p className={styles.desc}>
          上传截图和规则后，系统进入模型分析环节，先判断资料是否足够；发现模糊点时才提供选项或按钮让用户确认。
          前两步用于确保 PRD 完整，用户 Review 确认后才进入后续工作流。
        </p>
      </section>

      <div className={styles.steps}>
        {STEPS.map((step, index) => (
          <div key={step.key} className={`${styles.step} ${index <= currentStep ? styles.stepActive : ''}`}>
            <span>{index + 1}</span>
            {step.label}
          </div>
        ))}
      </div>

      <div className={styles.layout}>
        <main className={styles.panel}>
          {!job && (
            <form className={styles.form} onSubmit={submitUpload}>
              <label className={styles.label}>
                游戏名称 <span className={styles.required}>*</span>
                <input
                  required
                  className={styles.input}
                  placeholder="例：数独 / 数字华容道"
                  value={form.name}
                  onChange={event => setForm({ ...form, name: event.target.value })}
                />
              </label>

              <label className={styles.label}>
                接入目标
                <select
                  className={styles.input}
                  value={form.target_type}
                  onChange={event => setForm({ ...form, target_type: event.target.value })}
                >
                  {TARGET_TYPES.map(type => <option key={type.value} value={type.value}>{type.label}</option>)}
                </select>
              </label>

              <label className={styles.label}>
                游戏截图 <span className={styles.required}>*</span>
                <div className={styles.fileZone} onClick={() => document.getElementById('contribution-file').click()}>
                  {file ? <span>{file.name}</span> : '点击上传截图（PNG / JPG / WebP，最多 5MB）'}
                  <input
                    id="contribution-file"
                    type="file"
                    accept="image/png,image/jpeg,image/webp"
                    hidden
                    required
                    onChange={event => setFile(event.target.files?.[0] || null)}
                  />
                </div>
              </label>

              <label className={styles.label}>
                规则描述 <span className={styles.required}>*</span>
                <textarea
                  required
                  className={styles.textarea}
                  rows={7}
                  placeholder={'描述棋盘结构、操作规则、胜利条件和希望第一版做到哪里。'}
                  value={form.rules}
                  onChange={event => setForm({ ...form, rules: event.target.value })}
                />
              </label>

              <button type="submit" className="btn-primary" disabled={!canUpload}>
                创建接入申请
              </button>
            </form>
          )}

          {job && (
            <div className={styles.workspace}>
              <div className={styles.statusCard}>
                <span className={styles.badge}>{job.status}</span>
                <h2>{job.name}</h2>
                <p>{statusText}</p>
              </div>

              <section className={styles.section}>
                <h3>模型分析</h3>
                <p>{job.understanding?.summary}</p>
                <div className={styles.metaGrid}>
                  <span>置信度：{Math.round((job.understanding?.confidence || 0) * 100)}%</span>
                  <span>类型：{job.understanding?.game_type || 'unknown'}</span>
                  <span>截图：{job.image?.width} × {job.image?.height}</span>
                </div>
                <ul className={styles.list}>
                  {(job.understanding?.understood_rules || []).map(rule => <li key={rule}>{rule}</li>)}
                </ul>
              </section>

              {questions.length > 0 && job.status !== 'review_pending' && (
                <section className={styles.section}>
                  <h3>发现的模糊点</h3>
                  {questions.map(question => (
                    <div key={question.id} className={styles.question}>
                      <strong>{question.question}</strong>
                      <div className={styles.options}>
                        {question.options.map(option => (
                          <label key={option.value} className={styles.option}>
                            <input
                              type="radio"
                              name={question.id}
                              checked={answers[question.id] === option.value}
                              onChange={() => updateQuestionAnswer(question.id, option.value)}
                            />
                            {option.label}
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                  <button className="btn-primary" onClick={submitAnswers} disabled={!canAnswer}>
                    提交补充并重新分析
                  </button>
                </section>
              )}

              {job.status !== 'review_pending' && (
                <section className={styles.section}>
                  <h3>用户 Review PRD</h3>
                  {!job.prd && <p className={styles.muted}>模型分析确认资料足够后，可以生成 PRD。用户在这里 review，可返回模型分析继续补充；确认后进入后续工作流。</p>}
                  {job.prd && !editingPrd && <pre className={styles.prdPreview}>{job.prd}</pre>}
                  {job.prd && editingPrd && (
                    <textarea
                      className={`${styles.textarea} ${styles.prdEditor}`}
                      value={prdDraft}
                      onChange={event => setPrdDraft(event.target.value)}
                    />
                  )}
                  <div className={styles.actions}>
                    <button className="btn-primary" onClick={generatePrd} disabled={!canGeneratePrd}>
                      {job.prd ? '重新生成 PRD' : '生成 PRD'}
                    </button>
                    {job.prd && !editingPrd && <button className={styles.secondaryBtn} onClick={() => setEditingPrd(true)}>编辑 PRD</button>}
                    {job.prd && !editingPrd && <button className={styles.secondaryBtn} onClick={returnToAnalysis} disabled={loading}>返回模型分析</button>}
                    {job.prd && editingPrd && <button className={styles.secondaryBtn} onClick={savePrd} disabled={loading}>保存 PRD</button>}
                    {job.prd && <button className={styles.reviewBtn} onClick={submitReview} disabled={loading}>确认并进入工作流</button>}
                  </div>
                </section>
              )}

              {job.status === 'review_pending' && (
                <section className={`${styles.section} ${styles.doneBox}`}>
                  <h3>已提交</h3>
                  <p>你的需求已经进入后续工作流。当前会先等待维护者 review，再决定是否启动真实开发。</p>
                  <a href={job.github_url} target="_blank" rel="noreferrer">在 GitHub 查看项目进展</a>
                  <button className={styles.secondaryBtn} onClick={() => setEditingPrd(true)}>需要修改时可重新编辑 PRD</button>
                  {editingPrd && (
                    <>
                      <textarea
                        className={`${styles.textarea} ${styles.prdEditor}`}
                        value={prdDraft || job.prd || ''}
                        onChange={event => setPrdDraft(event.target.value)}
                      />
                      <button className="btn-primary" onClick={savePrd} disabled={loading}>保存为草稿，稍后再提交</button>
                    </>
                  )}
                </section>
              )}
            </div>
          )}
        </main>

        <aside className={styles.aside}>
          <h3>安全边界</h3>
          <ul>
            <li>上传内容只作为数据，不作为系统指令。</li>
            <li>模型输出走固定 JSON 和白名单按钮。</li>
            <li>本阶段不执行 shell、不改仓库、不创建 PR。</li>
            <li>提交后进入 review_pending，等待维护者审核。</li>
          </ul>
          {job && <button className={styles.secondaryBtn} onClick={resetFlow}>新建另一个申请</button>}
        </aside>
      </div>

      {message && <div className={styles.toast}>{message}</div>}
      {error && <div className={`${styles.toast} ${styles.errorToast}`}>{error}</div>}
    </div>
  )
}
