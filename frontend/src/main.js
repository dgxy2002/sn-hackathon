import './style.css'
import skylineImage from './assets/singapore-skyline-landscape.jpg'
import {
  ApiError,
  createClientId,
  createConversation,
  decideProposal,
  fetchReplay,
  invokeCoverCheck,
  sendConversationMessage,
  undoRevision,
} from './api.js'

const app = document.querySelector('#app')
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)')

const questions = [
  {
    category: 'visibility',
    weight: 0.25,
    kicker: 'Basics · What covers you',
    question: 'Do you know what insurance currently covers you?',
    note: 'Include cover bought by you, family, an employer, or a national scheme.',
    answers: [
      ['Yes', 'I know the main plans and benefits', 3],
      ['Mostly', 'I know the plans, not every detail', 2],
      ['A little', 'I only know one or two names', 1],
      ['Not yet', 'I need a simple inventory', 0],
    ],
  },
  {
    category: 'visibility',
    weight: 0.25,
    kicker: 'Basics · What it costs',
    question: 'Do you know what your insurance costs each month or year?',
    note: 'A rough total is enough; annual premiums can be divided by 12.',
    answers: [
      ['Exactly', 'I know the total', 3],
      ['Roughly', 'I know the range', 2],
      ['Partly', 'I know some premiums', 1],
      ['Not yet', 'I have never added them up', 0],
    ],
  },
  {
    category: 'foundations',
    weight: 0.25,
    kicker: 'Basics · What responds',
    question: 'If something serious happened, do you know which cover would respond?',
    note: 'Think hospitalisation, serious illness, disability, or death.',
    answers: [
      ['Clearly', 'I know the main benefits and triggers', 3],
      ['Mostly', 'I understand the broad differences', 2],
      ['A little', 'Some terms blur together', 1],
      ['Not yet', 'I need plain-language guidance', 0],
    ],
  },
  {
    category: 'terms',
    weight: 0.25,
    kicker: 'Basics · Where it stops',
    question: 'Do you know the main limits and when your cover ends?',
    note: 'Check exclusions, waiting periods, renewals, and the end age or date.',
    answers: [
      ['Yes', 'I know the main limits and end dates', 3],
      ['Some', 'I know the obvious ones', 2],
      ['Vaguely', 'I would need to verify them', 1],
      ['Not yet', 'I have not read the terms', 0],
    ],
  },
]

const onboardingSteps = [
  ['Your starting point', 'Five details used to calculate your protection starting point.'],
  ['What your plan already covers', 'Four figures copied from your latest policy schedule.'],
]

const goalOptions = [
  'Protect my family or dependants',
  'Protect my income if I cannot work',
  'Pay off debt if something happens',
  'Start with affordable basic protection',
]

const goalPriorityMap = {
  'Protect my family or dependants': { death: 100, disability: 75, critical_illness: 80, personal_accident: 20 },
  'Protect my income if I cannot work': { death: 50, disability: 100, critical_illness: 90, personal_accident: 20 },
  'Pay off debt if something happens': { death: 90, disability: 80, critical_illness: 60, personal_accident: 20 },
  'Start with affordable basic protection': { death: 75, disability: 75, critical_illness: 75, personal_accident: 20 },
}

const createEmptyProfile = () => ({
  name: '',
  email: '',
  consent: false,
  income: '',
  debt: '',
  insuranceStatus: 'Unsure',
  currentPremium: '',
  deathCover: '',
  tpdCover: '',
  advancedCiCover: '',
  goal: '',
  budget: '',
  productPreference: '',
})

const state = {
  view: 'intro',
  profileId: `browser-${createClientId()}`,
  entrySource: 'intro',
  questionIndex: 0,
  answers: [],
  onboardingStep: 0,
  direction: 'forward',
  keyboard: false,
  runtime: {
    status: 'idle',
    error: '',
    profile: null,
    extraction: null,
    recommendation: null,
    explanation: null,
  },
  profile: createEmptyProfile(),
  agent: {
    activeRevisionId: 'summary-v1',
    conversationId: '',
    status: 'idle',
    messages: [],
    actions: [],
    comparisonFilter: 'all',
    pendingFocus: '',
    pendingProposal: null,
    latestDelta: null,
    replay: [],
    canUndo: false,
    error: '',
    abortController: null,
    suggestedPrompts: [
      { id: 'how-gaps-work', label: 'How are my gaps calculated?', message: 'How were my protection gaps calculated?' },
      { id: 'show-unknowns', label: 'Show assumptions', message: 'What assumptions should I verify?' },
      { id: 'explore-term-life', label: 'Explore life cover', message: 'Which brochures mention term life protection?' },
      { id: 'explore-integrated-shield', label: 'Explore hospital cover', message: 'Which plans mention Integrated Shield hospital cover?' },
    ],
  },
}

const formatCurrency = (value) => new Intl.NumberFormat('en-SG', {
  style: 'currency',
  currency: 'SGD',
  maximumFractionDigits: 0,
}).format(value)

const escapeHtml = (value) => String(value)
  .replaceAll('&', '&amp;')
  .replaceAll('<', '&lt;')
  .replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;')
  .replaceAll("'", '&#039;')

const citationLinks = {
  'MONEYSENSE-LIFE-INSURANCE': 'https://www.moneysense.gov.sg/life-insurance/',
}

const safeExternalUrl = (value) => {
  try {
    const url = new URL(String(value || ''))
    return ['http:', 'https:'].includes(url.protocol) ? url.href : ''
  } catch {
    return ''
  }
}

const formatEvidenceDate = (value) => {
  if (!value) return 'Unknown'
  const [year, month, day] = String(value).slice(0, 10).split('-').map(Number)
  if (!year || !month || !day) return 'Unknown'
  return new Intl.DateTimeFormat('en-SG', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(Date.UTC(year, month - 1, day)))
}

const profileField = (value, stateName = 'present') => ({
  state: stateName,
  value,
  provenance: {
    source: 'user',
    recorded_at: new Date().toISOString(),
    source_ref: 'covercheck-browser-onboarding',
  },
})

