import {
  ArrowRight,
  Ban,
  Check,
  Circle,
  CircleAlert,
  CircleCheckBig,
  CircleHelp,
  createIcons,
  FileCheck2,
  FileSearch,
  FileText,
  Info,
  LockKeyhole,
  RotateCcw,
  ScanText,
  ShieldCheck,
  Trash2,
  Upload,
  X,
} from 'lucide'

import './style.css'
import skylineImage from './assets/singapore-skyline-landscape.jpg'
import {
  ApiError,
  createAnalysis,
  createIdempotencyKey,
  deleteAnalysis,
  extractTerms,
  reviewPrivacy,
  reviewTerms,
  scanPrivacy,
  uploadDocument,
} from './api.js'

const app = document.querySelector('#app')
const renderedIcons = {
  ArrowRight,
  Ban,
  Check,
  Circle,
  CircleAlert,
  CircleCheckBig,
  CircleHelp,
  FileCheck2,
  FileSearch,
  FileText,
  Info,
  LockKeyhole,
  RotateCcw,
  ScanText,
  ShieldCheck,
  Trash2,
  Upload,
  X,
}

const privacyLabels = {
  name: 'Name',
  national_id: 'National ID',
  contact: 'Contact detail',
  address: 'Address',
  policy_number: 'Policy number',
  account_detail: 'Account detail',
  signature: 'Signature',
  health_information: 'Health information',
}

const privacyDescriptions = {
  name: 'A person’s name',
  national_id: 'NRIC or another national ID',
  contact: 'Email address or phone number',
  address: 'Home or mailing address',
  policy_number: 'Policy or certificate number',
  account_detail: 'Bank or payment account details',
  signature: 'A signature or signed-by line',
  health_information: 'A personal medical-history or health-declaration field',
}

const termLabels = {
  'commitment.insurer': 'Insurer',
  'commitment.product_name': 'Product name',
  'commitment.document_type': 'Document type',
  'commitment.issue_date': 'Issue date',
  'commitment.policy_status': 'Policy status',
  'premium.amount': 'Premium amount',
  'premium.frequency': 'Payment frequency',
  'premium.payment_duration': 'Payment duration',
  'premium.escalation': 'Premium escalation',
  'coverage.commencement': 'Coverage commencement',
  'coverage.expiry_or_maturity': 'Coverage expiry or maturity',
  'exit.free_look_period': 'Free-look period',
}

const steps = [
  ['upload', 'Add PDFs'],
  ['privacy', 'Protect details'],
  ['terms', 'Check details'],
  ['summary', 'Done'],
]

const createInitialState = () => ({
  view: 'upload',
  purpose: 'considering_offer',
  decisionDate: '',
  privacyAcknowledged: false,
  files: [],
  analysisId: '',
  documents: [],
  findings: [],
  privacyActions: {},
  extraction: null,
  busy: false,
  status: '',
  error: '',
  keys: {
    uploads: [],
    privacyScan: '',
    privacyReview: '',
    extraction: '',
    termReview: '',
  },
})

let state = createInitialState()
let renderedView = state.view

const escapeHtml = (value = '') => String(value)
  .replaceAll('&', '&amp;')
  .replaceAll('<', '&lt;')
  .replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;')
  .replaceAll("'", '&#039;')

const formatBytes = (bytes) => {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

const capitalize = (value) => value.charAt(0).toUpperCase() + value.slice(1)

const formatDate = (value) => {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value)
  if (!match) return value
  const [, year, month, day] = match
  return new Intl.DateTimeFormat('en-SG', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(Date.UTC(Number(year), Number(month) - 1, Number(day))))
}

const formatTermValue = (term) => {
  if (term.value.state !== 'present') return 'Not found in these files'
  const value = term.value.value
  if (term.taxonomy_key === 'premium.amount') {
    return `${value.currency} ${value.amount}`
  }
  if (term.taxonomy_key === 'premium.payment_duration') {
    return `${value.duration} ${value.unit}`
  }
  if (term.taxonomy_key === 'premium.escalation') {
    return `${value.percentage}% ${value.frequency}`
  }
  if (term.taxonomy_key === 'exit.free_look_period') {
    return `${value.duration} ${value.unit}`
  }
  if (term.taxonomy_key === 'commitment.document_type') {
    return capitalize(String(value).replaceAll('_', ' '))
  }
  if (
    term.taxonomy_key === 'commitment.issue_date'
    || term.taxonomy_key === 'coverage.commencement'
    || term.taxonomy_key === 'coverage.expiry_or_maturity'
  ) {
    return formatDate(String(value))
  }
  const text = String(value).replaceAll('-', ' ')
  return capitalize(text)
}

