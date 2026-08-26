import './style.css'
import workerImage from './assets/covercheck-worker.jpg'

const app = document.querySelector('#app')
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)')

const questions = [
  {
    kicker: 'What you have',
    question: 'Do you know which insurance plans you have?',
    note: 'Include plans from family, work and CPF.',
    answers: [
      ['Yes', 'All of them', 3],
      ['Mostly', 'The main ones', 2],
      ['One or two', 'I am not sure', 1],
      ['No clue', 'I need to check', 0],
    ],
  },
  {
    kicker: 'What it pays',
    question: 'Do you know what your plans would pay for?',
    note: 'For example: hospital bills, illness or lost income.',
    answers: [
      ['Yes', 'The key payouts', 3],
      ['Mostly', 'A few gaps', 2],
      ['Roughly', 'Just the basics', 1],
      ['No clue', 'I only know the names', 0],
    ],
  },
  {
    kicker: 'What it costs',
    question: 'Do you know your total insurance cost each month?',
    note: 'Count plans paid by you or your family.',
    answers: [
      ['Exactly', 'I track it', 3],
      ['Roughly', 'Close enough', 2],
      ['Some of it', 'Not every plan', 1],
      ['No clue', 'Never added it up', 0],
    ],
  },
  {
    kicker: 'Work cover',
    question: 'Would your cover change if you left your job?',
    note: 'Some work benefits end on your last day.',
    answers: [
      ['I know', 'I checked', 3],
      ['Probably', 'I know the basics', 2],
      ['Not sure', 'I should ask HR', 1],
      ['No clue', 'Never thought about it', 0],
    ],
  },
  {
    kicker: 'The limits',
    question: 'Do you know what your plans do not cover?',
    note: 'These limits are called exclusions.',
    answers: [
      ['Yes', 'The main limits', 3],
      ['Some', 'One or two', 2],
      ['Vaguely', 'I need a refresh', 1],
      ['No clue', 'I have not checked', 0],
    ],
  },
]