const buildVersionedProfile = (insuranceStatus) => {
  const hasCurrentPolicy = insuranceStatus === 'Yes'
  const policyIsUnsure = insuranceStatus === 'Unsure'
  const unknown = () => profileField(null, 'unknown')
  const notApplicable = () => profileField(null, 'not_applicable')
  const policyValue = (value) => {
    if (hasCurrentPolicy) return value === '' ? unknown() : profileField(Number(value))
    return policyIsUnsure ? unknown() : notApplicable()
  }
  const policyUnknown = () => hasCurrentPolicy ? unknown() : policyIsUnsure ? unknown() : notApplicable()
  const priorities = goalPriorityMap[state.profile.goal] || goalPriorityMap['Start with affordable basic protection']

  return {
    schema_id: 'covercheck.profile',
    contract_version: '1.0.0',
    profile_id: state.profileId,
    version: 1,
    as_of_date: new Date().toISOString().slice(0, 10),
    consent: state.profile.consent,
    data: {
      life_stage: unknown(),
      employment_status: unknown(),
      goal: profileField(state.profile.goal),
      target_amount: unknown(),
      target_date: unknown(),
      monthly_income: profileField(Number(state.profile.income)),
      monthly_expenses: unknown(),
      emergency_savings_months: unknown(),
      dependant_count: unknown(),
      dependant_support_years: unknown(),
      liabilities: profileField(Number(state.profile.debt)),
      has_current_policy: policyIsUnsure ? unknown() : profileField(hasCurrentPolicy),
      existing_death_cover: policyValue(state.profile.deathCover),
      existing_ci_cover: policyValue(state.profile.advancedCiCover),
      government_cover: unknown(),
      employer_cover: unknown(),
      monthly_budget: profileField(Number(state.profile.budget)),
      product_preference: profileField(
        state.profile.productPreference === 'Protection only' ? 'protection-only' : 'savings-linked',
      ),
      age: unknown(),
      gender: unknown(),
      occupation: unknown(),
      marital_status: unknown(),
      supported_people: unknown(),
      loan_commitments: unknown(),
      current_insurer: policyUnknown(),
      current_product_name: policyUnknown(),
      current_product_type: policyUnknown(),
      integrated_shield_plan: policyUnknown(),
      integrated_shield_provider: policyUnknown(),
      current_monthly_premium: policyValue(state.profile.currentPremium),
      existing_terminal_illness_cover: policyUnknown(),
      existing_tpd_cover: policyValue(state.profile.tpdCover),
      existing_early_ci_cover: policyUnknown(),
      existing_intermediate_ci_cover: policyUnknown(),
      existing_advanced_ci_cover: policyValue(state.profile.advancedCiCover),
      existing_personal_accident_cover: policyUnknown(),
      riders: policyUnknown(),
      protection_priorities: profileField(priorities),
      credit_card_count: unknown(),
      credit_card_providers: unknown(),
      total_credit_limit: unknown(),
      credit_utilization_percent: unknown(),
      minimum_payment_frequency: unknown(),
    },
  }
}

async function prepareComparison(insuranceStatus = state.profile.insuranceStatus) {
  if (state.runtime.status === 'planning') return
  const controller = new AbortController()
  state.runtime.status = 'planning'
  state.runtime.error = ''
  render({ focus: false, preserveScroll: true })

  try {
    const profile = buildVersionedProfile(insuranceStatus)
    const invocation = await invokeCoverCheck({
      schema_id: 'covercheck.invocation',
      contract_version: '1.0.0',
      invocation_id: createClientId(),
      profile,
      extraction_id: null,
    }, controller.signal)
    state.runtime.profile = invocation.profile
    state.runtime.extraction = invocation.extraction
    state.runtime.recommendation = invocation.recommendation
    state.runtime.explanation = invocation.explanation
    state.runtime.status = invocation.state
    state.agent.activeRevisionId = 'summary-v1'
    state.agent.conversationId = ''
    state.agent.pendingProposal = null
    state.agent.latestDelta = null
    state.agent.replay = []
    state.agent.canUndo = false

    navigate('comparison')
  } catch (error) {
    state.runtime.status = 'failed'
    state.runtime.error = error instanceof ApiError
      ? error.message
      : 'CoverCheck is temporarily unavailable. Please try again.'
    render({ focus: false, preserveScroll: true })
  }
}

const actionTargetLabels = {
  'reasoning:ranking': 'Calculation method',
  'reasoning:assumptions': 'Assumptions to verify',
  'comparison:critical-illness': 'Critical-illness gap',
  'profile:decision-input': 'Profile update',
  'summary:current': 'Current result',
  'evidence:cached-catalogue': 'Brochure library',
}

const actionToolLabels = {
  ANSWER_QUESTION: 'Searched brochure library',
  FOCUS_SECTION: 'Opened result details',
  FILTER_COMPARISON: 'Focused the result',
  PROPOSE_PROFILE_PATCH: 'Prepared a profile change',
}

const agentMessageView = (message) => {
  const citations = (message.citations || []).map((citation) => {
    const safeUrl = safeExternalUrl(citation.url || citationLinks[citation.evidence_id])
    const label = escapeHtml(citation.label)
    const provider = escapeHtml(citation.provider || '')
    const product = escapeHtml(citation.product || '')
    const sourceFile = escapeHtml(citation.source_file || '')
    const excerpt = escapeHtml(citation.excerpt || '')
    const evidenceStateLabels = {
      approved: 'Provider source',
      current: 'Current source',
      unverified: 'Verify source',
      stale: 'Check date',
      conflicting: 'Conflicting details',
      unknown: 'Date unavailable',
    }
    const evidenceState = escapeHtml(
      citation.synthetic ? 'Illustrative source' : (evidenceStateLabels[citation.evidence_state] || 'Verify source'),
    )
    const freshness = escapeHtml(citation.freshness_status || 'unknown')
    const documentDate = escapeHtml(formatEvidenceDate(citation.document_as_of_date))
    const effectiveDate = escapeHtml(formatEvidenceDate(citation.product_effective_date))
    const source = safeUrl
      ? `<a href="${escapeHtml(safeUrl)}" target="_blank" rel="noreferrer">Open provider source <span aria-hidden="true">↗</span></a>`
      : `<span>${sourceFile ? `Brochure record: ${sourceFile}` : 'Open the provider website to verify current terms'}</span>`

    if (!citation.excerpt) {
      return safeUrl
        ? `<a href="${escapeHtml(safeUrl)}" target="_blank" rel="noreferrer">${label} <span aria-hidden="true">↗</span></a>`
        : `<span>${label}</span>`
    }

    return `
      <details class="agent-evidence">
        <summary>
          <span><b>${provider || label}</b><small>${product || label}</small></span>
          <i class="is-${escapeHtml(citation.evidence_state || 'unknown')}">${evidenceState}</i>
        </summary>
        <div class="agent-evidence-detail">
          <blockquote>${excerpt}</blockquote>
          <dl>
            <div><dt>Brochure as at</dt><dd>${documentDate}</dd></div>
            <div><dt>Terms effective</dt><dd>${effectiveDate}</dd></div>
            <div><dt>Freshness</dt><dd>${freshness}</dd></div>
          </dl>
          <p>${source}</p>
        </div>
      </details>
    `
  }).join('')

  return `
    <article class="agent-message is-${escapeHtml(message.role)}">
      <span class="mono">${message.role === 'assistant' ? 'COVERCHECK' : 'YOU'}</span>
      <p>${escapeHtml(message.content)}</p>
      ${citations ? `<div class="agent-citations" aria-label="Answer sources">${citations}</div>` : ''}
    </article>
  `
}

const agentActionView = (action, index) => `
  <details class="agent-action is-${escapeHtml(action.status)}" ${index === state.agent.actions.length - 1 ? 'open' : ''}>
    <summary>
      <span class="action-sequence mono">${String(index + 1).padStart(2, '0')}</span>
      <span><b>${escapeHtml(actionToolLabels[action.tool] || 'Reviewed result')}</b><small>${escapeHtml(actionTargetLabels[action.target] || 'No change made')}</small></span>
      <i aria-hidden="true">${action.status === 'completed' ? 'DONE' : 'NO CHANGE'}</i>
    </summary>
    <div class="agent-action-detail">
      <span>${action.evidence_count} evidence record${action.evidence_count === 1 ? '' : 's'}</span>
      <span>${action.confirmation_required ? 'Your confirmation is required' : 'Result unchanged'}</span>
      <span>${action.error_code ? escapeHtml(action.error_code) : escapeHtml(action.affected_regions.join(', '))}</span>
    </div>
  </details>
`