const activeStep = () => Math.max(0, steps.findIndex(([id]) => id === state.view))

const stepRail = () => {
  const current = activeStep()
  return `
    <nav class="step-rail" aria-label="Review progress">
      <p class="rail-label">Your progress</p>
      <ol>
        ${steps.map(([id, label], index) => `
          <li class="${index === current ? 'is-active' : ''} ${index < current ? 'is-complete' : ''}">
            <span class="step-marker">${index < current ? '<i data-lucide="check"></i>' : index + 1}</span>
            <span>${escapeHtml(label)}</span>
          </li>
        `).join('')}
      </ol>
      <div class="local-note">
        <i data-lucide="lock-keyhole"></i>
        <p><strong>Your files stay here</strong><span>They are read on this computer and never uploaded to an AI service.</span></p>
      </div>
    </nav>
  `
}

const header = () => `
  <header class="app-header">
    <button class="brand" type="button" data-action="restart" aria-label="Check another policy">
      <span class="brand-mark"><i data-lucide="shield-check"></i></span>
      <span>Before You Commit</span>
    </button>
    <div class="header-status">
      <span class="local-status"><i data-lucide="circle"></i> Files stay on this computer</span>
      ${state.analysisId ? `
        <button class="icon-button" type="button" data-action="delete" title="Delete this check" aria-label="Delete this check" ${state.busy ? 'disabled' : ''}>
          <i data-lucide="trash-2"></i>
        </button>
      ` : ''}
    </div>
  </header>
`

const errorBanner = () => state.error ? `
  <div class="error-banner" role="alert">
    <i data-lucide="circle-alert"></i>
    <span>${escapeHtml(state.error)}</span>
  </div>
` : ''

const busyOverlay = () => state.busy ? `
  <div class="busy-bar" role="status" aria-live="polite">
    <span class="spinner" aria-hidden="true"></span>
    <span>${escapeHtml(state.status)}</span>
  </div>
` : ''

const uploadView = () => `
  <section class="workspace view-enter" aria-labelledby="upload-title">
    <div class="workspace-heading">
      <p class="eyebrow">Understand it before you sign it</p>
      <h1 id="upload-title">Turn a policy PDF into a short, useful checklist.</h1>
      <p class="lede">Upload the documents for one life-insurance policy. We’ll pull out key costs and dates, show what we could not find, and give you a clearer list of things to check. This is a document check, not a product recommendation.</p>
    </div>

    <form id="upload-form" class="upload-form">
      <fieldset class="purpose-fieldset">
        <legend>What are you checking?</legend>
        <div class="segmented-control">
          <label>
            <input type="radio" name="purpose" value="considering_offer" ${state.purpose === 'considering_offer' ? 'checked' : ''}>
            <span>An offer I’m considering</span>
          </label>
          <label>
            <input type="radio" name="purpose" value="reviewing_issued_policy" ${state.purpose === 'reviewing_issued_policy' ? 'checked' : ''}>
            <span>A policy I just received</span>
          </label>
        </div>
      </fieldset>

      <label class="date-field">
        <span>Deadline or free-look date <small>Optional</small></span>
        <input type="date" name="decision-date" value="${escapeHtml(state.decisionDate)}">
      </label>

      <div class="upload-zone ${state.files.length ? 'has-files' : ''}" id="upload-zone">
        <input class="sr-only" id="pdf-files" type="file" accept="application/pdf,.pdf" multiple>
        <div class="upload-icon"><i data-lucide="upload"></i></div>
        <div>
          <strong>Add your policy PDFs</strong>
          <span>Up to 8 PDFs · 20 MB and 100 pages each</span>
        </div>
        <label class="secondary-button" for="pdf-files">Choose PDFs</label>
      </div>

      ${state.files.length ? `
        <div class="file-list" aria-label="Selected files">
          ${state.files.map((file, index) => `
            <div class="file-row">
              <i data-lucide="file-text"></i>
              <p><strong>${escapeHtml(file.name)}</strong><span>${formatBytes(file.size)}</span></p>
              <button class="icon-button" type="button" data-remove-file="${index}" title="Remove file" aria-label="Remove ${escapeHtml(file.name)}">
                <i data-lucide="x"></i>
              </button>
            </div>
          `).join('')}
        </div>
      ` : ''}

      <label class="privacy-acknowledgement">
        <input type="checkbox" name="privacy-acknowledgement" ${state.privacyAcknowledged ? 'checked' : ''} required>
        <span><strong>Keep my documents on this computer.</strong> They will not be sent to an AI service. Temporary copies are removed when I delete this check or it expires.</span>
      </label>

      ${errorBanner()}
      <div class="form-actions">
        <span>${state.files.length ? `${state.files.length} file${state.files.length === 1 ? '' : 's'} selected` : 'No files selected'}</span>
        <button class="primary-button" type="submit" ${state.busy || !state.files.length || !state.privacyAcknowledged ? 'disabled' : ''}>
          Check my documents <i data-lucide="arrow-right"></i>
        </button>
      </div>
    </form>
  </section>

  <aside class="visual-panel" style="--panel-image: url('${skylineImage}')" aria-label="Singapore skyline">
    <div class="visual-caption">
      <span class="mono">LIFE INSURANCE · SINGAPORE</span>
      <p>Know what the paperwork says.</p>
    </div>
    <dl>
      <div><dt>Your files</dt><dd>Stay local</dd></div>
      <div><dt>Sent to AI</dt><dd>Never</dd></div>
      <div><dt>Product advice</dt><dd>None</dd></div>
    </dl>
  </aside>
`

