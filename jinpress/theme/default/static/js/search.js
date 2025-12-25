/**
 * JinPress Furo-Style Theme - Search Functionality
 */

(function() {
    'use strict';

    let searchIndex = null;
    let searchModal = null;
    let searchInput = null;
    let searchResults = null;
    let activeIndex = -1;

    // ===== Simple Search Index =====
    class SearchIndex {
        constructor() {
            this.documents = [];
            this.index = new Map();
        }

        addDocument(doc) {
            const id = this.documents.length;
            this.documents.push(doc);
            
            const words = this.tokenize(doc.title + ' ' + doc.content + ' ' + (doc.headings || []).join(' '));
            words.forEach(word => {
                if (!this.index.has(word)) {
                    this.index.set(word, new Set());
                }
                this.index.get(word).add(id);
            });
        }

        tokenize(text) {
            return text
                .toLowerCase()
                .replace(/[^\w\s]/g, ' ')
                .split(/\s+/)
                .filter(word => word.length > 1);
        }

        search(query) {
            const queryWords = this.tokenize(query);
            if (queryWords.length === 0) return [];

            const scores = new Map();
            
            queryWords.forEach(word => {
                // Exact match
                const exactMatches = this.index.get(word) || new Set();
                exactMatches.forEach(id => {
                    scores.set(id, (scores.get(id) || 0) + 10);
                });
                
                // Prefix match
                this.index.forEach((docIds, indexWord) => {
                    if (indexWord.startsWith(word) && indexWord !== word) {
                        docIds.forEach(id => {
                            scores.set(id, (scores.get(id) || 0) + 5);
                        });
                    }
                });
            });

            return Array.from(scores.entries())
                .sort((a, b) => b[1] - a[1])
                .slice(0, 10)
                .map(([id]) => this.documents[id]);
        }
    }


    // ===== Load Search Index =====
    async function loadSearchIndex() {
        try {
            // Try different paths for the search index
            const paths = ['/search-index.json', './search-index.json'];
            
            for (const path of paths) {
                try {
                    const response = await fetch(path);
                    if (response.ok) {
                        const data = await response.json();
                        const index = new SearchIndex();
                        data.forEach(doc => index.addDocument(doc));
                        return index;
                    }
                } catch (e) {
                    continue;
                }
            }
            
            console.warn('Search index not found');
            return null;
        } catch (error) {
            console.error('Failed to load search index:', error);
            return null;
        }
    }

    // ===== Open/Close Modal =====
    function openSearchModal() {
        if (!searchModal) return;
        searchModal.classList.add('open');
        searchInput.focus();
        document.body.style.overflow = 'hidden';
    }

    function closeSearchModal() {
        if (!searchModal) return;
        searchModal.classList.remove('open');
        searchInput.value = '';
        hideSearchResults();
        document.body.style.overflow = '';
    }

    // ===== Hide Search Results =====
    function hideSearchResults() {
        searchResults.innerHTML = '';
        activeIndex = -1;
    }

    // ===== Perform Search =====
    function performSearch(query) {
        if (!searchIndex || !query.trim()) {
            hideSearchResults();
            return;
        }

        const results = searchIndex.search(query);
        displaySearchResults(results, query);
    }


    // ===== Display Results =====
    function displaySearchResults(results, query) {
        searchResults.innerHTML = '';
        activeIndex = -1;

        if (results.length === 0) {
            searchResults.innerHTML = '<div class="search-no-results">No results found for "' + escapeHtml(query) + '"</div>';
            return;
        }

        results.forEach((result, index) => {
            const item = createSearchResultItem(result, query, index);
            searchResults.appendChild(item);
        });
    }

    // Alias for backward compatibility
    function displayResults(results, query) {
        displaySearchResults(results, query);
    }

    // ===== Create Search Result Item =====
    function createSearchResultItem(result, query, index) {
        const item = document.createElement('div');
        item.className = 'search-result-item';
        item.setAttribute('data-index', index);
        
        item.innerHTML = `
            <div class="search-result-title">${highlightMatches(result.title, query)}</div>
            <div class="search-result-excerpt">${createExcerpt(result.content, query)}</div>
            <div class="search-result-url">${result.url}</div>
        `;
        
        item.addEventListener('click', () => {
            window.location.href = result.url;
        });
        
        item.addEventListener('mouseenter', () => {
            setActiveResult(index);
        });
        
        return item;
    }

    // ===== Highlight Matches =====
    function highlightMatches(text, query) {
        const words = query.toLowerCase().split(/\s+/).filter(w => w.length > 1);
        let result = escapeHtml(text);
        
        words.forEach(word => {
            const regex = new RegExp('(' + escapeRegex(word) + ')', 'gi');
            result = result.replace(regex, '<mark>$1</mark>');
        });
        
        return result;
    }

    // ===== Create Excerpt =====
    function createExcerpt(content, query, maxLength = 150) {
        const words = query.toLowerCase().split(/\s+/).filter(w => w.length > 1);
        const lowerContent = content.toLowerCase();
        
        // Find first match position
        let matchPos = -1;
        for (const word of words) {
            const pos = lowerContent.indexOf(word);
            if (pos !== -1 && (matchPos === -1 || pos < matchPos)) {
                matchPos = pos;
            }
        }
        
        // Extract excerpt around match
        let start = Math.max(0, matchPos - 50);
        let end = Math.min(content.length, start + maxLength);
        
        if (matchPos === -1) {
            start = 0;
            end = Math.min(content.length, maxLength);
        }
        
        let excerpt = content.substring(start, end);
        if (start > 0) excerpt = '...' + excerpt;
        if (end < content.length) excerpt = excerpt + '...';
        
        return highlightMatches(excerpt, query);
    }


    // ===== Keyboard Navigation =====
    function setActiveResult(index) {
        const items = searchResults.querySelectorAll('.search-result-item');
        items.forEach((item, i) => {
            item.classList.toggle('active', i === index);
        });
        activeIndex = index;
        
        // Scroll into view
        if (items[index]) {
            items[index].scrollIntoView({ block: 'nearest' });
        }
    }

    function handleKeydown(e) {
        const items = searchResults.querySelectorAll('.search-result-item');
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                setActiveResult(Math.min(activeIndex + 1, items.length - 1));
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                setActiveResult(Math.max(activeIndex - 1, 0));
                break;
                
            case 'Enter':
                e.preventDefault();
                if (items[activeIndex]) {
                    items[activeIndex].click();
                }
                break;
                
            case 'Escape':
                closeSearchModal();
                break;
        }
    }

    // ===== Utility Functions =====
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }


    // ===== Initialize =====
    async function initSearch() {
        searchModal = document.getElementById('search-modal');
        searchInput = document.getElementById('search-modal-input');
        searchResults = document.getElementById('search-modal-results');
        
        if (!searchModal || !searchInput || !searchResults) return;
        
        // Load search index
        searchIndex = await loadSearchIndex();
        
        // Search trigger button
        const searchTrigger = document.getElementById('search-trigger');
        if (searchTrigger) {
            searchTrigger.addEventListener('click', openSearchModal);
        }
        
        // Backdrop click to close
        const backdrop = searchModal.querySelector('.search-modal-backdrop');
        if (backdrop) {
            backdrop.addEventListener('click', closeSearchModal);
        }
        
        // Search input events
        let debounceTimer;
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                performSearch(searchInput.value);
            }, 150);
        });
        
        searchInput.addEventListener('keydown', handleKeydown);
        
        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Open with / or Ctrl+K
            if ((e.key === '/' || (e.ctrlKey && e.key === 'k')) && 
                !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
                e.preventDefault();
                openSearchModal();
            }
        });
    }

    // Alias for backward compatibility
    async function init() {
        await initSearch();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSearch);
    } else {
        initSearch();
    }

})();
