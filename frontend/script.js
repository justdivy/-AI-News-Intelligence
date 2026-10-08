const ARTICLE_LIMIT = 50_000;
const FILE_SIZE_LIMIT = 1_000_000;
const API_URL = 'http://127.0.0.1:5000/api/analyze';

const articleForm = document.querySelector('#article-form');
const articleInput = document.querySelector('#article-input');
const inputCounts = document.querySelector('#input-counts');
const articleFile = document.querySelector('#article-file');
const selectedFile = document.querySelector('#selected-file');
const formMessage = document.querySelector('#form-message');
const clearButton = document.querySelector('#clear-button');
const sampleButton = document.querySelector('#sample-button');
const heroSampleButton = document.querySelector('#hero-sample-button');
const menuToggle = document.querySelector('#menu-toggle');
const primaryNavigation = document.querySelector('#primary-navigation');
const analyzeButton = document.querySelector('#analyze-button');
let latestAnalysis = null;
let frequencyChart = null;

const demoArticle = `India's space agency announced a new climate-monitoring mission in New Delhi on Tuesday. The Indian Space Research Organisation (ISRO) will work with NASA to launch two satellites next year. Scientists say the mission will measure changes in soil moisture and track extreme weather across South Asia. The project is expected to cost about $85 million, with research teams from Bengaluru and Washington, D.C. contributing data. ISRO Chairperson S. Somanath said the collaboration will help communities prepare for floods and droughts. Officials from both agencies signed the agreement on 14 March 2025.`;

function getWordCount(text) {
  const trimmed = text.trim();
  return trimmed ? trimmed.split(/\s+/u).length : 0;
}

function updateCounts() {
  const text = articleInput.value;
  inputCounts.textContent = `${text.length.toLocaleString()} characters · ${getWordCount(text).toLocaleString()} words`;
}

function showMessage(message, isError = false) {
  formMessage.textContent = message;
  formMessage.dataset.state = isError ? 'error' : 'info';
}

function setText(selector, value) {
  document.querySelector(selector).textContent = value;
}

function replaceWithEmptyState(list, message) {
  const item = document.createElement('li');
  item.className = 'empty-state';
  item.textContent = message;
  list.replaceChildren(item);
}

function fillEntityList(selector, values, emptyMessage) {
  const list = document.querySelector(selector);
  if (!values.length) {
    replaceWithEmptyState(list, emptyMessage);
    return;
  }
  const items = values.map((value) => {
    const item = document.createElement('li');
    item.textContent = value;
    return item;
  });
  list.replaceChildren(...items);
}

function resetPipeline() {
  document.querySelectorAll('.pipeline-step').forEach((step) => {
    step.classList.remove('is-processing', 'is-complete');
    step.querySelector('.step-status').textContent = 'Waiting';
  });
  setText('#pipeline-status', 'Waiting for an article');
}

function setPipelineProcessing() {
  document.querySelectorAll('.pipeline-step').forEach((step) => {
    step.classList.remove('is-complete');
    step.classList.add('is-processing');
    step.querySelector('.step-status').textContent = 'Processing…';
  });
  setText('#pipeline-status', 'NLP is processing the article…');
}

function clearRenderedResults() {
  latestAnalysis = null;
  if (frequencyChart) {
    frequencyChart.destroy();
    frequencyChart = null;
  }
  ['#stat-words', '#stat-unique', '#stat-sentences', '#stat-entities', '#stat-keywords']
    .forEach((selector) => setText(selector, '—'));
  setText('#results-caption', 'Results will appear here after analysis');
  setText('#entity-count', '—');
  fillEntityList('#people-list', [], 'Entities will appear after analysis.');
  fillEntityList('#organizations-list', [], '—');
  fillEntityList('#locations-list', [], '—');
  fillEntityList('#dates-list', [], '—');
  fillEntityList('#money-list', [], '—');

  const keywordList = document.querySelector('#keyword-list');
  replaceWithEmptyState(keywordList, 'Keywords will appear after analysis.');
  setText('#summary-text', 'A concise summary will appear after analysis.');
  document.querySelector('#summary-text').classList.add('empty-state');
  document.querySelector('#pos-table-body').innerHTML = '<tr><td class="empty-state" colspan="3">POS tags will appear after analysis.</td></tr>';
  setText('#original-preview', 'Your article text will appear here.');
  setText('#processed-text', 'Cleaned, lowercased tokens without stopwords or punctuation will appear here.');
  setText('#highlighted-text', 'Your analyzed article with highlighted entities will appear here.');
  document.querySelector('#highlighted-text').classList.add('empty-state');
  setText('#chart-empty', 'The word frequency chart will appear after analysis.');
  document.querySelector('#chart-empty').hidden = false;
  resetPipeline();
}