const proposalView = () => {
  const proposal = state.agent.pendingProposal
  if (!proposal) return ''
  const patch = proposal.patch
  return `
    <section class="agent-proposal" aria-labelledby="proposal-title">
      <span class="mono">CONFIRMATION REQUIRED</span>
      <h3 id="proposal-title">Change ${escapeHtml(patch.field_name.replaceAll('_', ' '))}?</h3>
      <p>${escapeHtml(String(patch.old_value))} → ${escapeHtml(String(patch.proposed_value))}</p>
      <small>${escapeHtml(patch.reason)}</small>
      <div>
        <button type="button" data-action="confirm-proposal" data-proposal-id="${escapeHtml(proposal.proposal_id)}">Confirm and recalculate</button>
        <button type="button" data-action="cancel-proposal" data-proposal-id="${escapeHtml(proposal.proposal_id)}">Cancel</button>
      </div>
    </section>
  `
}

const revisionView = () => {
  const delta = state.agent.latestDelta
  if (!delta) return ''
  const inputChanges = delta.changed_inputs
    .map((change) => `${change.field_name}: ${change.old_value} → ${change.new_value}`)
    .join(' · ')
  const gapChanges = delta.changed_gaps
    .map((change) => `${change.gap_type}: ${formatCurrency(change.old_amount)} → ${formatCurrency(change.new_amount)}`)
    .join(' · ')

  return `
    <section class="agent-delta" aria-live="polite">
      <span class="mono">REVISION APPLIED</span>
      <p>${escapeHtml(inputChanges || 'Profile updated')}</p>
      ${gapChanges ? `<small>${escapeHtml(gapChanges)}</small>` : ''}
      <small>Your protection starting point was recalculated.</small>
    </section>
  `
}

const agentView = () => {
  const statusLabels = {
    idle: 'Ready',
    planning: 'Working on it',
    waiting_for_confirmation: 'Waiting for confirmation',
    completed: 'Completed',
    unsupported: 'No source found',
    cancelled: 'Cancelled',
    failed: 'Temporarily unavailable',
  }
  const isBusy = state.agent.status === 'planning'
  const messages = state.agent.messages.length
    ? state.agent.messages.map(agentMessageView).join('')
    : '<p class="agent-empty">Ask how the amounts were calculated, update your budget, or search the brochure library by cover type or provider.</p>'

  return `
    <section class="agent-workspace" id="ask-covercheck" aria-labelledby="agent-title">
      <div class="agent-conversation">
        <div class="agent-heading">
          <div>
            <span class="section-index mono">04 · ASK & EXPLORE</span>
            <h2 id="agent-title">Ask about your result.</h2>
          </div>
          <span class="agent-state is-${state.agent.status}" aria-live="polite">${statusLabels[state.agent.status]}</span>
        </div>
        <p class="agent-deck">CoverCheck can explain your calculation, search real brochure excerpts, and recalculate after a change you confirm.</p>
        <div class="provider-list" aria-label="Brochure providers available">
          <span>Brochure library</span><b>AIA</b><b>FWD</b><b>Great Eastern</b><b>Singlife</b>
        </div>
        <div class="agent-prompts" aria-label="Suggested questions">
          ${state.agent.suggestedPrompts.map((prompt) => `
            <button type="button" data-agent-prompt data-prompt="${escapeHtml(prompt.message)}" ${isBusy ? 'disabled' : ''}>
              ${escapeHtml(prompt.label)} <span aria-hidden="true">↗</span>
            </button>
          `).join('')}
        </div>
        <div class="agent-messages" aria-live="polite">${messages}</div>
        ${state.agent.error ? `<p class="agent-error" role="alert">${escapeHtml(state.agent.error)}</p>` : ''}
        ${proposalView()}
        ${revisionView()}
        <form class="agent-composer" id="agent-form">
          <label class="sr-only" for="agent-message">Ask CoverCheck about your result</label>
          <textarea id="agent-message" name="message" rows="2" maxlength="1000" placeholder="Ask about a gap, provider, cover type, or change your budget" required ${isBusy ? 'disabled' : ''}></textarea>
          ${isBusy
            ? '<button class="agent-stop" type="button" data-action="stop-agent">Stop</button>'
            : '<button class="agent-send" type="submit">Send <span aria-hidden="true">↗</span></button>'}
        </form>
        <p class="agent-boundary">Brochure excerpts are read-only and may be dated. CoverCheck asks before changing any profile input.</p>
        <details class="activity-panel">
          <summary><span>Session activity</span><small>${state.agent.actions.length} action${state.agent.actions.length === 1 ? '' : 's'}</small></summary>
          ${state.agent.conversationId ? `
            <div class="revision-controls">
              <button type="button" data-action="show-replay">Show history</button>
              <button type="button" data-action="undo-revision" ${state.agent.canUndo ? '' : 'disabled'}>Undo last confirmed change</button>
            </div>
            ${state.agent.replay.length ? `<ol class="replay-list">${state.agent.replay.map((item) => `
              <li><span class="mono">${String(item.sequence).padStart(2, '0')}</span>${escapeHtml(item.event_type.replaceAll('_', ' '))}</li>
            `).join('')}</ol>` : ''}
          ` : ''}
          <div class="agent-actions">
            ${state.agent.actions.length
              ? state.agent.actions.map(agentActionView).join('')
              : '<p class="agent-empty">No changes or source lookups yet.</p>'}
          </div>
        </details>
      </div>
    </section>
  `
}

const readinessCategories = {
  visibility: { label: 'Coverage visibility', weight: 50 },
  foundations: { label: 'Protection basics', weight: 25 },
  terms: { label: 'Terms awareness', weight: 25 },
}

const getReadinessBreakdown = () => {
  const categories = Object.fromEntries(
    Object.entries(readinessCategories).map(([key, item]) => [key, { ...item, earned: 0, possible: 0 }]),
  )
  let weightedScore = 0
  questions.forEach((question, index) => {
    const normalized = (state.answers[index]?.value ?? 0) / 3
    weightedScore += normalized * question.weight
    categories[question.category].earned += normalized * question.weight
    categories[question.category].possible += question.weight
  })
  return {
    score: Math.round(weightedScore * 100),
    categories: Object.fromEntries(
      Object.entries(categories).map(([key, item]) => [key, {
        ...item,
        score: Math.round((item.earned / item.possible) * 100),
      }]),
    ),
  }
}

const getScore = () => getReadinessBreakdown().score

const brand = (tone = '') => `
  <a class="brand ${tone}" href="#" data-action="home" aria-label="CoverCheck SG home">
    <span class="brand-mark" aria-hidden="true">C</span>
    <span>CoverCheck SG</span>
  </a>
`

const trustNote = () => `
  <p class="trust-note">Educational starting point—not financial advice. Verify current policy terms and speak with a licensed adviser before buying, replacing, or cancelling cover.</p>
`

const appHeader = ({ step = '', back = false } = {}) => `
  <header class="app-header">
    ${brand()}
    <div class="header-meta">
      ${step ? `<span class="mono">${step}</span>` : ''}
      ${back ? '<button class="text-button" type="button" data-action="back">Back</button>' : ''}
    </div>
  </header>
`

