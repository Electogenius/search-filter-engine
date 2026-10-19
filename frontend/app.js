/**
 * E-Commerce Search & Filter Engine - Frontend Script

 * This file coordinates client-side user interactions with search input,
 * filters, and sorting. Algorithm calls and backend data fetching will be
 * wired in subsequent milestones.
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

// ============================================================================
// 1. HEALTH CHECK INTEGRATION
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
// 2. SEARCH & FILTERING (API INTEGRATION PLACEHOLDER)
// ============================================================================
/**
 * Gather active query and filter values, then call the search endpoint.
 * 
 * TODO (Team Milestone 2):
 * - Construct URLSearchParams matching docs/api-contract.md:
 *     q, category, min_price, max_price, min_rating, available, sort_by
 * - Call: GET ${API_BASE_URL}/search?...
 * - Handle response, render product cards into `resultsContainer`,
 *   and update `resultsCount`.
 */
function handleSearch() {
  const query = searchInput.value.trim();
  const category = categoryFilter.value;
  const minPrice = minPriceInput.value;
  const maxPrice = maxPriceInput.value;
  const minRating = ratingFilter.value;
  const availableOnly = availabilityFilter.checked;
  const sortBy = sortSelect.value;

  console.log("Search requested with parameters:", {
    query,
    category,
    minPrice,
    maxPrice,
    minRating,
    availableOnly,
    sortBy,
  });

  // Future API Integration point:
  // fetch(`${API_BASE_URL}/search?...`)
  //   .then(res => res.json())
  //   .then(data => renderResults(data.results));
}

// ============================================================================
// 3. AUTOCOMPLETE SUGGESTIONS (API INTEGRATION PLACEHOLDER)
// ============================================================================
/**
 * Fetch prefix matching suggestions from Trie.
 * 
 * TODO (Team Milestone 2):
 * - Debounce input event on `searchInput`.
 * - If query length >= 2:
 *     Call: GET ${API_BASE_URL}/suggest?prefix=${encodeURIComponent(prefix)}
 * - Populate `autocompleteBox` with matching titles/terms.
 */
function handleAutocomplete(event) {
  const prefix = event.target.value.trim();
  if (!prefix) {
    autocompleteBox.classList.add("hidden");
    return;
  }

  // Future API Integration point:
  // fetch(`${API_BASE_URL}/suggest?prefix=${encodeURIComponent(prefix)}`)
  //   .then(res => res.json())
  //   .then(data => renderSuggestions(data.suggestions));
}

// ============================================================================
// 4. RELATED PRODUCTS RECOMMENDATIONS (API INTEGRATION PLACEHOLDER)
// ============================================================================
/**
 * Fetch co-occurrence recommendations for a specific product.
 * 
 * TODO (Team Milestone 3):
 * - Call: GET ${API_BASE_URL}/products/${productId}/related
 * - Display recommendations in product modal or drawer.
 */
function handleProductRecommendations(productId) {
  console.log("Fetch recommendations for product:", productId);

  // Future API Integration point:
  // fetch(`${API_BASE_URL}/products/${productId}/related`)
  //   .then(res => res.json())
  //   .then(data => renderRecommendations(data.recommendations));
}

// ============================================================================
// 5. EVENT LISTENERS
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
  console.log("Filters reset to default.");
});

// Initial health check on page load
document.addEventListener("DOMContentLoaded", () => {
  checkBackendHealth();
});

