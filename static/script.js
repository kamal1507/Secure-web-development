// script.js
// Simple JavaScript for the Library Management System
// Kept minimal and beginner-friendly

// ---- Delete confirmation ----
// Called when admin clicks "Delete" on a book
function confirmDelete(bookTitle) {
    return confirm('Are you sure you want to delete "' + bookTitle + '"?\nThis action cannot be undone.');
}


// ---- Auto-dismiss flash messages after 4 seconds ----
document.addEventListener('DOMContentLoaded', function () {

    // Hide flash messages after a few seconds
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach(function (flash) {
        setTimeout(function () {
            flash.style.transition = 'opacity 0.5s ease';
            flash.style.opacity = '0';
            setTimeout(function () {
                flash.remove();
            }, 500);
        }, 4000); // 4 seconds
    });


    // ---- Live search filter (client-side, for browse page) ----
    // This filters visible table rows as the user types in the search box
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function () {
            const query = this.value.toLowerCase();
            const rows = document.querySelectorAll('.data-table tbody tr');

            rows.forEach(function (row) {
                const text = row.textContent.toLowerCase();
                // Show row if it matches, hide if it doesn't
                row.style.display = text.includes(query) ? '' : 'none';
            });
        });
    }

});