const introView = () => `
  <main class="intro-screen view-enter" data-screen="intro">
    <img
      class="intro-image"
      src="${skylineImage}"
      alt="Singapore skyline across Marina Bay in daylight"
      width="2200"
      height="782"
      fetchpriority="high"
    />
    <div class="intro-scrim" aria-hidden="true"></div>
    <header class="intro-header">
      ${brand('brand-inverse')}
      <span class="intro-label">Singapore · Ages 18-30</span>
    </header>
    <section class="intro-copy" aria-labelledby="intro-title">
      <p class="eyebrow intro-sequence">Insurance clarity, minus the sales pitch.</p>
      <h1 id="intro-title" class="display-title intro-sequence">Find your protection starting point.</h1>
      <p class="intro-deck intro-sequence">Choose the path that fits. The gap check uses five inputs—no NRIC or medical details.</p>
      <div class="intro-actions intro-sequence" aria-label="Choose how to start">
        <button class="journey-button is-primary" type="button" data-action="start-no-policy">
          <span>I don’t have a plan</span><small>Start from zero private cover</small><i aria-hidden="true">→</i>
        </button>
        <button class="journey-button" type="button" data-action="review-policy">
          <span>Review a plan I have</span><small>Add four figures from your policy</small><i aria-hidden="true">→</i>
        </button>
      </div>
      <button class="intro-quiz-link intro-sequence" type="button" data-action="start-quiz">Or check my insurance basics · 4 questions</button>
    </section>
    <p class="image-credit">Photo: <a href="https://commons.wikimedia.org/wiki/File:Singapore_(SG),_Marina_Bay_--_2019_--_4439-48.jpg" target="_blank" rel="noreferrer">Dietmar Rabich / Wikimedia Commons</a> · <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noreferrer">CC BY-SA 4.0</a></p>
  </main>
`

const questionView = () => {
  const item = questions[state.questionIndex]
  const progress = ((state.questionIndex + 1) / questions.length) * 100
  const options = item.answers.map((answer, index) => `
    <button
      class="answer-option"
      type="button"
      data-answer="${index}"
      aria-label="Answer ${index + 1}: ${answer[0]}. ${answer[1]}"
    >
      <span class="answer-key" aria-hidden="true">${index + 1}</span>
      <span class="answer-copy"><strong>${answer[0]}</strong><small>${answer[1]}</small></span>
      <span class="answer-dot" aria-hidden="true"></span>
    </button>
  `).join('')

  return `
    <main class="question-screen ${state.keyboard ? 'is-keyboard' : ''}" data-screen="question">
      ${appHeader({ step: `${String(state.questionIndex + 1).padStart(2, '0')} / ${String(questions.length).padStart(2, '0')}`, back: true })}
      <div class="progress-track" aria-label="Quiz progress: question ${state.questionIndex + 1} of ${questions.length}">
        <span style="--progress: ${progress / 100}"></span>
      </div>
      <section class="question-layout view-enter ${state.direction === 'back' ? 'from-left' : 'from-right'}">
        <div class="question-number mono" aria-hidden="true">Q${String(state.questionIndex + 1).padStart(2, '0')}</div>
        <div class="question-main">
          <p class="eyebrow">${item.kicker}</p>
          <h1 class="question-title screen-title" tabindex="-1">${item.question}</h1>
          <p class="question-note">${item.note}</p>
          <div class="answer-list" role="group" aria-label="Choose one answer">
            ${options}
          </div>
          <p class="keyboard-hint mono">Press 1-${item.answers.length} to answer · Esc to go back</p>
        </div>
      </section>
    </main>
  `
}

const resultView = () => {
  const breakdown = getReadinessBreakdown()
  const score = breakdown.score
  const topicRows = [
    ['What covers you', 'List private, employer, family-bought, and national cover', 0],
    ['What it costs', 'Add monthly and annual premiums into one total', 1],
    ['What responds', 'Separate hospital, illness, disability, and death benefits', 2],
    ['Where it stops', 'Verify exclusions, waiting periods, renewals, and end dates', 3],
  ]
  const actionCount = topicRows.filter(([, , index]) => (state.answers[index]?.value ?? 0) < 2).length
  const headline = actionCount === 0
    ? 'You know the basics. Now check if the numbers still fit.'
    : `${actionCount} thing${actionCount === 1 ? '' : 's'} to check before you compare plans.`

  const coverageRow = (label, detail, index) => {
    const known = (state.answers[index]?.value ?? 0) >= 2
    return `
    <li>
      <span class="coverage-status ${known ? 'is-known' : 'is-unknown'}">${known ? 'Visible' : 'Check'}</span>
      <strong>${label}</strong>
      <span>${detail}</span>
    </li>
  `
  }

  return `
    <main class="report-screen" data-screen="result">
      ${appHeader()}
      <section class="report-lead report-reveal reveal-1" aria-labelledby="result-title">
        <p class="eyebrow">Your readiness read</p>
        <div class="score-lockup">
          <strong class="score-value mono">${score}</strong>
          <span>/ 100</span>
        </div>
        <h1 id="result-title" class="report-title screen-title" tabindex="-1">${headline}</h1>
        <p class="report-definition">This score measures readiness actions and understanding—not wealth, suitability or how protected you are.</p>
        <div class="readiness-breakdown" aria-label="Weighted readiness categories">
          ${Object.values(breakdown.categories).map((category) => `
            <article>
              <span class="mono">${category.weight}% WEIGHT</span>
              <strong>${category.score}</strong>
              <p>${category.label}</p>
            </article>
          `).join('')}
        </div>
      </section>

      <section class="coverage-map report-reveal reveal-2" aria-labelledby="coverage-title">
        <div class="section-index mono">01 · What is visible</div>
        <div>
          <h2 id="coverage-title">What you know so far</h2>
          <ul>
            ${topicRows.map(([label, detail, index]) => coverageRow(label, detail, index)).join('')}
          </ul>
        </div>
      </section>

      <section class="result-action report-reveal reveal-3">
        <div>
          <span class="section-index mono">NEXT · ABOUT 3 MIN</span>
          <h2>Turn this into a protection starting point.</h2>
        </div>
        <div class="result-paths">
          <button class="primary-button" type="button" data-action="start-no-policy">I don’t have a plan <span aria-hidden="true">→</span></button>
          <button class="secondary-button" type="button" data-action="review-policy">Review a plan I have</button>
        </div>
      </section>
      <footer class="report-footer">${trustNote()}</footer>
    </main>
  `
}

const signupView = () => `
  <main class="form-screen" data-screen="signup">
    ${appHeader({ back: true })}
    <section class="form-intro view-enter">
      <p class="eyebrow">Before the gap check</p>
      <h1 class="form-title screen-title" tabindex="-1">No account. Just clear consent.</h1>
      <p>Your answers are used to calculate the result. A compact profile summary—not a policy document—is sent to Amazon Bedrock for a plain-language explanation.</p>
    </section>
    <form id="account-form" class="account-form view-enter" novalidate>
      <label class="consent-row">
        <input type="checkbox" name="consent" data-field="consent" ${state.profile.consent ? 'checked' : ''} required />
        <span>I agree to the use of my answers for this coverage check and its AI-generated explanation.</span>
      </label>
      <button class="primary-button" type="submit">Continue to five inputs <span aria-hidden="true">→</span></button>
      <p class="form-error" id="account-error" role="alert"></p>
    </form>
    <aside class="privacy-aside view-enter">
      <span class="mono">NOT COLLECTED</span>
      <p>No name, email, NRIC, medical details, payment, or beneficiary information.</p>
    </aside>
  </main>
`

const radioGroup = (name, label, options, current, required = false) => `
  <fieldset class="choice-field">
    <legend>${label}</legend>
    <div class="segmented-options">
      ${options.map((option) => `
        <label>
          <input type="radio" name="${name}" data-field="${name}" value="${escapeHtml(option)}" ${current === option ? 'checked' : ''} ${required ? 'required' : ''} />
          <span>${option}</span>
        </label>
      `).join('')}
    </div>
  </fieldset>
`

const activeOnboardingSteps = () => state.profile.insuranceStatus === 'Yes'
  ? onboardingSteps
  : onboardingSteps.slice(0, 1)