const privacyGroups = () => Object.values(state.findings.reduce((groups, finding) => {
  const group = groups[finding.category] || {
    category: finding.category,
    findings: [],
    pages: new Set(),
  }
  group.findings.push(finding)
  group.pages.add(finding.region.page)
  groups[finding.category] = group
  return groups
}, {})).map((group) => ({ ...group, pages: [...group.pages].sort((left, right) => left - right) }))

const pageList = (pages) => pages.length <= 5
  ? pages.join(', ')
  : `${pages.slice(0, 4).join(', ')} and ${pages.length - 4} more`

const parserLabel = (parserPath) => parserPath === 'ocr' ? 'Scanned with OCR' : 'Text read directly'

const privacyView = () => {
  const groups = privacyGroups()
  return `
    <section class="workspace review-workspace view-enter" aria-labelledby="privacy-title">
      <div class="workspace-heading compact-heading">
        <p class="eyebrow">Protect personal details</p>
        <h1 id="privacy-title">We found a few things you may want to hide.</h1>
        <p class="lede">The actual values are hidden here. We’ve selected the safest option for each type, so you can review the list and continue in one click.</p>
      </div>

      <form id="privacy-form">
        <div class="review-toolbar">
          <span>${groups.length} type${groups.length === 1 ? '' : 's'} of private information</span>
          <span>${state.findings.length} place${state.findings.length === 1 ? '' : 's'} found</span>
        </div>
        <div class="privacy-groups">
          ${groups.map((group, index) => `
            <fieldset class="privacy-group">
              <legend class="sr-only">How to handle ${escapeHtml(privacyLabels[group.category] || group.category)}</legend>
              <span class="finding-index mono">${String(index + 1).padStart(2, '0')}</span>
              <div class="privacy-group-copy">
                <h2>${escapeHtml(privacyLabels[group.category] || group.category)}</h2>
                <p>${escapeHtml(privacyDescriptions[group.category] || 'Private information')} · ${group.findings.length} place${group.findings.length === 1 ? '' : 's'} on page${group.pages.length === 1 ? '' : 's'} ${pageList(group.pages)}</p>
              </div>
              <div class="privacy-choice-grid">
                ${[
                  ['redact', 'Hide it', 'Recommended'],
                  ['exclude', 'Skip those lines', 'May remove useful details'],
                  ['keep', 'Use as-is', 'Stays on this computer'],
                ].map(([value, label, hint]) => `
                  <label>
                    <input type="radio" name="privacy-category-${escapeHtml(group.category)}" value="${value}" data-privacy-category="${escapeHtml(group.category)}" ${group.findings.every((finding) => state.privacyActions[finding.finding_id] === value) ? 'checked' : ''}>
                    <span><strong>${label}</strong><small>${hint}</small></span>
                  </label>
                `).join('')}
              </div>
            </fieldset>
          `).join('')}
        </div>
        ${errorBanner()}
        <div class="sticky-actions">
          <p><i data-lucide="shield-check"></i> “Hide it” replaces the private value before the document is checked.</p>
          <button class="primary-button" type="submit" ${state.busy ? 'disabled' : ''}>
            Protect details and continue <i data-lucide="arrow-right"></i>
          </button>
        </div>
      </form>
    </section>
    <aside class="context-panel">
      <p class="eyebrow">Your documents</p>
      ${state.documents.map((document) => `
        <div class="document-meta">
          <i data-lucide="file-check-2"></i>
          <p><strong>${document.page_count} page${document.page_count === 1 ? '' : 's'}</strong><span>${parserLabel(document.parser_path)} · ${formatBytes(document.size_bytes)}</span></p>
        </div>
      `).join('')}
    </aside>
  `
}

