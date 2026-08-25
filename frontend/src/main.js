import './style.css'
import workerImage from './assets/covercheck-worker.jpg'

const app = document.querySelector('#app')
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)')

const questions = [
  {
    kicker: 'Policy roll call',
    question: 'If someone asked what insurance covers you today, how complete would your list be?',
    note: 'Think personal policies, employer benefits, and government schemes.',
    answers: [
      ['Complete', 'I can name every policy and scheme.', 3],
      ['Mostly there', 'I know the main ones, not every detail.', 2],
      ['A little fuzzy', 'I remember one or two names.', 1],
      ['Unknown', 'I would need to ask my parents.', 0],
    ],
  },
  {
    kicker: 'Who holds the pen?',
    question: 'Do you know who owns each policy and who pays the premium?',
    note: 'The policy owner, life assured, and premium payer can be different people.',
    answers: [
      ['Yes, for all', 'The roles are clear to me.', 3],
      ['For most', 'One policy is still unclear.', 2],
      ['Only who pays', 'The ownership details are fuzzy.', 1],
      ['Not yet', 'I have never checked.', 0],
    ],
  },
  {
    kicker: 'The actual numbers',
    question: 'Could you state your death, TPD, and critical illness coverage amounts?',
    note: 'Knowing that you have a policy is different from knowing what it can pay.',
    answers: [
      ['Yes', 'I know all three amounts.', 3],
      ['Some', 'I know one or two amounts.', 2],
      ['Roughly', 'I only know an estimate.', 1],
      ['No', 'Those numbers are unknown.', 0],
    ],
  },
  {
    kicker: 'Hospital cover',
    question: 'How well do you know your ward level, deductible, and co-insurance?',
    note: 'These details affect what you pay when a hospital claim happens.',
    answers: [
      ['All clear', 'I can explain each item.', 3],
      ['Partly clear', 'I know my ward level.', 2],
      ['Name only', 'I only know the plan name.', 1],
      ['Unknown', 'I am not sure what I have.', 0],
    ],
  },
  {
    kicker: 'Work perks',
    question: 'Which insurance benefits disappear if you leave your employer?',
    note: 'Employer cover is useful, but it may not travel with you.',
    answers: [
      ['I know exactly', 'I checked the benefits schedule.', 3],
      ['Broadly', 'I know what is employer-provided.', 2],
      ['Not the limits', 'I know there is cover, not how much.', 1],
      ['No idea', 'I have not seen the schedule.', 0],
    ],
  },
  {
    kicker: 'Premium reality',
    question: 'Do you know your total annual premium and its share of your income?',
    note: 'MoneySense uses 15% of income as an educational protection-spending reference.',
    answers: [
      ['To the dollar', 'I track both amount and percentage.', 3],
      ['Total only', 'I know the annual amount.', 2],
      ['One policy only', 'The rest is still paid by family.', 1],
      ['Unknown', 'I have never added it up.', 0],
    ],
  },
  {
    kicker: 'The fine print',
    question: 'Could you point to the main exclusions and surrender implications?',
    note: 'This is about knowing where to verify them, not memorising every clause.',
    answers: [
      ['Yes', 'I know the document and sections.', 3],
      ['One of them', 'I can find exclusions or surrender terms.', 2],
      ['I would search', 'I have the documents somewhere.', 1],
      ['Not yet', 'I would need help locating them.', 0],
    ],
  },
  {
    kicker: 'Before saying yes',
    question: 'How ready are you to verify an adviser and compare alternatives?',
    note: 'A good next step is verifiable, not rushed.',
    answers: [
      ['Ready', 'I know the MAS register and what to compare.', 3],
      ['Mostly ready', 'I compare beyond premium price.', 2],
      ['Need a checklist', 'I am not sure what matters.', 1],
      ['Starting fresh', 'I would rely on the first explanation.', 0],
    ],
  },
]

const onboardingSteps = [
  ['Life stage', 'A little context, kept deliberately coarse.'],
  ['Monthly picture', 'Enough to test affordability, not to judge your lifestyle.'],
  ['Responsibilities', 'People and commitments your cover may need to protect.'],
  ['Coverage baseline', 'Government and employer cover come before extra plans.'],
  ['Priorities', 'Tell the comparison what “fit” means to you.'],
]

