/**
 * E-Commerce Search & Filter Engine - Frontend Controller
 * 
 * Coordinates search input, multi-criteria filtering, sorting, and displays
 * results powered by the in-memory AVL-Tree based inverted index backend.
 * Provides a responsive fullscreen modal view for examining product details.
 */

const API_BASE_URL = "http://localhost:8000/api";

// DOM Element References
const searchInput = document.getElementById("search-input");
const searchBtn = document.getElementById("search-btn");
const autocompleteBox = document.getElementById("autocomplete-box");
const categoryFilter = document.getElementById("category-filter");
const minPriceInput = document.getElementById("min-price");
const maxPriceInput = document.getElementById("max-price");
const ratingFilter = document.getElementById("rating-filter");
const availabilityFilter = document.getElementById("availability-filter");
const applyFiltersBtn = document.getElementById("apply-filters-btn");
const resetFiltersBtn = document.getElementById("reset-filters-btn");
const sortSelect = document.getElementById("sort-select");
const resultsContainer = document.getElementById("results-container");
const resultsCount = document.getElementById("results-count");
const correctionBanner = document.getElementById("correction-banner");
const systemStatusText = document.querySelector("#system-status .status-text");

// Modal Element References
const productModal = document.getElementById("product-modal");
const modalContainer = document.getElementById("modal-container");
const modalBody = document.getElementById("modal-body");
const modalCloseBtn = document.getElementById("modal-close-btn");
const modalExpandBtn = document.getElementById("modal-expand-btn");

// In-memory cache of current search results by product ID
let currentResultsMap = new Map();

// ============================================================================
// 1. HEALTH CHECK
// ============================================================================
async function checkBackendHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (response.ok) {
      const data = await response.json();
      if (systemStatusText) {
        systemStatusText.textContent = `Backend: Connected (${data.status})`;
      }
    }
  } catch (error) {
    if (systemStatusText) {
      systemStatusText.textContent = "Backend: Offline (start FastAPI server)";
    }
  }
}

// ============================================================================
// 2. SEARCH & FILTERING (INTEGRATED WITH AVL INVERTED INDEX)
// ============================================================================
/**
 * Gather active query and filter values, query the backend search endpoint,
 * and render the resulting product cards.
 *
 * @param {string|null} forcedQuery - Explicit query string override.
 * @param {boolean} autoCorrect - Whether to enable typo correction via Bloom Filter & Levenshtein DP.
 */
async function handleSearch(forcedQuery = null, autoCorrect = true) {
  closeAutocomplete();
  if (forcedQuery !== null) {
    searchInput.value = forcedQuery;
  }
  const query = searchInput.value.trim();
  const category = categoryFilter.value;
  const minPrice = minPriceInput.value;
  const maxPrice = maxPriceInput.value;
  const minRating = ratingFilter.value;
  const availableOnly = availabilityFilter.checked;
  const sortBy = sortSelect.value;

  // Build query params matching docs/api-contract.md
  const params = new URLSearchParams();
  if (query) params.append("q", query);
  if (category) params.append("category", category);
  if (minPrice) params.append("min_price", minPrice);
  if (maxPrice) params.append("max_price", maxPrice);
  if (minRating) params.append("min_rating", minRating);
  if (availableOnly) params.append("available", "true");
  if (sortBy) params.append("sort_by", sortBy);
  if (!autoCorrect) params.append("auto_correct", "false");
  params.append("limit", "50");

  resultsContainer.innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">⏳</div>
      <h4>Searching In-Memory Catalogue...</h4>
      <p>Querying AVL Inverted Index, Bloom Filter, and evaluating filters.</p>
    </div>
  `;

  try {
    const response = await fetch(`${API_BASE_URL}/search?${params.toString()}`);
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Search request failed");
    }

    const data = await response.json();
    renderSearchResults(data);
  } catch (error) {
    if (correctionBanner) {
      correctionBanner.classList.add("hidden");
      correctionBanner.innerHTML = "";
    }
    resultsContainer.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">⚠️</div>
        <h4>Search Error</h4>
        <p>${escapeHtml(error.message)}</p>
      </div>
    `;
    resultsCount.textContent = "Error executing search";
  }
}

/**
 * Render list of product cards into the results container.
 */