const sourcePages = (term) => {
  const pages = (state.extraction?.spans || [])
    .filter((span) => term.source_span_ids.includes(span.span_id))
    .map((span) => span.region.page)
  return [...new Set(pages)].sort((left, right) => left - right)
}

const termRows = (terms, offset = 0) => terms.map((term, index) => {
  const pages = sourcePages(term)
  const unknown = term.value.state !== 'present'
  return `
    <article class="term-row ${unknown ? 'is-unknown' : ''}">
      <span class="term-index mono">${String(offset + index + 1).padStart(2, '0')}</span>
      <div class="term-copy">
        <p>${escapeHtml(termLabels[term.taxonomy_key] || term.taxonomy_key)}</p>
        <h3>${escapeHtml(formatTermValue(term))}</h3>
      </div>
      <div class="term-source">
        <span class="state-chip ${unknown ? 'is-warning' : 'is-present'}">${unknown ? 'Not found' : 'Found'}</span>
        <small>${pages.length ? `Page ${pages.join(', ')}` : 'No matching page'}</small>
      </div>
    </article>
  `
}).join('')

const termsView = () => {
  const foundTerms = state.extraction.terms.filter((term) => term.value.state === 'present')
  const missingTerms = state.extraction.terms.filter((term) => term.value.state !== 'present')
  return `
    <section class="workspace review-workspace view-enter" aria-labelledby="terms-title">
      <div class="workspace-heading compact-heading">
        <p class="eyebrow">Key policy details</p>
        <h1 id="terms-title">Here’s what we found in your documents.</h1>
        <p class="lede">Check these details against the PDF. “Not found” means we could not locate a clear answer in the files you gave us.</p>
      </div>

      <form id="terms-form">
        ${foundTerms.length ? `
          <section class="term-section" aria-labelledby="found-terms-title">
            <div class="term-section-heading">
              <h2 id="found-terms-title">Found in your files</h2>
              <span>${foundTerms.length}</span>
            </div>
            <div class="term-list">${termRows(foundTerms)}</div>
          </section>
        ` : ''}
        ${missingTerms.length ? `
          <section class="term-section" aria-labelledby="missing-terms-title">
            <div class="term-section-heading">
              <h2 id="missing-terms-title">Questions to follow up</h2>
              <span>${missingTerms.length}</span>
            </div>
            <div class="term-list">${termRows(missingTerms, foundTerms.length)}</div>
          </section>
        ` : ''}
        ${errorBanner()}
        <div class="sticky-actions">
          <p><i data-lucide="info"></i> A missing detail is a question to raise with the insurer, not proof that the term does not apply.</p>
          <button class="primary-button" type="submit" ${state.busy ? 'disabled' : ''}>
            These details look right <i data-lucide="check"></i>
          </button>
        </div>
      </form>
    </section>
    <aside class="context-panel evidence-panel">
      <p class="eyebrow">Where this came from</p>
      <h2>Your PDFs</h2>
      <p>Every detail marked “Found” points back to a page in the documents you uploaded.</p>
      <div class="boundary-note"><i data-lucide="ban"></i><span>This tool does not rank policies or tell you whether to buy one.</span></div>
    </aside>
  `
}

