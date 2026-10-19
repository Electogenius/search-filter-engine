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
 */
async function handleSearch() {
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
  params.append("limit", "50");

  resultsContainer.innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">⏳</div>
      <h4>Searching In-Memory Catalogue...</h4>
      <p>Querying AVL Inverted Index and evaluating filters.</p>
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

  // Update in-memory map for fast modal lookup
  currentResultsMap.clear();
  results.forEach(product => currentResultsMap.set(product.id, product));

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

  resultsCount.textContent = query
    ? `Showing ${results.length} of ${total} match${total === 1 ? '' : 'es'} for "${query}" (AVL Index)`
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
          <span class="card-price">$${Number(product.price).toFixed(2)}</span>
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
      <div class="modal-price">$${Number(product.price).toFixed(2)}</div>
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

// Close modal on Escape key
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !productModal.classList.contains("hidden")) {
    closeModal();
  }
});

// ============================================================================
// 4. AUTOCOMPLETE & RECOMMENDATIONS (PLACEHOLDERS)
// ============================================================================
function handleAutocomplete(event) {
  const prefix = event.target.value.trim();
  if (!prefix) {
    autocompleteBox.classList.add("hidden");
    return;
  }
  // Autocomplete will be plugged into Trie in Milestone 2
}

// ============================================================================
// 5. EVENT LISTENERS & INITIALIZATION
// ============================================================================
searchBtn.addEventListener("click", handleSearch);

searchInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
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
  autocompleteBox.classList.add("hidden");
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
