/**
 * JinPress Default Theme - Search Functionality
 */

(function() {
    'use strict';

    let searchIndex = null;
    let searchInput = null;
    let searchResults = null;

    // Simple search index structure
    class SearchIndex {
        constructor() {
            this.documents = [];
            this.index = new Map();
        }

        addDocument(doc) {
            const id = this.documents.length;
            this.documents.push(doc);
            
            // Index the document
            const words = this.tokenize(doc.title + ' ' + doc.content);
            words.forEach(word => {
                if (!this.index.has(word)) {
                    this.index.set(word, []);
                }
                this.index.get(word).push(id);
            });
        }

        tokenize(text) {
            return text
                .toLowerCase()
                .replace(/[^\w\s]/g, ' ')
                .split(/\s+/)
                .filter(word => word.length > 2);
        }

        search(query) {
            const queryWords = this.tokenize(query);
            if (queryWords.length === 0) return [];

            const results = new Map();
            
            queryWords.forEach(word => {
                const docIds = this.index.get(word) || [];
                docIds.forEach(id => {
                    const score = results.get(id) || 0;
                    results.set(id, score + 1);
                });
            });

            // Sort by score and return documents
            return Array.from(results.entries())
                .sort((a, b) => b[1] - a[1])
                .slice(0, 10)
                .map(([id]) => this.documents[id]);
        }
    }

    // Load search index
    async function loadSearchIndex() {
        try {
            const response = await fetch('/search-index.json');
            if (!response.ok) {
                console.warn('Search index not found');
                return null;
            }
            
            const data = await response.json();
            const index = new SearchIndex();
            
            data.forEach(doc => {
                index.addDocument(doc);
            });
            
            return index;
        } catch (error) {
            console.error('Failed to load search index:', error);
            return null;
        }
    }

    // Perform search
    function performSearch(query) {
        if (!searchIndex || !query.trim()) {
            hideSearchResults();
            return;
        }

        const results = searchIndex.search(query);
        displaySearchResults(results, query);
    }

    // Display search results
    function displaySearchResults(results, query) {
        if (!searchResults) return;

        searchResults.innerHTML = '';

        if (results.length === 0) {
            const noResults = document.createElement('div');
            noResults.className = 'search-no-results';
            noResults.textContent = 'No results found';
            searchResults.appendChild(noResults);
        } else {
            results.forEach(result => {
                const item = createSearchResultItem(result, query);
                searchResults.appendChild(item);
            });
        }

        searchResults.style.display = 'block';
    }

    // Create search result item
    function createSearchResultItem(result, query) {
        const item = document.createElement('div');
        item.className = 'search-result-item';

        const title = document.createElement('div');
        title.className = 'search-result-title';
        title.textContent = result.title;

        const excerpt = document.createElement('div');
        excerpt.className = 'search-result-excerpt';
        excerpt.textContent = createExcerpt(result.content, query);

        const url = document.createElement('div');
        url.className = 'search-result-url';
        url.textContent = result.url;

        item.appendChild(title);
        item.appendChild(excerpt);
        item.appendChild(url);

        item.addEventListener('click', () => {
            window.location.href = result.url;
        });

        return item;
    }

    // Create excerpt with highlighted query terms
    function createExcerpt(content, query, maxLength = 150) {
        const queryWords = query.toLowerCase().split(/\s+/);
        const sentences = content.split(/[.!?]+/);
        
        // Find sentence containing query terms
        let bestSentence = sentences[0] || '';
        let maxMatches = 0;
        
        sentences.forEach(sentence => {
            const matches = queryWords.filter(word => 
                sentence.toLowerCase().includes(word)
            ).length;
            
            if (matches > maxMatches) {
                maxMatches = matches;
                bestSentence = sentence;
            }
        });

        // Truncate if too long
        if (bestSentence.length > maxLength) {
            bestSentence = bestSentence.substring(0, maxLength) + '...';
        }

        return bestSentence.trim();
    }

    // Hide search results
    function hideSearchResults() {
        if (searchResults) {
            searchResults.style.display = 'none';
        }
    }

    // Initialize search functionality
    function initSearch() {
        searchInput = document.getElementById('search-input');
        searchResults = document.getElementById('search-results');

        if (!searchInput || !searchResults) {
            return;
        }

        // Load search index
        loadSearchIndex().then(index => {
            searchIndex = index;
            if (searchIndex) {
                searchInput.placeholder = 'Search...';
            } else {
                searchInput.placeholder = 'Search unavailable';
                searchInput.disabled = true;
            }
        });

        // Search input event listeners
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(this.value);
            }, 300);
        });

        searchInput.addEventListener('focus', function() {
            if (this.value.trim()) {
                performSearch(this.value);
            }
        });

        // Hide results when clicking outside
        document.addEventListener('click', function(e) {
            if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                hideSearchResults();
            }
        });

        // Keyboard navigation
        searchInput.addEventListener('keydown', function(e) {
            const items = searchResults.querySelectorAll('.search-result-item');
            const activeItem = searchResults.querySelector('.search-result-item.active');
            
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (activeItem) {
                    activeItem.classList.remove('active');
                    const next = activeItem.nextElementSibling;
                    if (next) {
                        next.classList.add('active');
                    } else if (items.length > 0) {
                        items[0].classList.add('active');
                    }
                } else if (items.length > 0) {
                    items[0].classList.add('active');
                }
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (activeItem) {
                    activeItem.classList.remove('active');
                    const prev = activeItem.previousElementSibling;
                    if (prev) {
                        prev.classList.add('active');
                    } else if (items.length > 0) {
                        items[items.length - 1].classList.add('active');
                    }
                } else if (items.length > 0) {
                    items[items.length - 1].classList.add('active');
                }
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (activeItem) {
                    activeItem.click();
                } else if (items.length > 0) {
                    items[0].click();
                }
            } else if (e.key === 'Escape') {
                hideSearchResults();
                searchInput.blur();
            }
        });
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSearch);
    } else {
        initSearch();
    }

})();