const onboardingFields = () => {
  const profile = state.profile
  if (state.onboardingStep === 0) {
    return `
      ${radioGroup('insuranceStatus', 'Where are you starting?', ['No', 'Yes', 'Unsure'], profile.insuranceStatus, true)}
      <div class="path-callout">
        <span class="mono">${profile.insuranceStatus === 'Yes' ? 'EXISTING PLAN PATH' : profile.insuranceStatus === 'No' ? 'NO-PLAN PATH' : 'UNSURE PATH'}</span>
        <p>${profile.insuranceStatus === 'Yes' ? 'Copy four amounts from your latest policy schedule. Only figures you confirm are used.' : profile.insuranceStatus === 'No' ? 'The calculation starts from zero declared private cover.' : 'No private cover is deducted until you can verify it.'}</p>
      </div>
      <div class="field-pair">
        <label class="field money-field"><span>Monthly take-home income</span><i>S$</i><input type="number" min="0.01" step="0.01" data-field="income" value="${profile.income}" placeholder="e.g. 4,200" required /></label>
        <label class="field money-field"><span>Total loans left to pay</span><i>S$</i><input type="number" min="0" step="0.01" data-field="debt" value="${profile.debt}" placeholder="Enter 0 if none" required /></label>
      </div>
      <p class="field-caption">A rough loan total is enough. Savings and spending are not needed for this calculation.</p>
      ${radioGroup('goal', 'What matters most right now?', goalOptions, profile.goal, true)}
      ${radioGroup('productPreference', 'What type of cover would you prefer to explore?', ['Protection only', 'Open to savings features'], profile.productPreference, true)}
      <label class="field money-field"><span>Maximum additional monthly premium</span><i>S$</i><input type="number" min="0.01" step="0.01" data-field="budget" value="${profile.budget}" placeholder="e.g. 150" required /></label>
      <p class="field-caption">This is your stated ceiling for exploring cover—not a quote or spending recommendation.</p>
    `
  }

  const premiumShare = profile.income > 0 ? (profile.currentPremium / profile.income) * 100 : 0
  return `
    <div class="unknown-callout">
      <strong>Only enter amounts you can verify.</strong>
      <p>These are the current-plan figures used in the gap and affordability calculations. Enter 0 only when the policy explicitly has no such benefit.</p>
    </div>
    <div class="field-pair">
      <label class="field money-field"><span>Total current monthly premium</span><i>S$</i><input type="number" min="0" step="0.01" data-field="currentPremium" value="${profile.currentPremium}" placeholder="e.g. 120" required /></label>
      <label class="field money-field"><span>Death benefit</span><i>S$</i><input type="number" min="0" step="0.01" data-field="deathCover" value="${profile.deathCover}" placeholder="e.g. 100,000" required /></label>
      <label class="field money-field"><span>Total permanent disability benefit</span><i>S$</i><input type="number" min="0" step="0.01" data-field="tpdCover" value="${profile.tpdCover}" placeholder="e.g. 100,000" required /></label>
      <label class="field money-field"><span>Advanced critical illness benefit</span><i>S$</i><input type="number" min="0" step="0.01" data-field="advancedCiCover" value="${profile.advancedCiCover}" placeholder="e.g. 50,000" required /></label>
    </div>
    <div class="premium-preview ${premiumShare > 15 ? 'is-high' : premiumShare > 5 ? 'is-watch' : 'is-comfort'}">
      <span class="mono">CURRENT PREMIUM / INCOME</span>
      <strong>${premiumShare.toFixed(1)}%</strong>
      <p>5% is a planning reference. MoneySense’s educational upper reference is 15% of income.</p>
    </div>
  `
}

const onboardingView = () => {
  const steps = activeOnboardingSteps()
  const current = steps[state.onboardingStep]
  const isFinalStep = state.onboardingStep === steps.length - 1
  const isPlanning = isFinalStep && state.runtime.status === 'planning'
  const finalAction = 'Calculate my protection gaps'
  return `
    <main class="onboarding-screen" data-screen="onboarding">
      ${appHeader({ step: `PROFILE ${state.onboardingStep + 1} / ${steps.length}`, back: true })}
      <div class="onboarding-layout">
        <aside class="stepper" aria-label="Onboarding progress">
          <p class="mono">YOUR PROFILE</p>
          <ol>
            ${steps.map((step, index) => `
              <li class="${index === state.onboardingStep ? 'is-current' : ''} ${index < state.onboardingStep ? 'is-complete' : ''}">
                <span>${String(index + 1).padStart(2, '0')}</span><b>${step[0]}</b>
              </li>
            `).join('')}
          </ol>
          <p class="stepper-note">Only details used in your calculation are required.</p>
        </aside>
        <section class="onboarding-main view-enter">
          <p class="eyebrow">Step ${state.onboardingStep + 1}</p>
          <h1 class="onboarding-title screen-title" tabindex="-1">${current[0]}</h1>
          <p class="onboarding-deck">${current[1]}</p>
          <form id="onboarding-form" class="fact-form">
            ${onboardingFields()}
            <div class="form-actions">
              ${state.onboardingStep > 0 ? '<button class="secondary-button" type="button" data-action="previous-onboarding">Previous</button>' : ''}
              <button class="primary-button" type="submit" ${isPlanning ? 'disabled' : ''}>${isPlanning ? 'Running checks…' : isFinalStep ? `${finalAction} <span aria-hidden="true">→</span>` : 'Next step <span aria-hidden="true">→</span>'}</button>
            </div>
            ${state.runtime.error ? `<p class="form-error" role="alert">${escapeHtml(state.runtime.error)}</p>` : ''}
          </form>
        </section>
      </div>
    </main>
  `
}

const illustrativeOptions = {
  'synthetic-lioncity-term-flex': {
    type: 'Term life',
    direction: 'Family and debt protection',
    description: 'A high-cover, fixed-term structure to explore when death and disability gaps are the priority.',
    benefit: 'S$400,000',
    term: 'To age 65',
    premium: 78,
  },
  'synthetic-harbour-essential-ci': {
    type: 'Critical illness',
    direction: 'Serious-illness cash cover',
    description: 'A lump-sum critical-illness structure to explore alongside hospital and income protection.',
    benefit: 'S$150,000',
    term: '30 years',
    premium: 64,
  },
  'synthetic-orchid-income-shield': {
    type: 'Disability income',
    direction: 'Monthly income protection',
    description: 'A monthly-benefit structure to explore if being unable to work is your main concern.',
    benefit: 'S$2,000 / month',
    term: 'To age 60',
    premium: 92,
  },
}

const optionDirectionsView = (evaluations) => `
  <div class="direction-grid">
    ${evaluations.map((evaluation) => {
      const option = illustrativeOptions[evaluation.plan_id]
      if (!option) return ''
      return `
        <article class="direction-card ${evaluation.rank === 1 ? 'is-primary' : ''}">
          <div class="direction-card-heading">
            <span class="mono">${evaluation.rank === 1 ? 'START HERE' : `ALTERNATIVE ${evaluation.rank - 1}`}</span>
            <span>${escapeHtml(option.type)}</span>
          </div>
          <h3>${escapeHtml(option.direction)}</h3>
          <p>${escapeHtml(option.description)}</p>
          <dl>
            <div><dt>Example benefit</dt><dd>${escapeHtml(option.benefit)}</dd></div>
            <div><dt>Example term</dt><dd>${escapeHtml(option.term)}</dd></div>
            <div><dt>Illustrative premium</dt><dd>${formatCurrency(option.premium)} / month</dd></div>
          </dl>
        </article>
      `
    }).join('')}
  </div>
  <p class="illustration-note"><b>Illustrative examples only.</b> These are not insurer products or quotes. Use them to understand which cover structure to investigate in the brochure library or with a licensed adviser.</p>
`