const onboardingSteps = [
  ['Life stage', 'Tell us where you are now.'],
  ['Monthly budget', 'A quick affordability check.'],
  ['People and loans', 'Who relies on you?'],
  ['Cover now', 'Start with what you already have.'],
  ['Priorities', 'What matters most?'],
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
      alt="Three young adults at Marina Bay with Marina Bay Sands behind them"
      width="1800"
      height="1200"
      fetchpriority="high"
    />
    <div class="intro-scrim" aria-hidden="true"></div>
    <header class="intro-header">
      ${brand('brand-inverse')}
      <span class="intro-label">Singapore · Ages 18-30</span>
    </header>
    <section class="intro-copy" aria-labelledby="intro-title">
      <p class="eyebrow intro-sequence">Insurance, minus the blur.</p>
      <h1 id="intro-title" class="display-title intro-sequence">What did your parents actually buy?</h1>
      <p class="intro-deck intro-sequence">Five quick questions. No salary, NRIC or upload needed.</p>
      <button class="primary-button intro-sequence" type="button" data-action="start-quiz">
        Check my readiness <span aria-hidden="true">→</span>
      </button>
    </section>
    <aside class="participation-note intro-sequence" aria-label="Pilot participation">
      <strong>24</strong>
      <span>hackathon pilot<br />completions this week</span>
    </aside>
    <p class="image-credit">Photo: krzhck / Unsplash · Marina Bay</p>
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
  const score = getScore()
  const policyKnown = (state.answers[0]?.value ?? 0) >= 2
  const coverageKnown = (state.answers[1]?.value ?? 0) >= 2
  const costKnown = (state.answers[2]?.value ?? 0) >= 2
  const workKnown = (state.answers[3]?.value ?? 0) >= 2
  const exclusionsKnown = (state.answers[4]?.value ?? 0) >= 2
  const unknownCount = [policyKnown, coverageKnown, costKnown, workKnown, exclusionsKnown].filter((value) => !value).length
  const headline = unknownCount === 0
    ? 'You know the basics. Now check if the numbers still fit.'
    : `${unknownCount} thing${unknownCount === 1 ? '' : 's'} to check before you compare plans.`

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
        <p class="report-definition">This score measures what you know, not how well-off or protected you are.</p>
      </section>

      <section class="coverage-map report-reveal reveal-2" aria-labelledby="coverage-title">
        <div class="section-index mono">01 · What is visible</div>
        <div>
          <h2 id="coverage-title">What you know so far</h2>
          <ul>
            ${coverageRow('Your plans', policyKnown ? 'You know the main plans.' : 'Check which plans you have.', policyKnown)}
            ${coverageRow('What they pay', coverageKnown ? 'You know the main payouts.' : 'Check what each plan pays for.', coverageKnown)}
            ${coverageRow('Monthly cost', costKnown ? 'You know the total cost.' : 'Add up every premium.', costKnown)}
            ${coverageRow('Work cover', workKnown ? 'You know what ends with your job.' : 'Ask HR what ends when you leave.', workKnown)}
            ${coverageRow('Plan limits', exclusionsKnown ? 'You know the main exclusions.' : 'Check what is not covered.', exclusionsKnown)}
          </ul>
        </div>
      </section>

      <section class="benchmark-section report-reveal reveal-3" aria-labelledby="benchmark-title">
        <div class="section-index mono">02 · Context, not competition</div>
        <div class="benchmark-content">
          <div class="benchmark-heading">
            <h2 id="benchmark-title">Hackathon pilot participants</h2>
            <p>See where your score sits. This is context, not a ranking.</p>
          </div>
          <div class="benchmark-distribution" role="img" aria-label="Bell curve of pilot readiness scores. Your score is ${score}; the pilot midpoint is 61.">
            <svg viewBox="0 0 700 240" preserveAspectRatio="none" aria-hidden="true">
              <path class="distribution-area" d="M0 220 C85 220 113 210 150 190 C205 160 225 80 300 42 C340 21 360 21 400 42 C475 80 495 160 550 190 C587 210 615 220 700 220 L700 240 L0 240 Z" />
              <path class="distribution-line" d="M0 220 C85 220 113 210 150 190 C205 160 225 80 300 42 C340 21 360 21 400 42 C475 80 495 160 550 190 C587 210 615 220 700 220" />
            </svg>
            <span class="distribution-marker pilot" style="--position: 61%"><i></i><b>Pilot midpoint<br />61</b></span>
            <span class="distribution-marker you" style="--position: ${score}%"><i></i><b>You<br />${score}</b></span>
            <span class="distribution-scale mono"><i>0</i><i>50</i><i>100</i></span>
          </div>
          <p class="source-line mono">n=24 · ages 19-29 · collected 18-25 Aug 2026 · demo pilot sample</p>
        </div>
      </section>

      <section class="result-action report-reveal reveal-4">
        <div>
          <span class="section-index mono">NEXT · ABOUT 5 MIN</span>
          <h2>Fill the gaps. Then compare.</h2>
        </div>
        <button class="primary-button" type="button" data-action="create-account">Continue with a demo account <span aria-hidden="true">→</span></button>
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
      <h1 class="form-title screen-title" tabindex="-1">A demo account. Nothing is sent or saved.</h1>
      <p>Your answers stay in this tab and reset when you refresh.</p>
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
        <span>I understand my answers stay in this browser session.</span>
      </label>
      <button class="primary-button" type="submit">Start my profile <span aria-hidden="true">→</span></button>
      <p class="form-error" id="account-error" role="alert"></p>
    </form>
    <aside class="privacy-aside view-enter">
      <span class="mono">NOT COLLECTED</span>
      <p>No NRIC, medical details, payment or beneficiary information.</p>
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
          <span>Changing jobs soon?</span>
          <select data-field="jobChange" name="jobChange">
            <option>No plans</option>
            <option>Maybe this year</option>
            <option>Yes, soon</option>
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
          <small>MoneySense guide: aim for 3-6 months of expenses.</small>
        </label>
      `
    case 2:
      return `
        ${radioGroup('dependants', 'Who relies on your income?', ['None', 'Parents', 'Partner or child', 'Multiple people'], profile.dependants)}
        <label class="field money-field"><span>Loans left to pay</span><i>S$</i><input type="number" min="0" step="1000" data-field="debt" value="${profile.debt}" /></label>
        <p class="field-caption">A rough total is enough.</p>
      `
    case 3:
      return `
        <fieldset class="check-field">
          <legend>Cover you already have</legend>
          <label><input type="checkbox" data-field="medishield" ${profile.medishield ? 'checked' : ''} /><span><b>MediShield Life</b><small>Helps with large hospital bills.</small></span></label>
          <label><input type="checkbox" data-field="careshield" ${profile.careshield ? 'checked' : ''} /><span><b>CareShield Life</b><small>Monthly support for severe disability.</small></span></label>
          <label><input type="checkbox" data-field="employer" ${profile.employer ? 'checked' : ''} /><span><b>Work insurance</b><small>Cover from your current job.</small></span></label>
        </fieldset>
        <p class="field-caption">Not sure? Leave it unchecked. We will show it as unknown.</p>
      `
    default:
      return `
        <label class="field">
          <span>Main goal</span>
          <textarea rows="3" data-field="goal">${escapeHtml(profile.goal)}</textarea>
        </label>
        <label class="range-field">
          <span><b>Monthly insurance budget</b><output>${formatCurrency(profile.budget)}</output></span>
          <input type="range" min="50" max="500" step="10" data-field="budget" value="${profile.budget}" />
          <small>This is a comfort limit, not a spending target.</small>
        </label>
        ${radioGroup('preference', 'Plan type', ['Protection-only', 'Open to plans with savings', 'Not sure yet'], profile.preference)}
      `
  }
}

const onboardingView = () => {
  const current = onboardingSteps[state.onboardingStep]
  return `
    <main class="onboarding-screen" data-screen="onboarding">
      ${appHeader({ step: `PROFILE ${state.onboardingStep + 1} / ${onboardingSteps.length}`, back: true })}
      <div class="onboarding-layout">
        <aside class="stepper" aria-label="Onboarding progress">
          <p class="mono">YOUR PROFILE</p>
          <ol>
            ${onboardingSteps.map((step, index) => `
              <li class="${index === state.onboardingStep ? 'is-current' : ''} ${index < state.onboardingStep ? 'is-complete' : ''}">
                <span>${String(index + 1).padStart(2, '0')}</span><b>${step[0]}</b>
              </li>
            `).join('')}
          </ol>
          <p class="stepper-note">You can go back. It is fine not to know.</p>
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
      <p class="eyebrow">Check a policy</p>
      <h1 class="upload-title screen-title" tabindex="-1">Upload one policy. We will flag anything unclear.</h1>
      <p>Demo only: your file stays on this device. This screen always loads a fake sample.</p>
    </section>
    <section class="upload-zone view-enter" aria-labelledby="upload-label">
      <div class="upload-symbol" aria-hidden="true"><span>PDF</span></div>
      <div>
        <h2 id="upload-label">Drop a policy document here</h2>
        <p>PDF, JPG or PNG · Use a sample, not your real policy</p>
      </div>
      <label class="primary-button file-button">
        Choose a file
        <input id="policy-file" type="file" accept=".pdf,.jpg,.jpeg,.png" />
      </label>
      <span class="or-label mono">OR</span>
      <button class="secondary-button" type="button" data-action="use-sample">Use synthetic sample policy</button>
    </section>
    <div class="upload-guardrails view-enter">
      <p><span class="mono">01</span> Every detail links back to a page.</p>
      <p><span class="mono">02</span> Unclear text is marked for review.</p>
      <p><span class="mono">03</span> This demo never tells you to cancel.</p>
    </div>
  </main>
`

const ocrField = (label, value, confidence, unresolved = false) => `
  <label class="ocr-field ${unresolved ? 'is-unresolved' : ''}">
    <span><b>${label}</b><i class="confidence ${confidence >= 90 ? 'high' : confidence >= 75 ? 'medium' : 'low'}">${confidence}%</i></span>
    <input type="text" value="${escapeHtml(value)}" ${unresolved ? 'placeholder="Review required"' : ''} />
    <small class="mono">${unresolved ? 'TO CHECK · PAGE 6' : 'MATCHED ON PAGE 1'}</small>
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
            <div class="document-highlight"><dt>Death / permanent disability</dt><dd>S$100,000</dd></div>
            <div><dt>Policy term</dt><dd>To age 65</dd></div>
            <div><dt>Annual premium</dt><dd>S$684.00</dd></div>
          </dl>
          <p class="document-fineprint">This synthetic document is created for the CoverCheck SG hackathon prototype. It is not an issued insurance contract.</p>
        </article>
      </section>
      <section class="extraction-panel">
        <div class="extraction-heading ocr-reveal">
          <p class="eyebrow">6 details found · 1 to check</p>
          <h1 class="ocr-title screen-title" tabindex="-1">Check the details before using them.</h1>
          <p>Confidence shows how clearly the text was read. It does not rate the plan.</p>
        </div>
        <form class="ocr-fields">
          ${ocrField('Insurance company', 'Merlion Mutual', 99)}
          ${ocrField('Plan name', 'Foundation Term Protect', 98)}
          ${ocrField('Death / permanent disability', 'S$100,000', 96)}
          ${ocrField('Monthly cost', 'S$57', 93)}
          ${ocrField('Cover ends', 'At age 65', 88)}
          ${ocrField('Critical illness add-on', '', 42, true)}
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
          <h1 class="comparison-title screen-title" tabindex="-1">Your current plan covers part of the basics.</h1>
        </div>
        <div class="comparison-meta">
          <span class="synthetic-badge">Synthetic plan data</span>
          <span class="mono">PROFILE V1 · RULESET 2026.08</span>
        </div>
      </section>

      <section class="gap-strip" aria-labelledby="gap-title">
        <div class="gap-intro">
          <span class="section-index mono">01 · CALCULATED GAPS</span>
          <h2 id="gap-title">What may still be missing</h2>
          <p>MoneySense figures are a guide, not a target for everyone.</p>
        </div>
        <div class="gap-stat">
          <span>Death or permanent disability</span>
          <strong class="mono">${formatCurrency(deathGap)}</strong>
          <small>MoneySense guide: 9× annual income</small>
        </div>
        <div class="gap-stat">
          <span>Critical illness</span>
          <strong class="mono">${formatCurrency(ciGap)}</strong>
          <small>MoneySense guide: 4× annual income</small>
        </div>
        <div class="gap-stat is-unknown">
          <span>Income if you cannot work</span>
          <strong>Unknown</strong>
          <small>work benefit details not provided</small>
        </div>
      </section>

      <section class="comparison-section" aria-labelledby="compare-title">
        <div class="comparison-section-heading">
          <div>
            <span class="section-index mono">02 · ELIGIBLE OPTIONS</span>
            <h2 id="compare-title">Compare what you pay and get.</h2>
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
              <tr><th scope="row">What it covers</th><td>Death + permanent disability</td><td>Critical illness</td><td>Income if you cannot work</td></tr>
              <tr><th scope="row">Monthly premium</th><td><strong>S$78</strong></td><td><strong>S$64</strong></td><td><strong>S$92</strong></td></tr>
              <tr><th scope="row">Benefit amount</th><td>S$400,000</td><td>S$150,000</td><td>S$2,000 / month</td></tr>
              <tr><th scope="row">How long</th><td>To age 65</td><td>30 years</td><td>To age 60</td></tr>
              <tr><th scope="row">Main downside</th><td>Does not fill the full gap</td><td>No death or disability payout</td><td>90-day wait before payouts</td></tr>
              <tr><th scope="row">Key limit</th><td>Approval and price depend on health history</td><td>Early-stage illness not included</td><td>Claim test changes after 24 months</td></tr>
              <tr><th scope="row">Evidence</th><td><a href="https://www.moneysense.gov.sg/life-insurance/" target="_blank" rel="noreferrer">Source notes ↗</a><br /><small class="mono">SYN-LTF-01 · 25 AUG 2026</small></td><td><a href="https://www.moneysense.gov.sg/insurance-basics/" target="_blank" rel="noreferrer">Source notes ↗</a><br /><small class="mono">SYN-HEC-02 · 25 AUG 2026</small></td><td><a href="https://www.moneysense.gov.sg/insurance-basics/" target="_blank" rel="noreferrer">Source notes ↗</a><br /><small class="mono">SYN-OIS-03 · 25 AUG 2026</small></td></tr>
            </tbody>
          </table>
        </div>

        <div class="reasoning-drawers">
          <details open>
            <summary><span><b>Why LionCity Term Flex ranks first</b><small>Fit score 82 / 100 · synthetic</small></span><i aria-hidden="true">+</i></summary>
            <div class="drawer-content"><p>It covers the biggest known gap, stays within budget and is protection-only. It still does not fill the full MoneySense guide amount.</p></div>
          </details>
          <details>
            <summary><span><b>What the ranking does not know</b><small>Three assumptions remain</small></span><i aria-hidden="true">+</i></summary>
            <div class="drawer-content"><p>Your work cover, existing illness add-on and insurance company approval are still unknown. Check these before deciding.</p></div>
          </details>
          <details>
            <summary><span><b>Excluded synthetic option</b><small>Meridian Whole Life Plus · over budget</small></span><i aria-hidden="true">+</i></summary>
            <div class="drawer-content"><p>It costs S$286 a month, above your S$${state.profile.budget} budget. It also includes savings features you did not ask for.</p></div>
          </details>
        </div>
      </section>

      <section class="decision-footer">
        <div>
          <span class="section-index mono">BEFORE YOU ACT</span>
          <h2>Check the policy. Check the adviser.</h2>
          <p>Do not cancel existing cover based on this demo. A new plan may have different terms or cost more.</p>
        </div>
        <a class="primary-button" href="https://eservices.mas.gov.sg/rr" target="_blank" rel="noreferrer">Check an adviser on MAS <span aria-hidden="true">↗</span></a>
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
