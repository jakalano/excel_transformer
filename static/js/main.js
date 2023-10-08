console.log('main.js loaded');
function handleSummaryPageActions() {
    // Check if you're on the summary page
    if (window.location.pathname === '/summary/') { // Adjust this path according to your Django URL configuration for the summary page
        console.log("Summary page");
        let nextPageLink = document.querySelector('.page-link[href="/edit_data/"]');
        let removeRowsCheckbox = document.getElementById('removeRowsCheckbox');
        let removeEmptyRowsForm = document.getElementById('removeEmptyRowsForm');
        if (removeRowsCheckbox) {
            console.log("checkbox")
            if (nextPageLink) {
                console.log("Next page link found", nextPageLink);  // Additional log
                nextPageLink.addEventListener('click', function(event) {
                    console.log("Next page link clicked");
                    if (removeRowsCheckbox.checked) {
                        event.preventDefault();
                        console.log("Checkbox is checked, submitting form");
                        removeEmptyRowsForm.submit();
                    }
                });
            } else {
                console.log("Next page link NOT found");  // Additional log
            }
            }
    }
}

// Call the function when the document is ready
document.addEventListener('DOMContentLoaded', handleSummaryPageActions);

