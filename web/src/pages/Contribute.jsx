import { useMemo, useState } from 'react'
import styles from './Contribute.module.css'
import { fetchJson } from '../lib/api'

const STEPS = [
  { key: 'upload', label: '上传资料' },
  { key: 'understand', label: '模型理解' },
  { key: 'clarify', label: '补充确认' },
  { key: 'prd', label: 'PRD 草稿' },
]

const TARGETS = [
  ['rules_only', '只生成规则说明'],
  ['playable', '做可玩版本'],
  ['solver', '做自动求解'],
  ['play_and_solve', '可玩 + 自动求解'],
]

const STATUS_LABELS = {
  needs_clarification: '等待补充',
  understanding_ready: '理解已就绪',
  prd_ready: 'PRD 待提交',
  review_pending: '等待维护者 review',
}

const GITHUB_PROGRESS_URL = 'https://github.com/ChatArch/ChatGame'

function currentStep(job) {
  if (!job) return 'upload'
  if (job.status === 'needs_clarification') return 'clarify'
  if (job.status === 'prd_ready' || job.status === 'review_pending') return 'prd'
  return 'understand'
}

function questionAnswered(question, answers) {
  const value = answers[question.id]
  if (Array.isArray(value)) return value.length > 0
  return typeof value === 'string' && value.trim().length > 0
}

