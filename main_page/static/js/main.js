
function handleSummaryPageActions() {
    // Check if you're on the summary page
    if (window.location.pathname === '/summary/') { // Adjust this path according to your Django URL configuration for the summary page
        let nextPageLink = document.querySelector('.page-link[href="{% url  next_page_url %}"]');
        let removeRowsCheckbox = document.getElementById('removeRowsCheckbox');
        let removeEmptyRowsForm = document.getElementById('removeEmptyRowsForm');

        if (nextPageLink && removeRowsCheckbox) {
            nextPageLink.addEventListener('click', function(event) {
                if (removeRowsCheckbox.checked) {
                    event.preventDefault();
                    removeEmptyRowsForm.submit();
                }
            });
        }
    }
}

// Call the function when the document is ready
document.addEventListener('DOMContentLoaded', handleSummaryPageActions);