const declaredCoverageView = (insuranceStatus) => {
  if (insuranceStatus === 'Unsure') {
    return '<p class="comparison-empty">Your current private cover is not yet confirmed, so it was not deducted. Check your policy schedule before using these amounts as a planning reference.</p>'
  }
  if (insuranceStatus === 'No') {
    return '<p class="comparison-empty">You said you do not have a current private policy, so the calculation starts from zero declared private cover.</p>'
  }
  const coverage = [
    ['Death', state.profile.deathCover],
    ['Total permanent disability', state.profile.tpdCover],
    ['Advanced critical illness', state.profile.advancedCiCover],
  ]
  return `
    <div class="declared-cover-heading">
      <div><span class="mono">YOU CONFIRMED</span><h3>Current private cover used in the calculation</h3></div>
      <div><b>${formatCurrency(state.profile.currentPremium)} / month</b><small>Confirm these figures against your latest policy schedule.</small></div>
    </div>
    <div class="declared-cover-grid">
      ${coverage.map(([label, amount]) => `<article><span>${label}</span><strong class="mono">${formatCurrency(amount)}</strong></article>`).join('')}
    </div>
    <p class="comparison-warning">Benefits stay separate because one payout may overlap with or reduce another. Confirm how your policy treats accelerated and overlapping benefits.</p>
  `
}

const comparisonView = () => {
  const recommendation = state.runtime.recommendation
  const explanation = state.runtime.explanation
  const gapByType = Object.fromEntries((recommendation?.gaps || []).map((gap) => [gap.gap_type, gap]))
  const deathGap = gapByType.death?.gap_amount || 0
  const ciGap = gapByType.critical_illness?.gap_amount || 0
  const tpdGap = gapByType.total_permanent_disability?.gap_amount
  const affordability = recommendation?.affordability
  const budgetIncomeShare = affordability?.budget_income_share == null
    ? null
    : affordability.budget_income_share * 100
  const criticalIllnessOnly = state.agent.comparisonFilter === 'critical-illness'
  const allEligible = (recommendation?.evaluations || [])
    .filter((evaluation) => evaluation.eligible)
    .sort((left, right) => left.rank - right.rank)
  const eligible = allEligible
    .filter((evaluation) => (
      !criticalIllnessOnly || illustrativeOptions[evaluation.plan_id]?.type === 'Critical illness'
    ))
  const closest = allEligible[0]
  const closestDirection = illustrativeOptions[closest?.plan_id]?.direction || 'No direction fits the stated monthly ceiling'
  const assumptions = (recommendation?.assumptions || [])
    .filter((assumption) => !assumption.startsWith('The explanation was tailored to:'))
  const policyField = state.runtime.profile?.data.has_current_policy
  const insuranceStatus = policyField?.state !== 'present'
    ? 'Unsure'
    : policyField.value ? 'Yes' : 'No'

  return `
    <main class="comparison-screen" data-screen="comparison">
      ${appHeader()}
      <section class="comparison-lead view-enter">
        <div>
          <p class="eyebrow">Your protection starting point</p>
          <h1 class="comparison-title screen-title" tabindex="-1">${insuranceStatus === 'Yes' ? 'See what your declared cover may still leave open.' : insuranceStatus === 'Unsure' ? 'See the starting point, then verify the cover you have.' : 'Start with the largest protection gaps.'}</h1>
          <p class="comparison-lead-deck">Calculated from the income, loans, budget, goal, and cover amounts you provided.</p>
        </div>
        <div class="comparison-meta">
          <span class="result-ready"><i aria-hidden="true"></i> Calculation complete</span>
          <span class="mono">UPDATED ${escapeHtml(state.runtime.profile?.as_of_date || new Date().toISOString().slice(0, 10))}</span>
        </div>
      </section>

      <section class="gap-strip" aria-labelledby="gap-title">
        <div class="gap-intro">
          <span class="section-index mono">01 · YOUR COVERAGE GAPS</span>
          <h2 id="gap-title">Amounts to investigate</h2>
          <p>A planning baseline—not a quote. Open the assumptions below to see what is and is not included.</p>
        </div>
        <div class="gap-stat">
          <span>Death</span>
          <strong class="mono">${formatCurrency(deathGap)}</strong>
          <small>9× annual income + loans − declared death cover</small>
        </div>
        <div class="gap-stat">
          <span>Total permanent disability</span>
          <strong class="mono">${tpdGap === undefined ? 'Unknown' : formatCurrency(tpdGap)}</strong>
          <small>${tpdGap === undefined ? 'Add your current TPD benefit to calculate this gap' : '9× annual income + loans − declared TPD cover'}</small>
        </div>
        <div class="gap-stat">
          <span>Critical illness</span>
          <strong class="mono">${formatCurrency(ciGap)}</strong>
          <small>4× annual income − declared critical-illness cover</small>
        </div>
        <div class="gap-stat premium-gap">
          <span>Your monthly ceiling</span>
          <strong class="mono">${formatCurrency(state.profile.budget)}</strong>
          <small>${budgetIncomeShare === null ? 'Income share unavailable' : `${budgetIncomeShare.toFixed(1)}% of monthly income`}</small>
        </div>
      </section>

      <section class="declared-cover-section" aria-labelledby="declared-cover-title">
        <div class="comparison-section-heading">
          <div><span class="section-index mono">02 · WHAT WE USED</span><h2 id="declared-cover-title">Your declared private cover</h2></div>
          <p>Each benefit is kept separate so overlapping policy payouts are not added together.</p>
        </div>
        ${declaredCoverageView(insuranceStatus)}
      </section>

      <section class="comparison-section" id="plan-comparison" aria-labelledby="compare-title" tabindex="-1">
        <div class="comparison-section-heading">
          <div>
            <span class="section-index mono">03 · WHAT TO EXPLORE</span>
            <h2 id="compare-title">Cover directions within your ceiling</h2>
          </div>
          <div class="comparison-context">
            <p><b>${escapeHtml(closestDirection)}</b> is the first structure to investigate based on your stated priority, preference, and ${formatCurrency(state.profile.budget)} monthly ceiling.</p>
            ${criticalIllnessOnly ? '<button class="text-button" type="button" data-action="clear-agent-filter">Show every direction</button>' : ''}
          </div>
        </div>
        ${eligible.length ? optionDirectionsView(eligible) : '<p class="comparison-empty">No example fits the monthly ceiling you entered. Ask CoverCheck to change your budget, or discuss a staged approach with a licensed adviser.</p>'}

        <div class="reasoning-drawers">
          <details id="ranking-reason" tabindex="-1">
            <summary><span><b>Plain-language explanation</b><small>${explanation ? 'Generated with Amazon Bedrock' : 'Recalculate to refresh'}</small></span><i aria-hidden="true">+</i></summary>
            <div class="drawer-content">
              <p>${escapeHtml(explanation?.summary || 'Your result has changed. The displayed amounts remain calculated from your confirmed inputs.')}</p>
            </div>
          </details>
          <details id="ranking-assumptions" tabindex="-1">
            <summary><span><b>Assumptions to verify</b><small>${assumptions.length} item${assumptions.length === 1 ? '' : 's'}</small></span><i aria-hidden="true">+</i></summary>
            <div class="drawer-content assumption-list">${assumptions.length ? `<ul>${assumptions.map((assumption) => `<li>${escapeHtml(assumption)}</li>`).join('')}</ul>` : '<p>No additional assumptions were recorded.</p>'}</div>
          </details>
        </div>
      </section>

      ${agentView()}

      <section class="decision-footer">
        <div>
          <span class="section-index mono">BEFORE YOU ACT</span>
          <h2>Verify before you decide.</h2>
          <p>Check current policy wording, premiums, exclusions, and replacement risks with a licensed adviser. Do not cancel existing cover from this calculation alone.</p>
        </div>
        <a class="primary-button" href="https://eservices.mas.gov.sg/rr" target="_blank" rel="noreferrer">Check an adviser on MAS <span aria-hidden="true">↗</span></a>
      </section>
      <footer class="comparison-footer">
        ${brand()}
        ${trustNote()}
        <button class="text-button" type="button" data-action="restart">Start over</button>
      </footer>
    </main>
  `
}

