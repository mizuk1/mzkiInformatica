// Base template scripts - Page loader functionality

// Show loader when clicking internal links
document.addEventListener('click', function(e) {
    const link = e.target.closest('a');
    if (link && link.href) {
        // Get the href attribute
        const href = link.getAttribute('href');
        
        // Check if it's an internal link (not external, not anchor, not new tab)
        const isExternal = link.hostname && link.hostname !== window.location.hostname;
        const isAnchor = href && href.startsWith('#');
        const isNewTab = link.target === '_blank' || link.target === '_new';
        const isMailOrTel = href && (href.startsWith('mailto:') || href.startsWith('tel:'));
        
        if (!isExternal && !isAnchor && !isNewTab && !isMailOrTel) {
            const loader = document.getElementById('page-loader');
            if (loader) {
                loader.classList.add('active');
            }
        }
    }
}, true); // Use capture phase

// Show loader when navigating away from page
window.addEventListener('beforeunload', function() {
    const loader = document.getElementById('page-loader');
    if (loader) {
        loader.classList.add('active');
    }
});

// Hide loader when page is ready
window.addEventListener('pageshow', function() {
    const loader = document.getElementById('page-loader');
    if (loader) {
        loader.classList.remove('active');
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const loader = document.getElementById('page-loader');
    if (loader) {
        loader.classList.remove('active');
    }
});