function renderSearchResults(data) {
  const results = data.results || [];
  const total = data.total || 0;
  const query = data.query || "";
  const correctedQuery = data.corrected_query || null;

  // Update in-memory map for fast modal lookup
  currentResultsMap.clear();
  results.forEach(product => currentResultsMap.set(product.id, product));

  // Render "Did You Mean: ...?" / Typo correction banner
  if (correctionBanner) {
    if (correctedQuery && correctedQuery.toLowerCase() !== query.toLowerCase()) {
      correctionBanner.innerHTML = `
        <div class="correction-content">
          <span class="correction-icon">💡</span>
          <span class="correction-text">
            Showing results for <strong>${escapeHtml(correctedQuery)}</strong>.
            Search instead for <button type="button" id="search-original-btn" class="correction-link"><em>${escapeHtml(query)}</em></button>?
          </span>
        </div>
      `;
      correctionBanner.classList.remove("hidden");

      const searchOriginalBtn = document.getElementById("search-original-btn");
      if (searchOriginalBtn) {
        searchOriginalBtn.addEventListener("click", () => {
          handleSearch(query, false);
        });
      }
    } else {
      correctionBanner.classList.add("hidden");
      correctionBanner.innerHTML = "";
    }
  }

  // Update results count header
  if (total === 0) {
    resultsCount.textContent = query
      ? `No results found for "${query}"`
      : "No products match current filters";
    resultsContainer.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">🔎</div>
        <h4>No Matching Products Found</h4>
        <p>Try refining your search terms or relaxing price/category filters.</p>
      </div>
    `;
    return;
  }

  const queryLabel = correctedQuery || query;
  resultsCount.textContent = queryLabel
    ? `Showing ${results.length} of ${total} match${total === 1 ? '' : 'es'} for "${queryLabel}" (AVL Index)`
    : `Showing ${results.length} of ${total} products`;

  const grid = document.createElement("div");
  grid.className = "products-grid";

  results.forEach(product => {
    const card = document.createElement("div");
    card.className = "product-card";
    card.setAttribute("role", "button");
    card.setAttribute("tabindex", "0");

    const stockClass = product.available ? "in-stock" : "out-of-stock";
    const stockLabel = product.available ? "In Stock" : "Out of Stock";
    const scoreBadge = product.score !== undefined
      ? `<span class="score-badge" title="Coordinate AVL term score">Score: ${product.score}</span>`
      : "";

    card.innerHTML = `
      <div>
        <div class="card-top">
          <span class="category-tag">${escapeHtml(product.category)}</span>
          <span class="stock-tag ${stockClass}">${stockLabel}</span>
        </div>
        <h3 class="card-title">${escapeHtml(product.title)}</h3>
        <p class="card-desc">${escapeHtml(product.description)}</p>
      </div>
      <div>
        <div class="card-meta">
          <span class="card-price">₹${Number(product.price).toFixed(2)}</span>
          <span class="card-rating">★ ${Number(product.rating).toFixed(1)}</span>
        </div>
        <div class="card-footer">
          ${scoreBadge}
          <button class="btn-card-fullscreen" type="button">Open Fullscreen ⛶</button>
        </div>
      </div>
    `;

    // Click handler to open fullscreen modal
    card.addEventListener("click", () => openFullscreenModal(product));
    card.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        openFullscreenModal(product);
      }
    });

    grid.appendChild(card);
  });

  resultsContainer.innerHTML = "";
  resultsContainer.appendChild(grid);
}

// ============================================================================
// 3. FULLSCREEN PRODUCT MODAL
// ============================================================================
/**
 * Display full product details in an expansive modal dialog with fullscreen option.
 */
function openFullscreenModal(product) {
  if (!product) return;

  const stockClass = product.available ? "in-stock" : "out-of-stock";
  const stockLabel = product.available ? "In Stock & Ready to Ship" : "Currently Out of Stock";
  const scoreHtml = product.score !== undefined
    ? `<div class="modal-dsa-info">
        <strong>⚡ AVL Index Retrieval Info:</strong> Matched query with relevance score of 
        <code>${product.score}</code> based on token frequency weighting.
       </div>`
    : "";

  modalBody.innerHTML = `
    <div class="modal-product-header">
      <div class="modal-product-tags">
        <span class="category-tag">${escapeHtml(product.category)}</span>
        <span class="stock-tag ${stockClass}">${stockLabel}</span>
      </div>
      <h2 class="modal-product-title">${escapeHtml(product.title)}</h2>
      <div class="modal-product-id">Product ID: ${escapeHtml(product.id)}</div>
    </div>

    <div class="modal-price-rating-row">
      <div class="modal-price">₹${Number(product.price).toFixed(2)}</div>
      <div class="modal-rating">★ ${Number(product.rating).toFixed(1)} / 5.0 Rating</div>
    </div>

    <div class="modal-section-heading">Product Overview</div>
    <p class="modal-description">${escapeHtml(product.description)}</p>

    ${scoreHtml}

    <div class="modal-footer">
      <button class="btn-primary" id="modal-action-close" type="button" style="width: auto; padding: 0.6rem 1.5rem;">
        Close View
      </button>
    </div>
  `;

  // Attach close event to footer close button
  const innerCloseBtn = document.getElementById("modal-action-close");
  if (innerCloseBtn) {
    innerCloseBtn.addEventListener("click", closeModal);
  }

  productModal.classList.remove("hidden");
  document.body.style.overflow = "hidden"; // Prevent background scroll
}

function closeModal() {
  productModal.classList.add("hidden");
  modalContainer.classList.remove("fullscreen");
  document.body.style.overflow = "";
}

function toggleFullscreen() {
  modalContainer.classList.toggle("fullscreen");
  if (modalExpandBtn) {
    modalExpandBtn.textContent = modalContainer.classList.contains("fullscreen") ? "🗗" : "⛶";
  }
}

// Modal event listeners
modalCloseBtn.addEventListener("click", closeModal);
modalExpandBtn.addEventListener("click", toggleFullscreen);

// Close modal when clicking on backdrop outside modal content
productModal.addEventListener("click", (e) => {
  if (e.target === productModal) {
    closeModal();
  }
});

// Close modal or autocomplete on Escape key
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    if (autocompleteBox && !autocompleteBox.classList.contains("hidden")) {
      closeAutocomplete();
    } else if (productModal && !productModal.classList.contains("hidden")) {
      closeModal();
    }
  }
});

// Close autocomplete dropdown when clicking outside
document.addEventListener("click", (e) => {
  if (
    autocompleteBox &&
    !autocompleteBox.classList.contains("hidden") &&
    !searchInput.contains(e.target) &&
    !autocompleteBox.contains(e.target)
  ) {
    closeAutocomplete();
  }
});

// ============================================================================
// 4. AUTOCOMPLETE SUGGESTIONS (POWERED BY TRIE)
// ============================================================================
let autocompleteDebounceTimer = null;

function closeAutocomplete() {
  if (autocompleteBox) {
    autocompleteBox.classList.add("hidden");
    autocompleteBox.innerHTML = "";
  }
}

/**
 * Debounced input handler (250ms) for prefix suggestions.
 */
function handleAutocomplete(event) {
  const prefix = event.target.value.trim();
  clearTimeout(autocompleteDebounceTimer);

  if (!prefix) {
    closeAutocomplete();
    return;
  }

  autocompleteDebounceTimer = setTimeout(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/suggest?prefix=${encodeURIComponent(prefix)}&limit=5`);
      if (!response.ok) {
        closeAutocomplete();
        return;
      }

      const data = await response.json();
      const suggestions = data.suggestions || [];
      renderAutocompleteSuggestions(suggestions);
    } catch (err) {
      console.error("Autocomplete fetch error:", err);
      closeAutocomplete();
    }
  }, 250);
}