const views = {
  intro: introView,
  quiz: questionView,
  result: resultView,
  signup: signupView,
  onboarding: onboardingView,
  comparison: comparisonView,
}

function render({ focus = true, preserveScroll = false } = {}) {
  const scrollTop = window.scrollY
  app.innerHTML = views[state.view]()
  document.body.dataset.view = state.view
  window.scrollTo({ top: preserveScroll ? scrollTop : 0, behavior: 'instant' })

  if (focus) {
    requestAnimationFrame(() => {
      const title = app.querySelector('.screen-title')
      if (title && (state.keyboard || reduceMotion.matches)) title.focus({ preventScroll: true })
    })
  }

  if (state.agent.pendingFocus) {
    const focusId = state.agent.pendingFocus
    state.agent.pendingFocus = ''
    requestAnimationFrame(() => {
      const target = app.querySelector(`#${focusId}`)
      if (!target) return
      if (target instanceof HTMLDetailsElement) target.open = true
      target.focus({ preventScroll: true })
      target.scrollIntoView({
        behavior: reduceMotion.matches ? 'auto' : 'smooth',
        block: 'center',
      })
    })
  }
}

const applyAgentActions = (actions) => {
  const actionMap = {
    'FOCUS_SECTION:reasoning:ranking': () => {
      state.agent.pendingFocus = 'ranking-reason'
    },
    'FOCUS_SECTION:reasoning:assumptions': () => {
      state.agent.pendingFocus = 'ranking-assumptions'
    },
    'FILTER_COMPARISON:comparison:critical-illness': () => {
      state.agent.comparisonFilter = 'critical-illness'
      state.agent.pendingFocus = 'plan-comparison'
    },
  }

  actions
    .filter((action) => action.status === 'completed')
    .forEach((action) => actionMap[`${action.tool}:${action.target}`]?.())
}

const syncProfileFromVersioned = (versionedProfile) => {
  const data = versionedProfile?.data
  if (!data) return
  const presentValue = (field, fallback) => field?.state === 'present' ? field.value : fallback
  const status = data.has_current_policy?.state === 'present'
    ? data.has_current_policy.value ? 'Yes' : 'No'
    : 'Unsure'

  state.profile.insuranceStatus = status
  state.profile.goal = presentValue(data.goal, state.profile.goal)
  state.profile.income = Number(presentValue(data.monthly_income, state.profile.income))
  state.profile.debt = Number(presentValue(data.liabilities, state.profile.debt))
  state.profile.budget = Number(presentValue(data.monthly_budget, state.profile.budget))
  state.profile.productPreference = presentValue(data.product_preference, 'protection-only') === 'protection-only'
    ? 'Protection only'
    : 'Open to savings features'
  state.profile.currentPremium = Number(presentValue(data.current_monthly_premium, status === 'Yes' ? state.profile.currentPremium : 0))
  state.profile.deathCover = Number(presentValue(data.existing_death_cover, status === 'Yes' ? state.profile.deathCover : 0))
  state.profile.tpdCover = Number(presentValue(data.existing_tpd_cover, status === 'Yes' ? state.profile.tpdCover : 0))
  state.profile.advancedCiCover = Number(presentValue(data.existing_advanced_ci_cover, status === 'Yes' ? state.profile.advancedCiCover : 0))
}

async function askAgent(message) {
  const content = String(message || '').trim()
  if (!content || state.agent.status === 'planning') return

  const controller = new AbortController()
  state.agent.abortController = controller
  state.agent.status = 'planning'
  state.agent.error = ''
  state.agent.messages.push({ role: 'user', content, citations: [] })
  render({ focus: false, preserveScroll: true })

  try {
    if (!state.agent.conversationId) {
      const conversation = await createConversation(
        state.agent.activeRevisionId,
        state.runtime.profile,
        state.runtime.recommendation,
        controller.signal,
      )
      state.agent.conversationId = conversation.conversation_id
      state.agent.suggestedPrompts = conversation.suggested_prompts
    }

    const response = await sendConversationMessage(
      state.agent.conversationId,
      {
        client_message_id: createClientId(),
        active_revision_id: state.agent.activeRevisionId,
        message: content,
      },
      controller.signal,
    )
    state.agent.messages.push({
      role: 'assistant',
      content: response.assistant_message.content,
      citations: response.assistant_message.citations,
    })
    state.agent.actions.push(...response.actions)
    state.agent.status = response.state
    state.agent.pendingProposal = response.proposal
    applyAgentActions(response.actions)
  } catch (error) {
    if (error.name === 'AbortError') {
      state.agent.status = 'cancelled'
      state.agent.error = 'Request stopped. The comparison remains unchanged.'
    } else {
      state.agent.status = 'failed'
      state.agent.error = error instanceof ApiError
        ? error.message
        : 'CoverCheck is temporarily unavailable. Please try again.'
    }
  } finally {
    state.agent.abortController = null
    render({ focus: false, preserveScroll: true })
  }
}

async function decideAgentProposal(proposalId, decision) {
  if (!proposalId || !state.agent.conversationId || state.agent.status === 'planning') return
  state.agent.status = 'planning'
  state.agent.error = ''
  render({ focus: false, preserveScroll: true })

  try {
    const response = await decideProposal(
      state.agent.conversationId,
      proposalId,
      decision,
      {
        client_request_id: createClientId(),
        expected_revision_id: state.agent.activeRevisionId,
      },
    )
    state.agent.pendingProposal = null
    state.agent.status = response.state
    if (response.revision) {
      state.agent.activeRevisionId = response.active_revision_id
      state.agent.latestDelta = response.revision.delta
      state.agent.canUndo = true
      state.runtime.profile = response.revision.profile
      state.runtime.recommendation = response.revision.recommendation
      state.runtime.explanation = null
      syncProfileFromVersioned(response.revision.profile)
    }
  } catch (error) {
    state.agent.status = 'failed'
    state.agent.error = error instanceof ApiError ? error.message : 'The proposal decision failed.'
  }
  render({ focus: false, preserveScroll: true })
}

async function showReplay() {
  if (!state.agent.conversationId) return
  try {
    const replay = await fetchReplay(state.agent.conversationId)
    state.agent.replay = replay.events
    state.agent.error = ''
  } catch (error) {
    state.agent.error = error instanceof ApiError ? error.message : 'Replay is unavailable.'
  }
  render({ focus: false, preserveScroll: true })
}