function renderFrequencyChart(frequencies) {
  const canvas = document.querySelector('#frequency-chart');
  const emptyMessage = document.querySelector('#chart-empty');
  if (frequencyChart) {
    frequencyChart.destroy();
    frequencyChart = null;
  }
  if (!frequencies.length) {
    emptyMessage.textContent = 'No content words were available for the chart.';
    emptyMessage.hidden = false;
    return;
  }
  if (typeof Chart === 'undefined') {
    emptyMessage.textContent = 'Chart.js did not load. NLP results are still available.';
    emptyMessage.hidden = false;
    return;
  }

  emptyMessage.hidden = true;
  try {
    frequencyChart = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: frequencies.map((item) => item.word),
        datasets: [{
          data: frequencies.map((item) => item.count),
          backgroundColor: '#6378ed',
          hoverBackgroundColor: '#7959e8',
          borderRadius: 5,
          borderSkipped: false,
          barThickness: 15,
        }],
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 550 },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => `${context.parsed.x} occurrence${context.parsed.x === 1 ? '' : 's'}`,
            },
          },
        },
        scales: {
          x: {
            beginAtZero: true,
            ticks: { precision: 0, color: '#8995a8', font: { family: 'DM Sans', size: 10 } },
            grid: { color: '#edf0f6' },
            border: { display: false },
          },
          y: {
            ticks: { color: '#52617a', font: { family: 'DM Sans', size: 10 } },
            grid: { display: false },
            border: { display: false },
          },
        },
      },
    });
  } catch (error) {
    console.warn('Could not render the word frequency chart.', error);
    emptyMessage.textContent = 'The chart could not be rendered. Other NLP results are available.';
    emptyMessage.hidden = false;
  }
}

function renderHighlightedArticle(text, entities) {
  const container = document.querySelector('#highlighted-text');
  const fragment = document.createDocumentFragment();
  const classByLabel = {
    PERSON: 'entity-person',
    ORG: 'entity-org',
    GPE: 'entity-location',
    LOC: 'entity-location',
    FAC: 'entity-location',
    DATE: 'entity-date',
    MONEY: 'entity-money',
  };
  const orderedEntities = [...entities].sort((left, right) => left.start - right.start || right.end - left.end);
  // spaCy offsets count Unicode code points; JavaScript slice() counts UTF-16 units.
  const codePointToUnitOffset = [0];
  let unitOffset = 0;
  for (const character of text) {
    unitOffset += character.length;
    codePointToUnitOffset.push(unitOffset);
  }
  let cursor = 0;

  for (const entity of orderedEntities) {
    const { start, end, label } = entity;
    if (!Number.isInteger(start) || !Number.isInteger(end) || start < 0 || end <= start || end >= codePointToUnitOffset.length) continue;
    const startUnit = codePointToUnitOffset[start];
    const endUnit = codePointToUnitOffset[end];
    if (startUnit < cursor) continue;
    const sourceText = text.slice(startUnit, endUnit);
    if (sourceText !== entity.text) continue;

    fragment.append(document.createTextNode(text.slice(cursor, startUnit)));
    const mark = document.createElement('mark');
    mark.className = classByLabel[label] || '';
    mark.textContent = sourceText;
    mark.title = entity.type || label;
    mark.setAttribute('aria-label', `${sourceText}: ${entity.type || label}`);
    fragment.append(mark);
    cursor = endUnit;
  }
  fragment.append(document.createTextNode(text.slice(cursor)));
  container.replaceChildren(fragment);
  container.classList.remove('empty-state');
}

