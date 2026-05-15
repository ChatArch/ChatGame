import { useState } from 'react'
import styles from './Contribute.module.css'

const STEPS = [
  { n: 1, label: '上传截图 + 描述规则', desc: '提供游戏截图和文字规则说明' },
  { n: 2, label: 'Agent CLI 分析', desc: '后端调用 Agent 理解规则、生成解析与求解代码' },
  { n: 3, label: '自动测试', desc: 'Agent 对生成代码跑测试，验证求解逻辑正确性' },
  { n: 4, label: '接入 chatgame', desc: '新游戏自动注册，出现在游戏库和求解器中' },
]

export default function Contribute() {
  const [form, setForm] = useState({ name: '', rules: '' })
  const [file, setFile]   = useState(null)
  const [toast, setToast] = useState(false)

  function submit(e) {
    e.preventDefault()
    setToast(true)
    setTimeout(() => setToast(false), 3500)
    setForm({ name: '', rules: '' })
    setFile(null)
  }

  return (
    <div className={styles.wrap}>
      <h1 className={styles.title}>添加新游戏</h1>
      <p className={styles.desc}>
        提交游戏截图与规则描述，后端将调用 Agent CLI 自动分析并实现求解逻辑，接入 chatgame。
      </p>

      {/* 流程示意 */}
      <div className={styles.pipeline}>
        {STEPS.map((s, i) => (
          <div key={s.n} className={styles.pipelineItem}>
            <div className={styles.pipelineStep}>
              <span className={styles.stepCircle}>{s.n}</span>
              <strong>{s.label}</strong>
              <span className={styles.stepDesc}>{s.desc}</span>
            </div>
            {i < STEPS.length - 1 && <div className={styles.arrow}>→</div>}
          </div>
        ))}
      </div>

      <div className={styles.notice}>
        当前为预留 UI，提交后不触发真实 Agent 流程。
      </div>

      <form className={styles.form} onSubmit={submit}>
        <label className={styles.label}>
          游戏名称 <span className={styles.required}>*</span>
          <input required className={styles.input} placeholder="例：数独 / 数字华容道"
            value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
        </label>

        <label className={styles.label}>
          游戏截图 <span className={styles.required}>*</span>
          <div className={styles.fileZone} onClick={() => document.getElementById('cfile').click()}>
            {file
              ? <span style={{ color: 'var(--accent)' }}>{file.name}</span>
              : '点击上传截图（PNG / JPG）'}
            <input id="cfile" type="file" accept="image/*" hidden required
              onChange={e => setFile(e.target.files[0])} />
          </div>
        </label>

        <label className={styles.label}>
          规则描述 <span className={styles.required}>*</span>
          <textarea required className={styles.textarea} rows={6}
            placeholder={'描述游戏规则，例如：\n• 棋盘大小和结构\n• 放置约束（行列唯一、区域限制等）\n• 胜利条件'}
            value={form.rules} onChange={e => setForm({ ...form, rules: e.target.value })} />
        </label>

        <button type="submit" className="btn-primary"
          disabled={!form.name || !form.rules || !file}
          style={{ marginTop: 4 }}>
          提交给 Agent
        </button>
      </form>

      {toast && (
        <div className={styles.toast}>
          已提交，Agent 将分析你的游戏规则并实现求解逻辑。
        </div>
      )}
    </div>
  )
}