const state = {
  view: 'intro',
  questionIndex: 0,
  answers: [],
  onboardingStep: 0,
  direction: 'forward',
  keyboard: false,
  fileName: '',
  profile: {
    name: 'Ari',
    email: '',
    consent: false,
    ageBand: '25-29',
    employment: 'Full-time employee',
    income: 4200,
    expenses: 2300,
    emergencyMonths: 3,
    dependants: 'None',
    debt: 0,
    medishield: true,
    careshield: true,
    employer: true,
    goal: 'Protect my income and avoid duplicate cover',
    budget: 180,
    preference: 'Protection-only',
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

const getScore = () => {
  const earned = state.answers.reduce((total, answer) => total + (answer?.value ?? 0), 0)
  return Math.round(34 + (earned / (questions.length * 3)) * 56)
}

const brand = (tone = '') => `
  <a class="brand ${tone}" href="#" data-action="home" aria-label="CoverCheck SG home">
    <span class="brand-mark" aria-hidden="true">C</span>
    <span>CoverCheck SG</span>
  </a>
`

const trustNote = () => `
  <p class="trust-note">Educational comparison, not financial advice. All plans shown are synthetic demo data.</p>
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
      src="${workerImage}"
      alt="A young Asian professional reviewing printed material at a desk"
      width="1800"
      height="1350"
      fetchpriority="high"
    />
    <div class="intro-scrim" aria-hidden="true"></div>
    <header class="intro-header">
      ${brand('brand-inverse')}
      <span class="intro-label">Singapore · Ages 19-29</span>
    </header>
    <section class="intro-copy" aria-labelledby="intro-title">
      <p class="eyebrow intro-sequence">Your policies deserve a proper introduction.</p>
      <h1 id="intro-title" class="display-title intro-sequence">What exactly did your parents buy?</h1>
      <p class="intro-deck intro-sequence">Eight candid questions. A clearer next move. No NRIC, salary, or policy upload required.</p>
      <button class="primary-button intro-sequence" type="button" data-action="start-quiz">
        Check my readiness <span aria-hidden="true">→</span>
      </button>
    </section>
    <aside class="participation-note intro-sequence" aria-label="Pilot participation">
      <strong>24</strong>
      <span>hackathon pilot<br />completions this week</span>
    </aside>
    <p class="image-credit">Photo: Steve Jerry / Unsplash</p>
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
      ${appHeader({ step: `${String(state.questionIndex + 1).padStart(2, '0')} / 08`, back: true })}
      <div class="progress-track" aria-label="Quiz progress: question ${state.questionIndex + 1} of 8">
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
  const score = getScore()
  const policyKnown = (state.answers[0]?.value ?? 0) >= 2
  const coverageKnown = (state.answers[2]?.value ?? 0) >= 2
  const hospitalKnown = (state.answers[3]?.value ?? 0) >= 2
  const workKnown = (state.answers[4]?.value ?? 0) >= 2
  const unknownCount = [policyKnown, coverageKnown, hospitalKnown, workKnown].filter((value) => !value).length
  const headline = unknownCount === 0
    ? 'You have a strong working map. A fact-find can now test whether the numbers still fit.'
    : `You know parts of your cover. ${unknownCount} detail${unknownCount === 1 ? '' : 's'} still block a reliable comparison.`

  const coverageRow = (label, detail, known) => `
    <li>
      <span class="coverage-status ${known ? 'is-known' : 'is-unknown'}">${known ? 'Known' : 'Unknown'}</span>
      <strong>${label}</strong>
      <span>${detail}</span>
    </li>
  `

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
        <p class="report-definition">This score measures readiness to make an informed decision. It does not measure wealth, risk, or personal worth.</p>
      </section>

      <section class="coverage-map report-reveal reveal-2" aria-labelledby="coverage-title">
        <div class="section-index mono">01 · What is visible</div>
        <div>
          <h2 id="coverage-title">Your current coverage map</h2>
          <ul>
            ${coverageRow('Policy inventory', policyKnown ? 'Names and categories are mostly clear.' : 'Policy names still need to be confirmed.', policyKnown)}
            ${coverageRow('Benefit amounts', coverageKnown ? 'Key sums assured are available.' : 'Death, TPD, or CI amounts need review.', coverageKnown)}
            ${coverageRow('Hospital terms', hospitalKnown ? 'Ward and cost-sharing terms are understood.' : 'Ward, deductible, or co-insurance is unresolved.', hospitalKnown)}
            ${coverageRow('Employer expiry', workKnown ? 'Portable and employer cover are distinguishable.' : 'Coverage after a job change is unknown.', workKnown)}
          </ul>
        </div>
      </section>

      <section class="benchmark-section report-reveal reveal-3" aria-labelledby="benchmark-title">
        <div class="section-index mono">02 · Context, not competition</div>
        <div class="benchmark-content">
          <div class="benchmark-heading">
            <h2 id="benchmark-title">Hackathon pilot participants</h2>
            <p>Similar participants most often missed employer-coverage expiry. No rank, no shame.</p>
          </div>
          <div class="benchmark-tape" role="img" aria-label="Your score ${score}; pilot median 61 out of 100">
            <span class="tape-label tape-start mono">0</span>
            <span class="tape-label tape-end mono">100</span>
            <span class="tape-marker pilot" style="--position: 61%"><i></i><b>Pilot median 61</b></span>
            <span class="tape-marker you" style="--position: ${score}%"><i></i><b>You ${score}</b></span>
          </div>
          <p class="source-line mono">n=24 · ages 19-29 · collected 18-25 Aug 2026 · demo pilot sample</p>
        </div>
      </section>

      <section class="result-action report-reveal reveal-4">
        <div>
          <span class="section-index mono">NEXT · 6-8 MIN</span>
          <h2>Turn the unknowns into a comparison you can inspect.</h2>
        </div>
        <button class="primary-button" type="button" data-action="create-account">Create a mock account <span aria-hidden="true">→</span></button>
      </section>
      <footer class="report-footer">${trustNote()}</footer>
    </main>
  `
}

const signupView = () => `
  <main class="form-screen" data-screen="signup">
    ${appHeader({ back: true })}
    <section class="form-intro view-enter">
      <p class="eyebrow">Save your progress</p>
      <h1 class="form-title screen-title" tabindex="-1">A mock account. No account system hiding underneath.</h1>
      <p>These details stay in this browser tab and disappear on refresh. We only use them to personalise the prototype.</p>
    </section>
    <form id="account-form" class="account-form view-enter" novalidate>
      <label class="field">
        <span>First name</span>
        <input type="text" name="name" data-field="name" value="${escapeHtml(state.profile.name)}" autocomplete="given-name" required />
      </label>
      <label class="field">
        <span>Email</span>
        <input type="email" name="email" data-field="email" value="${escapeHtml(state.profile.email)}" placeholder="you@example.com" autocomplete="email" required />
      </label>
      <label class="consent-row">
        <input type="checkbox" name="consent" data-field="consent" ${state.profile.consent ? 'checked' : ''} required />
        <span>I understand this is a local prototype and consent to using my answers for this session.</span>
      </label>
      <button class="primary-button" type="submit">Continue to the fact-find <span aria-hidden="true">→</span></button>
      <p class="form-error" id="account-error" role="alert"></p>
    </form>
    <aside class="privacy-aside view-enter">
      <span class="mono">NOT COLLECTED</span>
      <p>No NRIC, medical diagnoses, payment details, or beneficiary identities.</p>
    </aside>
  </main>
`

const radioGroup = (name, label, options, current) => `
  <fieldset class="choice-field">
    <legend>${label}</legend>
    <div class="segmented-options">
      ${options.map((option) => `
        <label>
          <input type="radio" name="${name}" data-field="${name}" value="${escapeHtml(option)}" ${current === option ? 'checked' : ''} />
          <span>${option}</span>
        </label>
      `).join('')}
    </div>
  </fieldset>
`

const onboardingFields = () => {
  const profile = state.profile
  switch (state.onboardingStep) {
    case 0:
      return `
        ${radioGroup('ageBand', 'Age band', ['19-24', '25-29'], profile.ageBand)}
        ${radioGroup('employment', 'Employment', ['Full-time employee', 'Contract or gig work', 'Starting work soon'], profile.employment)}
        <label class="field">
          <span>Expected job change</span>
          <select data-field="jobChange" name="jobChange">
            <option>No change expected</option>
            <option>Possibly within 12 months</option>
            <option>Actively changing roles</option>
          </select>
        </label>
      `
    case 1:
      return `
        <div class="field-pair">
          <label class="field money-field"><span>Monthly take-home income</span><i>S$</i><input type="number" min="0" step="100" data-field="income" value="${profile.income}" /></label>
          <label class="field money-field"><span>Monthly essentials</span><i>S$</i><input type="number" min="0" step="100" data-field="expenses" value="${profile.expenses}" /></label>
        </div>
        <label class="range-field">
          <span><b>Emergency savings</b><output>${profile.emergencyMonths} months</output></span>
          <input type="range" min="0" max="12" step="1" data-field="emergencyMonths" value="${profile.emergencyMonths}" />
          <small>MoneySense educational reference: 3-6 months of expenses.</small>
        </label>
      `
    case 2:
      return `
        ${radioGroup('dependants', 'People who rely on your income', ['None', 'Parents', 'Partner or child', 'Multiple people'], profile.dependants)}
        <label class="field money-field"><span>Major outstanding debt</span><i>S$</i><input type="number" min="0" step="1000" data-field="debt" value="${profile.debt}" /></label>
        <p class="field-caption">Use a broad amount. Do not enter account numbers or lender details.</p>
      `
    case 3:
      return `
        <fieldset class="check-field">
          <legend>Coverage you believe is active</legend>
          <label><input type="checkbox" data-field="medishield" ${profile.medishield ? 'checked' : ''} /><span><b>MediShield Life</b><small>Basic health insurance for Singapore Citizens and PRs.</small></span></label>
          <label><input type="checkbox" data-field="careshield" ${profile.careshield ? 'checked' : ''} /><span><b>CareShield Life</b><small>Long-term care support, where applicable.</small></span></label>
          <label><input type="checkbox" data-field="employer" ${profile.employer ? 'checked' : ''} /><span><b>Employer medical or group life</b><small>Usually tied to your current employment.</small></span></label>
        </fieldset>
        <p class="field-caption">“Believe” is intentional. Uploaded evidence can confirm or correct this later.</p>
      `
    default:
      return `
        <label class="field">
          <span>Primary goal</span>
          <textarea rows="3" data-field="goal">${escapeHtml(profile.goal)}</textarea>
        </label>
        <label class="range-field">
          <span><b>Comfortable monthly premium budget</b><output>${formatCurrency(profile.budget)}</output></span>
          <input type="range" min="50" max="500" step="10" data-field="budget" value="${profile.budget}" />
          <small>This is a comfort limit, not a spending target.</small>
        </label>
        ${radioGroup('preference', 'Product preference', ['Protection-only', 'Open to bundled products', 'Not sure yet'], profile.preference)}
      `
  }
}

const onboardingView = () => {
  const current = onboardingSteps[state.onboardingStep]
  return `
    <main class="onboarding-screen" data-screen="onboarding">
      ${appHeader({ step: `FACT-FIND ${state.onboardingStep + 1} / ${onboardingSteps.length}`, back: true })}
      <div class="onboarding-layout">
        <aside class="stepper" aria-label="Onboarding progress">
          <p class="mono">YOUR FACT-FIND</p>
          <ol>
            ${onboardingSteps.map((step, index) => `
              <li class="${index === state.onboardingStep ? 'is-current' : ''} ${index < state.onboardingStep ? 'is-complete' : ''}">
                <span>${String(index + 1).padStart(2, '0')}</span><b>${step[0]}</b>
              </li>
            `).join('')}
          </ol>
          <p class="stepper-note">Your answers stay editable. Unknown is a valid answer.</p>
        </aside>
        <section class="onboarding-main view-enter">
          <p class="eyebrow">Step ${state.onboardingStep + 1}</p>
          <h1 class="onboarding-title screen-title" tabindex="-1">${current[0]}</h1>
          <p class="onboarding-deck">${current[1]}</p>
          <form id="onboarding-form" class="fact-form">
            ${onboardingFields()}
            <div class="form-actions">
              ${state.onboardingStep > 0 ? '<button class="secondary-button" type="button" data-action="previous-onboarding">Previous</button>' : ''}
              <button class="primary-button" type="submit">${state.onboardingStep === onboardingSteps.length - 1 ? 'Review a policy' : 'Next step'} <span aria-hidden="true">→</span></button>
            </div>
          </form>
        </section>
      </div>
    </main>
  `
}

const uploadView = () => `
  <main class="upload-screen" data-screen="upload">
    ${appHeader({ step: 'POLICY REVIEW', back: true })}
    <section class="upload-heading view-enter">
      <p class="eyebrow">Bring the evidence</p>
      <h1 class="upload-title screen-title" tabindex="-1">One policy document. Every uncertain field stays visible.</h1>
      <p>For this prototype, no file leaves your device and no OCR service runs. Choosing a file loads the same reviewed synthetic extraction.</p>
    </section>
    <section class="upload-zone view-enter" aria-labelledby="upload-label">
      <div class="upload-symbol" aria-hidden="true"><span>PDF</span></div>
      <div>
        <h2 id="upload-label">Drop a policy schedule here</h2>
        <p>PDF, JPG, or PNG · demo only · avoid real personal documents</p>
      </div>
      <label class="primary-button file-button">
        Choose a file
        <input id="policy-file" type="file" accept=".pdf,.jpg,.jpeg,.png" />
      </label>
      <span class="or-label mono">OR</span>
      <button class="secondary-button" type="button" data-action="use-sample">Use synthetic sample policy</button>
    </section>
    <div class="upload-guardrails view-enter">
      <p><span class="mono">01</span> Page-level evidence stays attached to each field.</p>
      <p><span class="mono">02</span> Low-confidence values are never silently guessed.</p>
      <p><span class="mono">03</span> Replace or surrender advice is outside this prototype.</p>
    </div>
  </main>
`

const ocrField = (label, value, confidence, unresolved = false) => `
  <label class="ocr-field ${unresolved ? 'is-unresolved' : ''}">
    <span><b>${label}</b><i class="confidence ${confidence >= 90 ? 'high' : confidence >= 75 ? 'medium' : 'low'}">${confidence}%</i></span>
    <input type="text" value="${escapeHtml(value)}" ${unresolved ? 'placeholder="Review required"' : ''} />
    <small class="mono">${unresolved ? 'UNRESOLVED · PAGE 6' : `VERIFIED AGAINST PAGE ${label === 'Product' ? '1' : label === 'Premium' ? '2' : '3'}`}</small>
  </label>
`

const ocrView = () => `
  <main class="ocr-screen" data-screen="ocr">
    ${appHeader({ step: 'EXTRACTION REVIEW', back: true })}
    <div class="ocr-layout">
      <section class="document-panel view-enter" aria-label="Synthetic policy document preview">
        <div class="document-toolbar">
          <span class="mono">${escapeHtml(state.fileName || 'Inherited_Policy_Sample.pdf')}</span>
          <span class="mono">PAGE 1 / 8</span>
        </div>
        <article class="document-page">
          <div class="document-brand">MERLION MUTUAL</div>
          <p class="mono">POLICY SCHEDULE · SYNTHETIC DEMO</p>
          <h2>Foundation Term Protect</h2>
          <div class="document-rule"></div>
          <dl>
            <div><dt>Policy owner</dt><dd>Tan Mei</dd></div>
            <div><dt>Life assured</dt><dd>Ari Tan</dd></div>
            <div class="document-highlight"><dt>Death / TPD benefit</dt><dd>S$100,000</dd></div>
            <div><dt>Policy term</dt><dd>To age 65</dd></div>
            <div><dt>Annual premium</dt><dd>S$684.00</dd></div>
          </dl>
          <p class="document-fineprint">This synthetic document is created for the CoverCheck SG hackathon prototype. It is not an issued insurance contract.</p>
        </article>
      </section>
      <section class="extraction-panel">
        <div class="extraction-heading ocr-reveal">
          <p class="eyebrow">6 fields found · 1 needs you</p>
          <h1 class="ocr-title screen-title" tabindex="-1">Read the extraction, not just the confidence score.</h1>
          <p>Confidence measures text recognition. It does not prove that the policy still suits you.</p>
        </div>
        <form class="ocr-fields">
          ${ocrField('Insurer', 'Merlion Mutual', 99)}
          ${ocrField('Product', 'Foundation Term Protect', 98)}
          ${ocrField('Death / TPD benefit', 'S$100,000', 96)}
          ${ocrField('Premium', 'S$57 monthly', 93)}
          ${ocrField('Coverage term', 'To age 65', 88)}
          ${ocrField('Critical illness rider', '', 42, true)}
        </form>
        <div class="ocr-actions ocr-reveal">
          <p><span class="status-dot"></span> Five values match visible page evidence.</p>
          <button class="primary-button" type="button" data-action="confirm-extraction">Confirm and compare <span aria-hidden="true">→</span></button>
        </div>
      </section>
    </div>
  </main>
`

const comparisonView = () => {
  const annualIncome = Number(state.profile.income || 4200) * 12
  const deathTarget = annualIncome * 9
  const ciTarget = annualIncome * 4
  const deathGap = Math.max(0, deathTarget - 100000)
  const ciGap = Math.max(0, ciTarget - 50000)

  return `
    <main class="comparison-screen" data-screen="comparison">
      ${appHeader()}
      <section class="comparison-lead view-enter">
        <div>
          <p class="eyebrow">Comparison ready for ${escapeHtml(state.profile.name || 'you')}</p>
          <h1 class="comparison-title screen-title" tabindex="-1">Your inherited cover is a start. The remaining gap is mostly income protection.</h1>
        </div>
        <div class="comparison-meta">
          <span class="synthetic-badge">Synthetic plan data</span>
          <span class="mono">PROFILE V1 · RULESET 2026.08</span>
        </div>
      </section>

      <section class="gap-strip" aria-labelledby="gap-title">
        <div class="gap-intro">
          <span class="section-index mono">01 · CALCULATED GAPS</span>
          <h2 id="gap-title">Where the numbers point</h2>
          <p>MoneySense reference points are educational benchmarks, not universal prescriptions.</p>
        </div>
        <div class="gap-stat">
          <span>Death / TPD</span>
          <strong class="mono">${formatCurrency(deathGap)}</strong>
          <small>gap against 9× annual income</small>
        </div>
        <div class="gap-stat">
          <span>Critical illness</span>
          <strong class="mono">${formatCurrency(ciGap)}</strong>
          <small>gap against 4× annual income</small>
        </div>
        <div class="gap-stat is-unknown">
          <span>Disability income</span>
          <strong>Unknown</strong>
          <small>employer benefit limit not provided</small>
        </div>
      </section>

      <section class="comparison-section" aria-labelledby="compare-title">
        <div class="comparison-section-heading">
          <div>
            <span class="section-index mono">02 · ELIGIBLE OPTIONS</span>
            <h2 id="compare-title">Compare the trade-offs, not just the premium.</h2>
          </div>
          <p>Budget checked against your ${formatCurrency(state.profile.budget)} monthly comfort limit.</p>
        </div>
        <div class="table-wrap" tabindex="0" aria-label="Scrollable plan comparison table">
          <table class="plan-table">
            <thead>
              <tr>
                <th scope="col">Compare</th>
                <th scope="col" class="recommended"><span>Closest fit</span>LionCity Term Flex</th>
                <th scope="col">Harbour Essential CI</th>
                <th scope="col">Orchid Income Shield</th>
              </tr>
            </thead>
            <tbody>
              <tr><th scope="row">Category</th><td>Term life + TPD</td><td>Standalone CI</td><td>Disability income</td></tr>
              <tr><th scope="row">Monthly premium</th><td><strong>S$78</strong></td><td><strong>S$64</strong></td><td><strong>S$92</strong></td></tr>
              <tr><th scope="row">Illustrated cover</th><td>S$400,000</td><td>S$150,000</td><td>S$2,000 / month</td></tr>
              <tr><th scope="row">Term</th><td>To age 65</td><td>30 years</td><td>To age 60</td></tr>
              <tr><th scope="row">Main trade-off</th><td>Does not close the full benchmark gap</td><td>No death or TPD benefit</td><td>90-day waiting period</td></tr>
              <tr><th scope="row">Notable exclusion</th><td>Pre-existing conditions assessed at underwriting</td><td>Early-stage CI not included</td><td>Own-occupation definition changes after 24 months</td></tr>
              <tr><th scope="row">Evidence</th><td><a href="https://www.moneysense.gov.sg/life-insurance/" target="_blank" rel="noreferrer">Source notes ↗</a><br /><small class="mono">SYN-LTF-01 · 25 AUG 2026</small></td><td><a href="https://www.moneysense.gov.sg/insurance-basics/" target="_blank" rel="noreferrer">Source notes ↗</a><br /><small class="mono">SYN-HEC-02 · 25 AUG 2026</small></td><td><a href="https://www.moneysense.gov.sg/insurance-basics/" target="_blank" rel="noreferrer">Source notes ↗</a><br /><small class="mono">SYN-OIS-03 · 25 AUG 2026</small></td></tr>
            </tbody>
          </table>
        </div>

        <div class="reasoning-drawers">
          <details open>
            <summary><span><b>Why LionCity Term Flex ranks first</b><small>Fit score 82 / 100 · synthetic</small></span><i aria-hidden="true">+</i></summary>
            <div class="drawer-content"><p>It addresses the largest calculated gap, stays below your stated budget, matches your protection-only preference, and runs to age 65. It ranks ahead of the CI option because death and TPD are the larger quantified gap in this profile.</p></div>
          </details>
          <details>
            <summary><span><b>What the ranking does not know</b><small>Three assumptions remain</small></span><i aria-hidden="true">+</i></summary>
            <div class="drawer-content"><p>Employer disability-income limits, the inherited policy's CI rider, and underwriting outcomes remain unknown. The comparison should be refreshed after those values are verified.</p></div>
          </details>
          <details>
            <summary><span><b>Excluded synthetic option</b><small>Meridian Whole Life Plus · over budget</small></span><i aria-hidden="true">+</i></summary>
            <div class="drawer-content"><p>Excluded because its illustrated S$286 monthly premium exceeds your S$${state.profile.budget} comfort limit and conflicts with your ${escapeHtml(state.profile.preference.toLowerCase())} preference.</p></div>
          </details>
        </div>
      </section>

      <section class="decision-footer">
        <div>
          <span class="section-index mono">BEFORE YOU ACT</span>
          <h2>Verify the policy wording and the person advising you.</h2>
          <p>Do not cancel or replace inherited cover based on this prototype. A replacement may not reproduce existing benefits or underwriting terms.</p>
        </div>
        <a class="primary-button" href="https://eservices.mas.gov.sg/rr" target="_blank" rel="noreferrer">Open MAS register <span aria-hidden="true">↗</span></a>
      </section>
      <footer class="comparison-footer">
        ${brand()}
        ${trustNote()}
        <button class="text-button" type="button" data-action="restart">Restart prototype</button>
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
  upload: uploadView,
  ocr: ocrView,
  comparison: comparisonView,
}

function render({ focus = true } = {}) {
  app.innerHTML = views[state.view]()
  document.body.dataset.view = state.view
  window.scrollTo({ top: 0, behavior: 'instant' })

  if (focus) {
    requestAnimationFrame(() => {
      const title = app.querySelector('.screen-title')
      if (title && (state.keyboard || reduceMotion.matches)) title.focus({ preventScroll: true })
    })
  }
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
  if (state.view === 'signup') navigate('result', 'back', keyboard)
  else if (state.view === 'onboarding') {
    if (state.onboardingStep === 0) navigate('signup', 'back', keyboard)
    else {
      state.onboardingStep -= 1
      state.direction = 'back'
      state.keyboard = keyboard
      render()
    }
  } else if (state.view === 'upload') {
    state.onboardingStep = onboardingSteps.length - 1
    navigate('onboarding', 'back', keyboard)
  } else if (state.view === 'ocr') navigate('upload', 'back', keyboard)
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
  state.profile[key] = isBoolean ? target.checked : isNumber ? Number(target.value) : target.value

  if (target.type === 'range') {
    const output = target.closest('.range-field')?.querySelector('output')
    if (output) output.textContent = key === 'budget' ? formatCurrency(target.value) : `${target.value} months`
  }
}

app.addEventListener('input', (event) => updateProfileField(event.target))
app.addEventListener('change', (event) => {
  updateProfileField(event.target)
  if (event.target.id === 'policy-file' && event.target.files?.[0]) {
    state.fileName = event.target.files[0].name
    navigate('ocr')
  }
})

app.addEventListener('submit', (event) => {
  event.preventDefault()
  if (event.target.id === 'account-form') {
    const error = app.querySelector('#account-error')
    if (!event.target.checkValidity()) {
      if (error) error.textContent = 'Add a valid email and confirm consent to continue.'
      event.target.reportValidity()
      return
    }
    state.onboardingStep = 0
    navigate('onboarding', 'forward', true)
  }

  if (event.target.id === 'onboarding-form') {
    if (state.onboardingStep === onboardingSteps.length - 1) navigate('upload', 'forward', true)
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
  if (action === 'back') goBack()
  if (action === 'create-account') navigate('signup')
  if (action === 'previous-onboarding') {
    state.onboardingStep -= 1
    navigate('onboarding', 'back')
  }
  if (action === 'use-sample') {
    state.fileName = 'Inherited_Policy_Sample.pdf'
    navigate('ocr')
  }
  if (action === 'confirm-extraction') navigate('comparison')
  if (action === 'restart') {
    state.questionIndex = 0
    state.answers = []
    state.onboardingStep = 0
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