/**
 * Render suggestion items in the autocomplete dropdown.
 */
function renderAutocompleteSuggestions(suggestions) {
  if (!suggestions || suggestions.length === 0) {
    closeAutocomplete();
    return;
  }

  autocompleteBox.innerHTML = "";
  suggestions.forEach((item) => {
    const itemEl = document.createElement("div");
    itemEl.className = "autocomplete-item";
    itemEl.setAttribute("role", "button");
    itemEl.setAttribute("tabindex", "0");
    itemEl.textContent = item;

    const selectSuggestion = () => {
      searchInput.value = item;
      closeAutocomplete();
      handleSearch();
    };

    itemEl.addEventListener("click", selectSuggestion);
    itemEl.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        selectSuggestion();
      }
    });

    autocompleteBox.appendChild(itemEl);
  });

  autocompleteBox.classList.remove("hidden");
}

// ============================================================================
// 5. EVENT LISTENERS & INITIALIZATION
// ============================================================================
searchBtn.addEventListener("click", () => {
  closeAutocomplete();
  handleSearch();
});

searchInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    closeAutocomplete();
    handleSearch();
  }
});

searchInput.addEventListener("input", handleAutocomplete);
applyFiltersBtn.addEventListener("click", handleSearch);
sortSelect.addEventListener("change", handleSearch);

resetFiltersBtn.addEventListener("click", () => {
  categoryFilter.value = "";
  minPriceInput.value = "";
  maxPriceInput.value = "";
  ratingFilter.value = "";
  availabilityFilter.checked = false;
  sortSelect.value = "relevance";
  searchInput.value = "";
  if (correctionBanner) {
    correctionBanner.classList.add("hidden");
    correctionBanner.innerHTML = "";
  }
  closeAutocomplete();
  handleSearch();
});

// Utility to prevent XSS in dynamic HTML injection
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Run health check and initial product catalogue search on startup
document.addEventListener("DOMContentLoaded", () => {
  checkBackendHealth();
  handleSearch();
});
