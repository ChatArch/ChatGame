import { useState } from 'react'
import styles from './Contribute.module.css'

export default function Contribute() {
  const [form, setForm] = useState({ name: '', rules: '', contact: '' })
  const [file, setFile]   = useState(null)
  const [toast, setToast] = useState(false)

  function submit(e) {
    e.preventDefault()
    setToast(true)
    setTimeout(() => setToast(false), 3000)
    setForm({ name: '', rules: '', contact: '' })
    setFile(null)
  }

  return (
    <div className={styles.wrap}>
      <h1 className={styles.title}>贡献游戏</h1>
      <p className={styles.desc}>
        想让 chatgame 支持新的谜题游戏？填写下方信息，我们会评估并更新游戏库。
      </p>

      <div className={styles.notice}>
        当前为预留入口，提交后不触发自动流程。
      </div>

      <form className={styles.form} onSubmit={submit}>
        <label className={styles.label}>
          游戏名称 <span className={styles.required}>*</span>
          <input required className={styles.input} placeholder="例：数独 / 数字华容道"
            value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
        </label>

        <label className={styles.label}>
          游戏截图
          <div className={styles.fileZone} onClick={() => document.getElementById('cfile').click()}>
            {file ? file.name : '点击上传截图（PNG / JPG）'}
            <input id="cfile" type="file" accept="image/*" hidden
              onChange={e => setFile(e.target.files[0])} />
          </div>
        </label>

        <label className={styles.label}>
          规则描述 <span className={styles.required}>*</span>
          <textarea required className={styles.textarea} rows={5}
            placeholder="简要说明游戏规则：棋盘结构、约束条件、胜利条件…"
            value={form.rules} onChange={e => setForm({ ...form, rules: e.target.value })} />
        </label>

        <label className={styles.label}>
          联系方式（可选）
          <input className={styles.input} placeholder="邮箱 / GitHub 用户名"
            value={form.contact} onChange={e => setForm({ ...form, contact: e.target.value })} />
        </label>

        <button type="submit" className="btn-primary" style={{ marginTop: 8 }}>
          提交
        </button>
      </form>

      {toast && (
        <div className={styles.toast}>已收到，感谢贡献！</div>
      )}
    </div>
  )
}
