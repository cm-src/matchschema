/**
 * Central Basket - Matchschema
 * Dynamic schedule from games.json
 */

(function() {
  'use strict';

  // State
  let gamesData = [];
  let currentFilter = 'all';
  let currentDateFilter = 'upcoming';
  let searchQuery = '';
  let currentTheme = 'light'; // 'light' or 'dark'

  // DOM Elements
  const searchInput = document.getElementById('searchInput');
  const filterChips = document.getElementById('filterChips');
  let chips = document.querySelectorAll('.chip'); // Will be updated after dynamic build
  const segments = document.querySelectorAll('.segment');
  const tableToggle = document.getElementById('tableToggle');
  const tableSection = document.getElementById('tableSection');
  const gamesContainer = document.getElementById('gamesContainer');
  const matchCount = document.getElementById('matchCount');
  const emptyState = document.getElementById('emptyState');
  const clearFiltersBtn = document.getElementById('clearFilters');
  const sectionHeader = document.querySelector('.section-header');
  const sectionTitle = document.querySelector('.section-title');
  const tableToggleWrapper = document.querySelector('.table-toggle');
  const downloadsSection = document.querySelector('.downloads-section');
  const downloadsTitle = document.getElementById('downloadsTitle');
  const downloadTsvBtn = document.getElementById('downloadTsv');
  const downloadIcsBtn = document.getElementById('downloadIcs');
  const themeToggle = document.getElementById('themeToggle');

  /**
   * Initialize the application
   */
  async function init() {
    try {
      initTheme();
      await loadGames();
      attachEventListeners();
      updateDownloadsTitle();
      renderGames();
    } catch (error) {
      console.error('Failed to load games:', error);
      showError('Kunde inte ladda matchdata. Försök igen senare.');
    }
  }

  /**
   * Initialize theme from localStorage
   */
  function initTheme() {
    try {
      const savedTheme = localStorage.getItem('theme');
      if (savedTheme === 'light' || savedTheme === 'dark') {
        currentTheme = savedTheme;
      } else {
        // No saved preference - check system preference
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        currentTheme = prefersDark ? 'dark' : 'light';
      }
      applyTheme(currentTheme);
    } catch (e) {
      console.warn('Could not access localStorage:', e);
      currentTheme = 'light';
      applyTheme('light');
    }
  }

  /**
   * Apply theme to document
   */
  function applyTheme(theme) {
    const body = document.body;
    body.classList.remove('dark-mode');

    if (theme === 'dark') {
      body.classList.add('dark-mode');
    }
    // Light mode is default (no class needed)

    // Update toggle button state
    if (themeToggle) {
      const isDark = theme === 'dark';
      themeToggle.setAttribute('aria-pressed', isDark);
      themeToggle.setAttribute('title', isDark ? 'Mörkt läge - Klicka för ljust' : 'Ljust läge - Klicka för mörkt');
      themeToggle.setAttribute('aria-label', isDark ? 'Mörkt läge - Klicka för ljust' : 'Ljust läge - Klicka för mörkt');
    }
  }

  /**
   * Toggle theme - save to localStorage
   */
  function toggleTheme() {
    // Toggle between light and dark
    currentTheme = currentTheme === 'dark' ? 'light' : 'dark';

    try {
      localStorage.setItem('theme', currentTheme);
    } catch (e) {
      console.warn('Could not save theme to localStorage:', e);
    }

    applyTheme(currentTheme);
  }

  /**
   * Load games from JSON
   */
  async function loadGames() {
    const response = await fetch('./data/games.json');
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    gamesData = data.games || [];

    // Build filter chips dynamically from team data
    buildFilterChips();
  }

  /**
   * Build filter chips from unique teams in games data
   */
  function buildFilterChips() {
    if (!filterChips) return;

    // Extract unique teams with their display names
    const teamMap = new Map();
    gamesData.forEach(game => {
      if (game.team && game.teamDisplay && !teamMap.has(game.team)) {
        teamMap.set(game.team, game.teamDisplay);
      }
    });

    // Build HTML: "Alla" chip first, then team chips
    let html = '<button class="chip chip-active" data-filter="all">Alla</button>';
    teamMap.forEach((display, slug) => {
      html += `<button class="chip" data-filter="${escapeHtml(slug)}">${escapeHtml(display)}</button>`;
    });

    filterChips.innerHTML = html;

    // Update chips reference for event listeners
    chips = document.querySelectorAll('.chip');
  }

  /**
   * Attach event listeners
   */
  function attachEventListeners() {
    if (searchInput) {
      let debounceTimer;
      searchInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => handleSearch(e), 200);
      });
    }

    chips.forEach(chip => {
      chip.addEventListener('click', handleChipClick);
    });

    segments.forEach(segment => {
      segment.addEventListener('click', handleSegmentClick);
    });

    if (tableToggle) {
      tableToggle.addEventListener('click', toggleTable);
    }

    if (clearFiltersBtn) {
      clearFiltersBtn.addEventListener('click', clearFilters);
    }

    if (themeToggle) {
      themeToggle.addEventListener('click', toggleTheme);
    }

    if (downloadTsvBtn) {
      downloadTsvBtn.addEventListener('click', handleDownloadTsv);
    }

    if (downloadIcsBtn) {
      downloadIcsBtn.addEventListener('click', handleDownloadIcs);
    }

    // Check chip overflow for landscape mode fade indicator
    checkChipOverflow();
    window.addEventListener('resize', checkChipOverflow);
  }

  /**
   * Check if filter chips overflow and add indicator class
   */
  function checkChipOverflow() {
    const filterChips = document.querySelector('.filter-chips');
    if (!filterChips) return;

    // Only apply in landscape mode (max-height: 500px)
    if (window.matchMedia('(max-height: 500px)').matches) {
      if (filterChips.scrollWidth > filterChips.clientWidth) {
        filterChips.classList.add('has-overflow');
      } else {
        filterChips.classList.remove('has-overflow');
      }
    } else {
      filterChips.classList.remove('has-overflow');
    }
  }

  /**
   * Handle search input
   */
  function handleSearch(e) {
    searchQuery = e.target.value.toLowerCase().trim();
    renderGames();
  }

  /**
   * Handle chip click
   */
  function handleChipClick(e) {
    const clickedChip = e.target;
    const filter = clickedChip.dataset.filter;

    chips.forEach(chip => chip.classList.remove('chip-active'));
    clickedChip.classList.add('chip-active');

    currentFilter = filter;
    updateDownloadsTitle();
    renderGames();
  }

  /**
   * Handle segment click
   */
  function handleSegmentClick(e) {
    const clickedSegment = e.target;
    const dateFilter = clickedSegment.dataset.date;

    segments.forEach(segment => {
      segment.classList.remove('segment-active');
      segment.setAttribute('aria-checked', 'false');
    });
    clickedSegment.classList.add('segment-active');
    clickedSegment.setAttribute('aria-checked', 'true');

    currentDateFilter = dateFilter;
    renderGames();
  }

  /**
   * Toggle table visibility
   */
  function toggleTable() {
    const isOpen = tableSection.classList.toggle('open');
    tableToggle.setAttribute('aria-expanded', isOpen);
  }

  /**
   * Clear all filters
   */
  function clearFilters() {
    searchQuery = '';
    if (searchInput) searchInput.value = '';

    currentFilter = 'all';
    chips.forEach(chip => {
      chip.classList.remove('chip-active');
      if (chip.dataset.filter === 'all') chip.classList.add('chip-active');
    });

    currentDateFilter = 'upcoming';
    segments.forEach(segment => {
      segment.classList.remove('segment-active');
      segment.setAttribute('aria-checked', 'false');
      if (segment.dataset.date === 'upcoming') {
        segment.classList.add('segment-active');
        segment.setAttribute('aria-checked', 'true');
      }
    });

    updateDownloadsTitle();
    renderGames();
  }

  /**
   * Filter games based on current filters
   */
  function getFilteredGames() {
    return gamesData.filter(game => {
      // Team filter
      const teamMatch = currentFilter === 'all' || game.team === currentFilter;

      // Date filter - "Kommande" means today and onwards
      let dateMatch = true;
      if (currentDateFilter === 'upcoming' && game.start) {
        const gameDate = new Date(game.start);
        const today = new Date();
        // Compare only date parts (ignore time)
        const gameDay = new Date(gameDate.getFullYear(), gameDate.getMonth(), gameDate.getDate());
        const todayDay = new Date(today.getFullYear(), today.getMonth(), today.getDate());
        dateMatch = gameDay >= todayDay;
      }

      // Search filter
      const searchMatch = !searchQuery ||
        game.game.toLowerCase().includes(searchQuery) ||
        game.location.toLowerCase().includes(searchQuery) ||
        game.teamFull.toLowerCase().includes(searchQuery);

      return teamMatch && dateMatch && searchMatch;
    });
  }

  /**
   * Render games
   */
  function renderGames() {
    const filtered = getFilteredGames();

    // Show/hide sections based on results
    if (filtered.length === 0) {
      // Hide main content sections
      if (sectionHeader) sectionHeader.classList.add('is-hidden');
      if (tableToggleWrapper) tableToggleWrapper.classList.add('is-hidden');
      if (tableSection) tableSection.classList.add('is-hidden');
      gamesContainer.innerHTML = '';
      gamesContainer.classList.add('is-hidden');

      // Show empty state, hide downloads (nothing to download)
      emptyState.classList.remove('is-hidden');
      if (downloadsSection) downloadsSection.classList.add('is-hidden');
      return;
    }

    // Show main content sections
    if (sectionHeader) sectionHeader.classList.remove('is-hidden');
    if (tableToggleWrapper) tableToggleWrapper.classList.remove('is-hidden');
    if (tableSection) tableSection.classList.remove('is-hidden');
    gamesContainer.classList.remove('is-hidden');
    emptyState.classList.add('is-hidden');
    // Ensure downloads section is visible
    if (downloadsSection) downloadsSection.classList.remove('is-hidden');

    // Update match count
    if (matchCount) {
      matchCount.textContent = `${filtered.length} ${filtered.length === 1 ? 'match' : 'matcher'}`;
    }

    // Always update table (even when hidden)
    updateTable(filtered);

    // Group by date
    const grouped = groupByDate(filtered);

    // Render HTML
    gamesContainer.innerHTML = Object.entries(grouped)
      .map(([date, games]) => renderDateGroup(date, games))
      .join('');
  }

  /**
   * Group games by date
   */
  function groupByDate(games) {
    const grouped = {};
    games.forEach(game => {
      const date = game.start ? new Date(game.start).toDateString() : 'unknown';
      if (!grouped[date]) grouped[date] = [];
      grouped[date].push(game);
    });
    return grouped;
  }

  /**
   * Render a date group
   */
  function renderDateGroup(dateStr, games) {
    const dateLabel = formatDate(dateStr);
    const gamesHtml = games.map(renderGameCard).join('');

    return `
      <div class="date-divider">
        <div class="date-line"></div>
        <span class="date-text">${dateLabel}</span>
        <div class="date-line"></div>
      </div>
      ${gamesHtml}
    `;
  }

  /**
   * Render a game card
   */
  function renderGameCard(game) {
    const color = isValidCssColor(game.teamColor) ? game.teamColor : '#6B7280';
    const timeStr = formatTime(game.start, game.end);
    const dateAttr = game.start ? new Date(game.start).toISOString().split('T')[0] : '';

    return `
      <article class="game-card" data-team="${game.team}" data-date="${dateAttr}">
        <div class="team-strip" style="background: ${color}"></div>
        <div class="game-card-content">
          <div class="game-card-left">
            <h3 class="game-title">${escapeHtml(game.game)}</h3>
            <div class="game-meta">
              <div class="meta-item">
                <a href="${buildGoogleMapsSearchUrl(game.location)}" target="_blank" rel="noopener noreferrer" class="location-link" title="Öppna i Google Maps">
                  <svg class="meta-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                </a>
                <span class="meta-text">${escapeHtml(game.location)}</span>
              </div>
              <div class="meta-item">
                <svg class="meta-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                <span class="meta-text">${timeStr}</span>
              </div>
            </div>
          </div>
          <div class="game-card-right">
            <span class="team-badge" style="background: ${color}"${color === '#fec225' ? ' data-contrast="light"' : ''}>${escapeHtml(game.teamDisplay)}</span>
            <a href="${sanitizeUrl(game.url)}" target="_blank" rel="noopener noreferrer" class="btn-details">
              Matchdetaljer
              <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
            </a>
          </div>
        </div>
      </article>
    `;
  }

  /**
   * Update table view
   */
  function updateTable(games) {
    const tbody = document.querySelector('.data-table tbody');
    if (!tbody) return;

    // Clear table if no games
    if (games.length === 0) {
      tbody.innerHTML = '';
      return;
    }

    tbody.innerHTML = games.map(game => {
      const color = isValidCssColor(game.teamColor) ? game.teamColor : '#6B7280';
      const dateStr = game.start ? formatShortDate(new Date(game.start)) : '';

      return `
        <tr>
          <td>
            <div class="table-team">
              <span class="team-dot" style="background: ${color}"></span>
              ${escapeHtml(game.teamDisplay)}
            </div>
          </td>
          <td>${escapeHtml(game.game)}</td>
          <td>${escapeHtml(game.location)}</td>
          <td>${dateStr}</td>
          <td>
            <a href="${sanitizeUrl(game.url)}" target="_blank" rel="noopener noreferrer" class="table-link">
              Profixio
              <svg class="link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
            </a>
          </td>
        </tr>
      `;
    }).join('');
  }

  /**
   * Format date string
   */
  function formatDate(dateStr) {
    if (dateStr === 'unknown') return 'Okänt datum';
    const date = new Date(dateStr);
    return date.toLocaleDateString('sv-SE', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  }

  /**
   * Format short date (e.g., "16/11 12:45")
   */
  function formatShortDate(date) {
    const day = date.getDate();
    const month = date.getMonth() + 1;
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${day}/${month} ${hours}:${minutes}`;
  }

  /**
   * Format time range
   */
  function formatTime(start, end) {
    if (!start) return 'Tid TBD';
    const startDate = new Date(start);
    const endDate = end ? new Date(end) : null;

    const startStr = startDate.toLocaleTimeString('sv-SE', { hour: '2-digit', minute: '2-digit' });
    const endStr = endDate ? endDate.toLocaleTimeString('sv-SE', { hour: '2-digit', minute: '2-digit' }) : '';

    return endStr ? `${startStr}–${endStr}` : startStr;
  }

  /**
   * Escape HTML
   */
  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  /**
   * Validate a CSS color value for safe inline style injection.
   * Only allows 6-digit hex colors (e.g. #550f38).
   */
  function isValidCssColor(value) {
    return /^#[0-9A-Fa-f]{6}$/.test(value);
  }

  /**
   * Sanitize a URL for safe use in href attributes.
   * Only allows http:// and https:// protocols to prevent javascript: URLs.
   */
  function sanitizeUrl(url) {
    if (!url) return '#';
    try {
      const parsed = new URL(url);
      if (parsed.protocol === 'http:' || parsed.protocol === 'https:') return url;
    } catch { /* invalid URL */ }
    return '#';
  }

  /**
   * Build a Google Maps search URL using the official Maps URLs API.
   * @param {string} query - The search query (e.g., venue name)
   * @returns {string} - Google Maps URL
   * @see https://developers.google.com/maps/documentation/urls/get-started
   */
  function buildGoogleMapsSearchUrl(query) {
    const baseUrl = 'https://www.google.com/maps/search/';
    const params = new URLSearchParams();

    // api=1 is required for proper Universal Links support on mobile
    params.set('api', '1');
    // Use 'query' parameter for search (official parameter name)
    params.set('query', query);

    return `${baseUrl}?${params.toString()}`;
  }

  /**
   * Show an accessible toast notification instead of alert().
   */
  function showToast(message) {
    // Remove any existing toast
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.setAttribute('role', 'alert');
    toast.textContent = message;
    document.body.appendChild(toast);

    // Auto-dismiss after 3 seconds
    setTimeout(() => {
      toast.classList.add('toast-exit');
      toast.addEventListener('animationend', () => toast.remove());
    }, 3000);
  }

  /**
   * Show error message
   */
  function showError(message) {
    if (gamesContainer) {
      gamesContainer.innerHTML = `
        <div class="error-state">
          <p>${escapeHtml(message)}</p>
        </div>
      `;
    }
  }

  /**
   * Update downloads section title based on current filter
   */
  function updateDownloadsTitle() {
    if (!downloadsTitle) return;

    if (currentFilter === 'all') {
      downloadsTitle.textContent = 'Ladda ner alla matcher';
    } else {
      const teamName = getTeamDisplayName(currentFilter);
      downloadsTitle.textContent = `Ladda ner matcher för ${teamName}`;
    }
  }

  /**
   * Get display name for a team slug
   */
  function getTeamDisplayName(teamSlug) {
    for (const game of gamesData) {
      if (game.team === teamSlug && game.teamDisplay) {
        return game.teamDisplay;
      }
    }
    return teamSlug;
  }

  /**
   * Generate ICS calendar content from games
   */
  function generateICS(games) {
    const lines = [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'PRODID:-//Central Basket//Matchschema//SV',
      'CALSCALE:GREGORIAN',
      'METHOD:PUBLISH'
    ];

    for (const game of games) {
      const uid = `central-${game.id}`;
      const summary = escapeICS(`[${game.teamDisplay}] ${game.game}`);
      const location = escapeICS(game.location);
      const dtstart = formatICSDate(game.start);
      const dtend = formatICSDate(game.end);

      lines.push('BEGIN:VEVENT');
      lines.push(`UID:${uid}`);
      lines.push(`SUMMARY:${summary}`);
      lines.push(`LOCATION:${location}`);
      lines.push(`DTSTART;TZID=Europe/Stockholm:${dtstart}`);
      if (dtend) lines.push(`DTEND;TZID=Europe/Stockholm:${dtend}`);
      lines.push(`URL:${game.url}`);
      lines.push('END:VEVENT');
    }

    lines.push('END:VCALENDAR');
    return lines.join('\r\n');
  }

  /**
   * Generate TSV content from games
   */
  function generateTSV(games) {
    const header = 'Lag\tMatch\tPlats\tStarttid\tSluttid\tURL';
    const rows = games
      .sort((a, b) => new Date(a.start) - new Date(b.start))
      .map(game => {
        const start = game.start ? formatShortDate(new Date(game.start)) : '';
        const end = game.end ? formatShortDate(new Date(game.end)) : '';
        return `${game.teamDisplay}\t${game.game}\t${game.location}\t${start}\t${end}\t${game.url}`;
      });
    return header + '\n' + rows.join('\n');
  }

  /**
   * Format date for ICS using Stockholm wall-clock time (YYYYMMDDTHHMMSS).
   * Uses TZID=Europe/Stockholm so calendar apps show venue time,
   * not the viewer's local timezone.
   */
  function formatICSDate(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    const parts = new Intl.DateTimeFormat('sv-SE', {
      timeZone: 'Europe/Stockholm',
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      hour12: false
    }).formatToParts(date);
    const get = (type) => parts.find(p => p.type === type)?.value || '';
    return `${get('year')}${get('month')}${get('day')}T${get('hour')}${get('minute')}${get('second')}`;
  }

  /**
   * Escape special characters for ICS format
   */
  function escapeICS(text) {
    if (!text) return '';
    return text
      .replace(/\\/g, '\\\\')
      .replace(/;/g, '\\;')
      .replace(/,/g, '\\,')
      .replace(/\n/g, '\\n');
  }

  /**
   * Download blob as file
   */
  function downloadBlob(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  /**
   * Handle TSV download
   */
  function handleDownloadTsv() {
    const filtered = getFilteredGames();
    if (filtered.length === 0) {
      showToast('Inga matcher att ladda ner');
      return;
    }

    const tsv = generateTSV(filtered);
    const filename = currentFilter === 'all'
      ? 'matcher.tsv'
      : `matcher-${currentFilter}.tsv`;
    downloadBlob(tsv, filename, 'text/tab-separated-values;charset=utf-8');
  }

  /**
   * Handle ICS download
   */
  function handleDownloadIcs() {
    const filtered = getFilteredGames();
    if (filtered.length === 0) {
      showToast('Inga matcher att ladda ner');
      return;
    }

    const ics = generateICS(filtered);
    const filename = currentFilter === 'all'
      ? 'kalender.ics'
      : `kalender-${currentFilter}.ics`;
    downloadBlob(ics, filename, 'text/calendar;charset=utf-8');
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Register service worker for PWA
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('./sw.js')
        .then((reg) => {
          // Check for updates every 30 minutes
          setInterval(() => {
            reg.update();
          }, 30 * 60 * 1000);
        })
        .catch((err) => console.error('SW registration failed:', err));
    });
  }
})();