const summaryView = () => {
  const unknownCount = state.extraction.terms.filter((term) => term.value.state !== 'present').length
  return `
    <section class="workspace summary-workspace view-enter" aria-labelledby="summary-title">
      <div class="completion-mark"><i data-lucide="circle-check-big"></i></div>
      <div class="workspace-heading compact-heading">
        <p class="eyebrow">Document check complete</p>
        <h1 id="summary-title">You now have a clearer view of the paperwork.</h1>
        <p class="lede">Keep the missing details as questions for the insurer or adviser. This summary describes the files you supplied; it does not recommend the policy.</p>
      </div>

      <dl class="summary-terms">
        ${state.extraction.terms.map((term) => `
          <div>
            <dt>${escapeHtml(termLabels[term.taxonomy_key] || term.taxonomy_key)}</dt>
            <dd>${escapeHtml(formatTermValue(term))}</dd>
          </div>
        `).join('')}
      </dl>

      <div class="completion-notes">
        <article>
          <i data-lucide="file-search"></i>
          <p><strong>${state.documents.length} document${state.documents.length === 1 ? '' : 's'} checked</strong><span>${state.documents.reduce((sum, item) => sum + item.page_count, 0)} pages read on this computer</span></p>
        </article>
        <article class="${unknownCount ? 'has-warning' : ''}">
          <i data-lucide="circle-help"></i>
          <p><strong>${unknownCount} question${unknownCount === 1 ? '' : 's'} to follow up</strong><span>Ask about anything we could not find clearly.</span></p>
        </article>
      </div>

      ${errorBanner()}
      <div class="summary-actions">
        <button class="secondary-button" type="button" data-action="restart"><i data-lucide="rotate-ccw"></i> Check another policy</button>
        <button class="danger-button" type="button" data-action="delete"><i data-lucide="trash-2"></i> Delete this check</button>
      </div>
    </section>
    <aside class="context-panel final-panel">
      <p class="eyebrow">One important limit</p>
      <h2>This checks documents. It doesn’t choose for you.</h2>
      <p>Confirm unclear or missing details directly with the insurer or adviser before you sign.</p>
    </aside>
  `
}

const view = () => {
  if (state.view === 'privacy') return privacyView()
  if (state.view === 'terms') return termsView()
  if (state.view === 'summary') return summaryView()
  return uploadView()
}

const render = ({ focus = true } = {}) => {
  const viewChanged = state.view !== renderedView
  renderedView = state.view
  app.innerHTML = `
    ${header()}
    ${busyOverlay()}
    <div class="app-shell">
      ${stepRail()}
      <main class="content-grid">
        ${view()}
      </main>
    </div>
  `
  createIcons({ icons: renderedIcons, attrs: { 'aria-hidden': 'true' } })
  requestAnimationFrame(() => {
    if (viewChanged) globalThis.scrollTo(0, 0)
    if (focus) app.querySelector('h1')?.focus({ preventScroll: true })
  })
}

const setError = (error) => {
  state.error = error instanceof ApiError ? error.message : 'Something went wrong while checking the document. Please try again.'
}