function renderAnalysis(data) {
  latestAnalysis = data;
  window.latestAnalysis = data;
  const stats = data.statistics;
  setText('#stat-words', stats.total_words.toLocaleString());
  setText('#stat-unique', stats.unique_words.toLocaleString());
  setText('#stat-sentences', stats.sentences.toLocaleString());
  setText('#stat-entities', stats.entities.toLocaleString());
  setText('#stat-keywords', stats.keywords.toLocaleString());
  setText('#results-caption', 'Analysis complete');

  const groups = data.entities.groups;
  setText('#entity-count', `${data.entities.entity_count} found`);
  fillEntityList('#people-list', groups.people, 'No people detected.');
  fillEntityList('#organizations-list', groups.organizations, 'No organizations detected.');
  fillEntityList('#locations-list', groups.locations, 'No locations detected.');
  fillEntityList('#dates-list', groups.dates, 'No dates detected.');
  fillEntityList('#money-list', groups.money, 'No money values detected.');

  const keywordList = document.querySelector('#keyword-list');
  if (data.keywords.keywords.length) {
    const rows = data.keywords.keywords.map(({ keyword, score, relative_score }) => {
      const item = document.createElement('li');
      item.className = 'keyword-row';
      const name = document.createElement('strong');
      name.textContent = keyword;
      const scoreLabel = document.createElement('span');
      scoreLabel.textContent = `TF-IDF ${Number(score).toFixed(3)}`;
      const track = document.createElement('div');
      track.className = 'keyword-track';
      const bar = document.createElement('i');
      bar.style.width = `${Math.max(0, Math.min(100, Number(relative_score) * 100))}%`;
      track.append(bar);
      item.append(name, scoreLabel, track);
      return item;
    });
    keywordList.replaceChildren(...rows);
  } else {
    replaceWithEmptyState(keywordList, 'No keywords could be extracted.');
  }

  setText('#summary-text', data.summary.summary || 'No summary could be generated.');
  document.querySelector('#summary-text').classList.toggle('empty-state', !data.summary.summary);

  const posBody = document.querySelector('#pos-table-body');
  const posRows = data.pos.tags.map(({ token, pos, description }) => {
    const row = document.createElement('tr');
    for (const value of [token, pos, description]) {
      const cell = document.createElement('td');
      cell.textContent = value;
      row.append(cell);
    }
    return row;
  });
  if (posRows.length) posBody.replaceChildren(...posRows);
  else posBody.innerHTML = '<tr><td class="empty-state" colspan="3">No tokens found.</td></tr>';

  const original = articleInput.value;
  setText('#original-preview', original.length > 1500 ? `${original.slice(0, 1500)}…` : original);
  setText('#processed-text', data.preprocessing.processed_text || 'No content words remain after preprocessing.');
  renderHighlightedArticle(original, data.entities.entities);
  renderFrequencyChart(data.word_frequency.frequencies);
  setText('#pipeline-status', 'All steps completed');
  document.querySelectorAll('.pipeline-step').forEach((step) => {
    step.classList.remove('is-processing');
    step.classList.add('is-complete');
    step.querySelector('.step-status').textContent = 'Completed';
  });
}

function loadDemoArticle() {
  articleInput.value = demoArticle;
  selectedFile.textContent = 'Demo article loaded';
  updateCounts();
  clearRenderedResults();
  showMessage('Demo article loaded. Select Analyze article when you are ready.');
  articleInput.focus();
}

function resetFilePicker() {
  articleFile.value = '';
  selectedFile.textContent = 'No file selected';
}

articleInput.addEventListener('input', () => {
  updateCounts();
  clearRenderedResults();
  if (formMessage.dataset.state === 'error') showMessage('');
  if (selectedFile.textContent === 'Demo article loaded') selectedFile.textContent = 'No file selected';
});