async function undoAgentRevision() {
  if (!state.agent.conversationId || !state.agent.canUndo) return
  try {
    const response = await undoRevision(state.agent.conversationId, {
      client_request_id: createClientId(),
      expected_revision_id: state.agent.activeRevisionId,
    })
    state.agent.activeRevisionId = response.active_revision_id
    state.agent.latestDelta = response.restored_revision.delta
    state.agent.canUndo = false
    state.agent.status = 'completed'
    state.runtime.profile = response.restored_revision.profile
    state.runtime.recommendation = response.restored_revision.recommendation
    state.runtime.explanation = null
    syncProfileFromVersioned(response.restored_revision.profile)
  } catch (error) {
    state.agent.status = 'failed'
    state.agent.error = error instanceof ApiError ? error.message : 'The revision could not be undone.'
  }
  render({ focus: false, preserveScroll: true })
}

function navigate(view, direction = 'forward', keyboard = false) {
  state.view = view
  state.direction = direction
  state.keyboard = keyboard
  render()
}

function goBack(keyboard = false) {
  if (state.view === 'quiz') {
    if (state.questionIndex === 0) navigate('intro', 'back', keyboard)
    else {
      state.questionIndex -= 1
      state.direction = 'back'
      state.keyboard = keyboard
      render()
    }
    return
  }
  if (state.view === 'signup') navigate(state.entrySource === 'quiz' ? 'result' : 'intro', 'back', keyboard)
  else if (state.view === 'onboarding') {
    if (state.onboardingStep === 0) navigate('signup', 'back', keyboard)
    else {
      state.onboardingStep -= 1
      state.direction = 'back'
      state.keyboard = keyboard
      render()
    }
  }
}

function chooseAnswer(index, keyboard = false) {
  const answer = questions[state.questionIndex].answers[index]
  if (!answer) return
  state.answers[state.questionIndex] = { label: answer[0], value: answer[2] }

  const advance = () => {
    if (state.questionIndex === questions.length - 1) navigate('result', 'forward', keyboard)
    else {
      state.questionIndex += 1
      state.direction = 'forward'
      state.keyboard = keyboard
      render()
    }
  }

  if (keyboard || reduceMotion.matches) {
    advance()
    return
  }

  const selected = app.querySelector(`[data-answer="${index}"]`)
  selected?.classList.add('is-selected')
  window.setTimeout(advance, 190)
}

function updateProfileField(target) {
  const key = target.dataset.field
  if (!key) return
  const isBoolean = target.type === 'checkbox'
  const isNumber = target.type === 'number' || target.type === 'range'
  state.profile[key] = isBoolean
    ? target.checked
    : isNumber && target.value !== '' ? Number(target.value) : target.value

  if (target.type === 'range') {
    const output = target.closest('.range-field')?.querySelector('output')
    if (output) output.textContent = key === 'budget'
      ? formatCurrency(target.value)
      : `${target.value} / 100`
  }

  if (key === 'currentPremium' || key === 'income') {
    const premiumShare = state.profile.income > 0
      ? (state.profile.currentPremium / state.profile.income) * 100
      : 0
    const preview = app.querySelector('.premium-preview')
    const output = preview?.querySelector('strong')
    if (output) output.textContent = `${premiumShare.toFixed(1)}%`
    if (preview) {
      preview.classList.remove('is-comfort', 'is-watch', 'is-high')
      preview.classList.add(premiumShare > 15 ? 'is-high' : premiumShare > 5 ? 'is-watch' : 'is-comfort')
    }
  }
}

app.addEventListener('input', (event) => updateProfileField(event.target))
app.addEventListener('change', (event) => {
  updateProfileField(event.target)
  if (event.target.dataset.field === 'insuranceStatus') {
    render({ focus: false, preserveScroll: true })
  }
})

app.addEventListener('submit', (event) => {
  event.preventDefault()
  if (event.target.id === 'agent-form') {
    const form = new FormData(event.target)
    void askAgent(form.get('message'))
    return
  }

  if (event.target.id === 'account-form') {
    const error = app.querySelector('#account-error')
    if (!event.target.checkValidity()) {
      if (error) error.textContent = 'Confirm consent to continue.'
      event.target.reportValidity()
      return
    }
    state.onboardingStep = 0
    navigate('onboarding', 'forward', true)
  }

  if (event.target.id === 'onboarding-form') {
    if (!event.target.checkValidity()) {
      event.target.reportValidity()
      return
    }
    if (state.onboardingStep === activeOnboardingSteps().length - 1) {
      void prepareComparison(state.profile.insuranceStatus)
    }
    else {
      state.onboardingStep += 1
      navigate('onboarding', 'forward', true)
    }
  }
})

app.addEventListener('click', (event) => {
  const answer = event.target.closest('[data-answer]')
  if (answer) {
    chooseAnswer(Number(answer.dataset.answer))
    return
  }

  const prompt = event.target.closest('[data-agent-prompt]')
  if (prompt) {
    event.preventDefault()
    void askAgent(prompt.dataset.prompt)
    return
  }

  const control = event.target.closest('[data-action]')
  if (!control) return
  event.preventDefault()
  const action = control.dataset.action

  if (action === 'home') navigate('intro')
  if (action === 'start-quiz') {
    state.questionIndex = 0
    state.answers = []
    navigate('quiz')
  }
  if (action === 'start-no-policy') {
    state.entrySource = state.view === 'result' ? 'quiz' : 'intro'
    state.profile.insuranceStatus = 'No'
    state.onboardingStep = 0
    navigate('signup')
  }
  if (action === 'review-policy') {
    state.entrySource = state.view === 'result' ? 'quiz' : 'intro'
    state.profile.insuranceStatus = 'Yes'
    state.onboardingStep = 0
    navigate('signup')
  }
  if (action === 'back') goBack()
  if (action === 'previous-onboarding') {
    state.onboardingStep -= 1
    navigate('onboarding', 'back')
  }
  if (action === 'confirm-proposal') void decideAgentProposal(control.dataset.proposalId, 'confirm')
  if (action === 'cancel-proposal') void decideAgentProposal(control.dataset.proposalId, 'cancel')
  if (action === 'show-replay') void showReplay()
  if (action === 'undo-revision') void undoAgentRevision()
  if (action === 'clear-agent-filter') {
    state.agent.comparisonFilter = 'all'
    state.agent.pendingFocus = 'plan-comparison'
    render({ focus: false, preserveScroll: true })
  }
  if (action === 'stop-agent') state.agent.abortController?.abort()
  if (action === 'restart') {
    state.profileId = `browser-${createClientId()}`
    state.profile = createEmptyProfile()
    state.entrySource = 'intro'
    state.questionIndex = 0
    state.answers = []
    state.onboardingStep = 0
    state.agent.conversationId = ''
    state.agent.status = 'idle'
    state.agent.messages = []
    state.agent.actions = []
    state.agent.comparisonFilter = 'all'
    state.agent.pendingProposal = null
    state.agent.latestDelta = null
    state.agent.replay = []
    state.agent.canUndo = false
    state.runtime.status = 'idle'
    state.runtime.error = ''
    state.runtime.profile = null
    state.runtime.extraction = null
    state.runtime.recommendation = null
    state.runtime.explanation = null
    navigate('intro')
  }
})

document.addEventListener('keydown', (event) => {
  if (state.view !== 'quiz') return
  if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName)) return

  if (/^[1-4]$/.test(event.key)) {
    event.preventDefault()
    chooseAnswer(Number(event.key) - 1, true)
  }
  if (event.key === 'Escape') {
    event.preventDefault()
    goBack(true)
  }
})

render({ focus: false })