const setFiles = (files) => {
  const accepted = files
    .filter((file) => file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf'))
    .filter((file) => file.size <= 20 * 1024 * 1024)
    .slice(0, 8)
  state.files = accepted
  state.keys.uploads = accepted.map(() => createIdempotencyKey('upload'))
  state.error = accepted.length === files.length
    ? ''
    : 'Only PDF files up to 20 MB can be added.'
  render({ focus: false })
}

const loadExtraction = async () => {
  state.status = 'Looking for key costs, dates and policy details…'
  state.keys.extraction ||= createIdempotencyKey('extract')
  const extraction = await extractTerms(
    state.analysisId,
    state.keys.extraction,
  )
  state.extraction = extraction
  state.view = 'terms'
}

const beginReview = async () => {
  state.busy = true
  state.error = ''
  state.status = 'Preparing a private workspace…'
  render({ focus: false })
  try {
    if (!state.analysisId) {
      const created = await createAnalysis(state.purpose, state.decisionDate)
      state.analysisId = created.analysis.analysis_id
    }
    for (let index = state.documents.length; index < state.files.length; index += 1) {
      state.status = `Reading document ${index + 1} of ${state.files.length}…`
      render({ focus: false })
      const uploaded = await uploadDocument(
        state.analysisId,
        state.files[index],
        state.keys.uploads[index],
      )
      state.documents.push(uploaded.document)
    }
    state.status = 'Checking for personal details…'
    render({ focus: false })
    state.keys.privacyScan ||= createIdempotencyKey('privacy-scan')
    const scanned = await scanPrivacy(state.analysisId, state.keys.privacyScan)
    state.findings = scanned.findings
    state.privacyActions = Object.fromEntries(
      scanned.findings.map((finding) => [
        finding.finding_id,
        finding.action === 'review' ? 'redact' : finding.action,
      ]),
    )
    if (state.findings.length) {
      state.view = 'privacy'
    } else {
      await loadExtraction()
    }
  } catch (error) {
    setError(error)
  } finally {
    state.busy = false
    state.status = ''
    render()
  }
}

const confirmPrivacy = async () => {
  const unresolved = state.findings.some((finding) => !state.privacyActions[finding.finding_id])
  if (unresolved) {
    state.error = 'Choose how to handle each type of private information.'
    render({ focus: false })
    return
  }
  state.busy = true
  state.error = ''
  state.status = 'Hiding the personal details you selected…'
  render({ focus: false })
  try {
    const decisions = state.findings.map((finding) => ({
      finding_id: finding.finding_id,
      action: state.privacyActions[finding.finding_id],
      confirmed: true,
    }))
    state.keys.privacyReview ||= createIdempotencyKey('privacy-review')
    await reviewPrivacy(state.analysisId, decisions, state.keys.privacyReview)
    await loadExtraction()
  } catch (error) {
    setError(error)
  } finally {
    state.busy = false
    state.status = ''
    render()
  }
}

const confirmTerms = async () => {
  state.busy = true
  state.error = ''
  state.status = 'Saving your checked details…'
  render({ focus: false })
  try {
    const decisions = state.extraction.terms.map((term) => ({
      term_id: term.term_id,
      value: term.value,
      source_span_ids: term.source_span_ids,
      confirmed: true,
    }))
    state.keys.termReview ||= createIdempotencyKey('term-review')
    state.extraction = await reviewTerms(
      state.analysisId,
      decisions,
      state.keys.termReview,
    )
    state.view = 'summary'
  } catch (error) {
    setError(error)
  } finally {
    state.busy = false
    state.status = ''
    render()
  }
}

const destroyAnalysis = async () => {
  if (!state.analysisId) {
    state = createInitialState()
    render()
    return
  }
  if (!globalThis.confirm('Delete this check and its temporary document copies?')) return
  state.busy = true
  state.error = ''
  state.status = 'Deleting this check…'
  render({ focus: false })
  try {
    await deleteAnalysis(state.analysisId)
    state = createInitialState()
  } catch (error) {
    setError(error)
    state.busy = false
  }
  render()
}

app.addEventListener('submit', (event) => {
  event.preventDefault()
  if (event.target.id === 'upload-form') void beginReview()
  if (event.target.id === 'privacy-form') void confirmPrivacy()
  if (event.target.id === 'terms-form') void confirmTerms()
})

app.addEventListener('change', (event) => {
  if (event.target.id === 'pdf-files') {
    setFiles([...event.target.files])
    return
  }
  if (event.target.name === 'purpose') state.purpose = event.target.value
  if (event.target.name === 'decision-date') state.decisionDate = event.target.value
  if (event.target.name === 'privacy-acknowledgement') {
    state.privacyAcknowledged = event.target.checked
    render({ focus: false })
  }
  if (event.target.dataset.privacyCategory) {
    state.findings
      .filter((finding) => finding.category === event.target.dataset.privacyCategory)
      .forEach((finding) => {
        state.privacyActions[finding.finding_id] = event.target.value
      })
    state.error = ''
  }
})

app.addEventListener('click', (event) => {
  const removeButton = event.target.closest('[data-remove-file]')
  if (removeButton) {
    const index = Number(removeButton.dataset.removeFile)
    setFiles(state.files.filter((_, fileIndex) => fileIndex !== index))
    return
  }
  const action = event.target.closest('[data-action]')?.dataset.action
  if (action === 'delete') void destroyAnalysis()
  if (action === 'restart') {
    if (state.analysisId) void destroyAnalysis()
    else {
      state = createInitialState()
      render()
    }
  }
})

app.addEventListener('dragover', (event) => {
  if (!event.target.closest('#upload-zone')) return
  event.preventDefault()
  event.target.closest('#upload-zone').classList.add('is-dragging')
})

app.addEventListener('dragleave', (event) => {
  event.target.closest('#upload-zone')?.classList.remove('is-dragging')
})

app.addEventListener('drop', (event) => {
  const zone = event.target.closest('#upload-zone')
  if (!zone) return
  event.preventDefault()
  zone.classList.remove('is-dragging')
  setFiles([...event.dataTransfer.files])
})

render({ focus: false })