export default function Contribute() {
  const [form, setForm] = useState({ name: '', rules: '', target: 'play_and_solve' })
  const [file, setFile] = useState(null)
  const [job, setJob] = useState(null)
  const [answers, setAnswers] = useState({})
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const step = currentStep(job)
  const questions = job?.understanding?.questions || []
  const allAnswered = questions.every(question => questionAnswered(question, answers))
  const canSubmit = form.name.trim() && form.rules.trim() && file && !busy
  const imagePreview = useMemo(() => file ? URL.createObjectURL(file) : null, [file])

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const fd = new FormData()
      fd.append('name', form.name)
      fd.append('rules', form.rules)
      fd.append('target', form.target)
      fd.append('image', file)
      const nextJob = await fetchJson('/api/contributions', { method: 'POST', body: fd }, 30000)
      setJob(nextJob)
      setAnswers({})
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function submitAnswers() {
    setBusy(true)
    setError(null)
    try {
      const payload = {
        answers: questions.map(question => ({
          question_id: question.id,
          value: answers[question.id],
        })),
      }
      const nextJob = await fetchJson(`/api/contributions/${job.job_id}/answers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      setJob(nextJob)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function generatePrd() {
    setBusy(true)
    setError(null)
    try {
      const nextJob = await fetchJson(`/api/contributions/${job.job_id}/generate-prd`, { method: 'POST' })
      setJob(nextJob)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function submitForReview() {
    setBusy(true)
    setError(null)
    try {
      const nextJob = await fetchJson(`/api/contributions/${job.job_id}/approve-prd`, { method: 'POST' })
      setJob(nextJob)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  function answerQuestion(question, value) {
    setAnswers(current => ({ ...current, [question.id]: value }))
  }

  return (
    <div className={styles.wrap}>
      <section className={styles.hero}>
        <span className={styles.eyebrow}>安全受限原型</span>
        <h1 className={styles.title}>接入新游戏向导</h1>
        <p className={styles.desc}>
          上传截图和规则后，系统先判断资料是否足够；不足时只通过有限问题补充，确认后生成 PRD 草稿。当前原型不执行代码、不修改仓库、不创建 PR。
        </p>
      </section>

      <div className={styles.stepper}>
        {STEPS.map((item, index) => (
          <div key={item.key} className={`${styles.step} ${item.key === step ? styles.stepActive : ''}`}>
            <span>{index + 1}</span>
            {item.label}
          </div>
        ))}
      </div>

      {error && <div className={styles.error}>{error}</div>}

      <div className={styles.grid}>
        <section className={styles.panel}>
          <div className={styles.panelHead}>
            <h2>1. 上传资料</h2>
            <small>用户输入只作为待分析数据</small>
          </div>
          <form className={styles.form} onSubmit={submit}>
            <label className={styles.label}>
              游戏名称 <span>*</span>
              <input className={styles.input} value={form.name} placeholder="例：数独 / 数字华容道"
                onChange={e => setForm({ ...form, name: e.target.value })} />
            </label>

            <label className={styles.label}>
              接入目标
              <select className={styles.input} value={form.target}
                onChange={e => setForm({ ...form, target: e.target.value })}>
                {TARGETS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
              </select>
            </label>

            <label className={styles.label}>
              游戏截图 <span>*</span>
              <div className={styles.fileZone} onClick={() => document.getElementById('contribute-file').click()}>
                {imagePreview
                  ? <img src={imagePreview} alt="上传预览" className={styles.preview} />
                  : <span>点击上传 PNG / JPG / WebP，单张不超过 5MB</span>}
                <input id="contribute-file" type="file" accept="image/png,image/jpeg,image/webp" hidden
                  onChange={e => setFile(e.target.files[0])} />
              </div>
              {file && <small className={styles.fileName}>{file.name}</small>}
            </label>

            <label className={styles.label}>
              规则描述 <span>*</span>
              <textarea className={styles.textarea} rows={7}
                placeholder={'描述玩法、限制条件、胜利条件。\n例如：9x9 数独，每行每列和每个 3x3 宫不能重复，填满后过关。'}
                value={form.rules} onChange={e => setForm({ ...form, rules: e.target.value })} />
            </label>

            <button className="btn-primary" type="submit" disabled={!canSubmit}>
              {busy && !job ? '分析中...' : '开始受限分析'}
            </button>
          </form>
        </section>

        <section className={styles.panel}>
          <div className={styles.panelHead}>
            <h2>2. 模型理解</h2>
            <small>{job ? STATUS_LABELS[job.status] || job.status : '等待上传'}</small>
          </div>

          {!job && <div className={styles.empty}>上传资料后，这里会显示结构化理解结果。</div>}

          {job && (
            <div className={styles.understanding}>
              <div className={styles.metricRow}>
                <div><strong>{Math.round((job.understanding.confidence || 0) * 100)}%</strong><span>置信度</span></div>
                <div><strong>{job.understanding.sufficient ? '足够' : '待补充'}</strong><span>资料状态</span></div>
                <div><strong>{job.understanding.board?.type || 'unknown'}</strong><span>局面结构</span></div>
              </div>

              <p className={styles.summary}>{job.understanding.summary}</p>

              <h3>已理解规则</h3>
              <ul className={styles.list}>
                {job.understanding.understood_rules.map(rule => <li key={rule}>{rule}</li>)}
              </ul>

              {job.understanding.missing_information.length > 0 && (
                <>
                  <h3>还需要确认</h3>
                  <ul className={styles.listMuted}>
                    {job.understanding.missing_information.map(item => <li key={item}>{item}</li>)}
                  </ul>
                </>
              )}

              {job.understanding.risk_flags.length > 0 && (
                <div className={styles.risk}>检测到风险：{job.understanding.risk_flags.join(', ')}</div>
              )}
            </div>
          )}
        </section>

        <section className={styles.panel}>
          <div className={styles.panelHead}>
            <h2>3. 有限补充</h2>
            <small>只允许固定问题和白名单动作</small>
          </div>

          {!job && <div className={styles.empty}>等待模型生成需要确认的问题。</div>}

          {job && questions.length === 0 && (
            <div className={styles.readyBox}>
              <strong>资料已足够生成 PRD 草稿。</strong>
              <span>下一步需要用户主动点击生成，系统不会自动执行。</span>
            </div>
          )}

          {questions.length > 0 && (
            <div className={styles.questions}>
              {questions.map(question => (
                <div key={question.id} className={styles.questionCard}>
                  <h3>{question.question}</h3>
                  {question.type === 'single_choice' && question.options.map(option => (
                    <label key={option.value} className={styles.option}>
                      <input type="radio" name={question.id} value={option.value}
                        checked={answers[question.id] === option.value}
                        onChange={() => answerQuestion(question, option.value)} />
                      {option.label}
                    </label>
                  ))}
                  {question.type === 'short_text' && (
                    <textarea className={styles.textarea} rows={4} maxLength={question.max_length || 500}
                      placeholder="请补充一句简短说明"
                      value={answers[question.id] || ''}
                      onChange={e => answerQuestion(question, e.target.value)} />
                  )}
                </div>
              ))}
              <button className="btn-primary" type="button" onClick={submitAnswers} disabled={!allAnswered || busy}>
                提交补充并重新分析
              </button>
            </div>
          )}
        </section>

        <section className={`${styles.panel} ${styles.prdPanel}`}>
          <div className={styles.panelHead}>
            <h2>4. PRD 草稿</h2>
            <small>{job?.prd ? '已生成' : '等待生成'}</small>
          </div>

          {!job?.prd && (
            <div className={styles.empty}>
              模型理解确认后，可以生成 PRD 草稿。第一版提交给维护者 review 后停止，不继续执行实现动作。
            </div>
          )}

          {job?.prd && <pre className={styles.prd}>{job.prd}</pre>}

          {job?.status === 'review_pending' && (
            <div className={styles.submittedBox}>
              <strong>已提交审核</strong>
              <span>{job.review?.message || '维护者 review 后会决定是否进入实现阶段。'}</span>
              <a href={job.review?.progress_url || GITHUB_PROGRESS_URL} target="_blank" rel="noreferrer">
                在 GitHub 查看项目进展
              </a>
            </div>
          )}

          <div className={styles.actions}>
            <button className="btn-primary" type="button" onClick={generatePrd}
              disabled={!job || job.status !== 'understanding_ready' || busy}>
              生成 PRD 草稿
            </button>
            <button className="btn-ghost" type="button" onClick={submitForReview}
              disabled={!job?.prd || job.status !== 'prd_ready' || busy}>
              提交维护者 review
            </button>
          </div>
        </section>
      </div>
    </div>
  )
}