sampleButton.addEventListener('click', loadDemoArticle);
heroSampleButton.addEventListener('click', () => {
  loadDemoArticle();
  document.querySelector('#analyzer').scrollIntoView({ behavior: 'smooth', block: 'start' });
});

articleFile.addEventListener('change', async () => {
  const [file] = articleFile.files;
  if (!file) return;

  const hasTxtExtension = file.name.toLowerCase().endsWith('.txt');
  if (!hasTxtExtension) {
    resetFilePicker();
    showMessage('Please choose a .txt file.', true);
    return;
  }
  if (file.size > FILE_SIZE_LIMIT) {
    resetFilePicker();
    showMessage('That file is too large. The maximum upload size is 1 MB.', true);
    return;
  }

  try {
    const text = await file.text();
    if (articleFile.files[0] !== file) return;
    if (text.length > ARTICLE_LIMIT) {
      resetFilePicker();
      showMessage('This article exceeds the 50,000-character limit.', true);
      return;
    }
    articleInput.value = text;
    selectedFile.textContent = file.name;
    updateCounts();
    clearRenderedResults();
    showMessage('Text file loaded. Select Analyze article when you are ready.');
  } catch {
    if (articleFile.files[0] !== file) return;
    resetFilePicker();
    showMessage('The file could not be read. Please try another .txt file.', true);
  }
});

clearButton.addEventListener('click', () => {
  window.setTimeout(() => {
    resetFilePicker();
    updateCounts();
    clearRenderedResults();
    showMessage('');
  }, 0);
});

articleForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const article = articleInput.value;
  if (!article.trim()) {
    showMessage('Paste an article or load a sample before continuing.', true);
    articleInput.focus();
    return;
  }
  if (article.length > ARTICLE_LIMIT) {
    showMessage('This article exceeds the 50,000-character limit.', true);
    return;
  }

  analyzeButton.disabled = true;
  analyzeButton.textContent = 'Analyzing article…';
  analyzeButton.classList.add('is-loading');
  articleForm.setAttribute('aria-busy', 'true');
  setPipelineProcessing();
  showMessage('Sending the article to the NLP services…');
  try {
    let response;
    try {
      response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: article }),
      });
    } catch (error) {
      if (error instanceof TypeError) {
        throw new Error('Could not reach Flask. Start the backend at http://127.0.0.1:5000 and open this page through Live Server or a local HTTP server.');
      }
      throw error;
    }
    const data = await response.json().catch(() => null);
    if (!data || typeof data !== 'object') {
      throw new Error(`Flask returned an unreadable response (HTTP ${response.status}). Check the backend logs.`);
    }
    if (!response.ok) throw new Error(data.error || `Analysis failed (${response.status}).`);
    if (articleInput.value !== article) {
      resetPipeline();
      showMessage('The article changed while analysis was running. Analyze the current text to refresh results.');
      return;
    }
    renderAnalysis(data);
    showMessage('Analysis complete. Results are from the NLP services.');
  } catch (error) {
    resetPipeline();
    showMessage(error.message || 'Analysis could not be completed. Please try again.', true);
  } finally {
    analyzeButton.disabled = false;
    analyzeButton.classList.remove('is-loading');
    articleForm.removeAttribute('aria-busy');
    analyzeButton.innerHTML = 'Analyze article <span aria-hidden="true">→</span>';
  }
});

menuToggle.addEventListener('click', () => {
  const isOpen = menuToggle.getAttribute('aria-expanded') === 'true';
  menuToggle.setAttribute('aria-expanded', String(!isOpen));
  menuToggle.setAttribute('aria-label', isOpen ? 'Open navigation menu' : 'Close navigation menu');
  primaryNavigation.classList.toggle('is-open', !isOpen);
});

primaryNavigation.addEventListener('click', (event) => {
  if (event.target.closest('a')) {
    menuToggle.setAttribute('aria-expanded', 'false');
    menuToggle.setAttribute('aria-label', 'Open navigation menu');
    primaryNavigation.classList.remove('is-open');
  }
});

clearRenderedResults();
updateCounts();
